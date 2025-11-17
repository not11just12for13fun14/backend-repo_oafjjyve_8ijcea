import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import User, WorkoutPlan, MealPlan, Message, DailyLog

app = FastAPI(title="Gym Coach Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helpers

def oid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

# Health and schema endpoints
@app.get("/")
def root():
    return {"message": "Gym Coach Platform API"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    return response

# Users
@app.post("/api/users", response_model=dict)
def create_user(user: User):
    user_dict = user.model_dump()
    # Ensure unique email
    if db["user"].find_one({"email": user.email}):
        raise HTTPException(status_code=400, detail="Email already exists")
    new_id = create_document("user", user_dict)
    return {"id": new_id}

@app.get("/api/users", response_model=List[dict])
def list_users(role: Optional[str] = None):
    query = {"role": role} if role else {}
    items = get_documents("user", query)
    for i in items:
        i["id"] = str(i.pop("_id"))
    return items

@app.post("/api/connect", response_model=dict)
def connect_client(trainer_id: str, client_email: str):
    trainer = db["user"].find_one({"_id": oid(trainer_id), "role": "trainer"})
    if not trainer:
        raise HTTPException(status_code=404, detail="Trainer not found")
    client = db["user"].find_one({"email": client_email, "role": "client"})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    db["user"].update_one({"_id": client["_id"]}, {"$set": {"trainer_id": str(trainer["_id"])}})
    return {"status": "connected"}

# Workout Plans
@app.post("/api/workout-plans", response_model=dict)
def create_workout_plan(plan: WorkoutPlan):
    # Verify trainer-client relationship
    trainer = db["user"].find_one({"_id": oid(plan.trainer_id), "role": "trainer"})
    client = db["user"].find_one({"_id": oid(plan.client_id), "role": "client"})
    if not trainer or not client:
        raise HTTPException(status_code=400, detail="Invalid trainer or client")
    if client.get("trainer_id") not in (plan.trainer_id, str(trainer["_id"])):
        raise HTTPException(status_code=403, detail="Client not connected to trainer")
    new_id = create_document("workoutplan", plan)
    return {"id": new_id}

@app.get("/api/workout-plans", response_model=List[dict])
def list_workout_plans(trainer_id: Optional[str] = None, client_id: Optional[str] = None, active: bool = True):
    q = {"is_active": active}
    if trainer_id:
        q["trainer_id"] = trainer_id
    if client_id:
        q["client_id"] = client_id
    items = get_documents("workoutplan", q)
    for i in items:
        i["id"] = str(i.pop("_id"))
    return items

# Meal Plans
@app.post("/api/meal-plans", response_model=dict)
def create_meal_plan(plan: MealPlan):
    trainer = db["user"].find_one({"_id": oid(plan.trainer_id), "role": "trainer"})
    client = db["user"].find_one({"_id": oid(plan.client_id), "role": "client"})
    if not trainer or not client:
        raise HTTPException(status_code=400, detail="Invalid trainer or client")
    if client.get("trainer_id") not in (plan.trainer_id, str(trainer["_id"])):
        raise HTTPException(status_code=403, detail="Client not connected to trainer")
    new_id = create_document("mealplan", plan)
    return {"id": new_id}

@app.get("/api/meal-plans", response_model=List[dict])
def list_meal_plans(trainer_id: Optional[str] = None, client_id: Optional[str] = None, active: bool = True):
    q = {"is_active": active}
    if trainer_id:
        q["trainer_id"] = trainer_id
    if client_id:
        q["client_id"] = client_id
    items = get_documents("mealplan", q)
    for i in items:
        i["id"] = str(i.pop("_id"))
    return items

# Messages (simple chat history)
class MessageCreate(BaseModel):
    conversation_id: str
    sender_id: str
    content: str

@app.post("/api/messages", response_model=dict)
def send_message(payload: MessageCreate):
    msg = Message(**payload.model_dump())
    new_id = create_document("message", msg)
    return {"id": new_id}

@app.get("/api/messages", response_model=List[dict])
def get_messages(conversation_id: str, limit: int = 50):
    items = get_documents("message", {"conversation_id": conversation_id}, limit=limit)
    for i in items:
        i["id"] = str(i.pop("_id"))
    return items

# Daily logs for calories/weight
@app.post("/api/logs", response_model=dict)
def add_log(log: DailyLog):
    new_id = create_document("dailylog", log)
    return {"id": new_id}

@app.get("/api/logs", response_model=List[dict])
def list_logs(client_id: str, limit: int = 30):
    items = get_documents("dailylog", {"client_id": client_id}, limit=limit)
    for i in items:
        i["id"] = str(i.pop("_id"))
    return items

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
