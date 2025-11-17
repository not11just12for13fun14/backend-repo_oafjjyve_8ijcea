"""
Database Schemas for Gym Coach Platform

Each Pydantic model maps to a MongoDB collection (lowercased class name).
Use these for validation in your FastAPI endpoints.
"""
from __future__ import annotations
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Literal, Dict
from datetime import date

Role = Literal["trainer", "client"]

class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: EmailStr = Field(..., description="Email address")
    role: Role = Field(..., description="User role: trainer or client")
    trainer_id: Optional[str] = Field(None, description="If client, the linked trainer's id")
    connection_code: Optional[str] = Field(None, description="Unique code clients can use to connect to a trainer")
    avatar_url: Optional[str] = Field(None, description="Profile image URL")
    bio: Optional[str] = Field(None, description="Short bio")

class Exercise(BaseModel):
    name: str
    sets: int = Field(3, ge=1, le=10)
    reps: str = Field("10-12", description="Reps e.g. '8-10' or '12' or 'AMRAP'")
    rest_seconds: int = Field(60, ge=0)
    notes: Optional[str] = None

class WorkoutDay(BaseModel):
    day: Literal["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    focus: Optional[str] = Field(None, description="e.g. Push, Pull, Legs")
    exercises: List[Exercise] = Field(default_factory=list)

class WorkoutPlan(BaseModel):
    trainer_id: str
    client_id: str
    title: str
    goal: Optional[str] = None
    duration_weeks: int = Field(4, ge=1, le=52)
    schedule: List[WorkoutDay] = Field(default_factory=list)
    is_active: bool = True

class Meal(BaseModel):
    name: str
    calories: int = Field(..., ge=0)
    protein_g: int = Field(0, ge=0)
    carbs_g: int = Field(0, ge=0)
    fats_g: int = Field(0, ge=0)
    time_of_day: Optional[Literal["breakfast","lunch","dinner","snack"]] = None
    notes: Optional[str] = None

class MealPlan(BaseModel):
    trainer_id: str
    client_id: str
    title: str
    daily_calorie_target: int = Field(2000, ge=0)
    meals: List[Meal] = Field(default_factory=list)
    is_active: bool = True

class Message(BaseModel):
    conversation_id: str = Field(..., description="trainerId_clientId")
    sender_id: str
    content: str
    read: bool = False

class DailyLog(BaseModel):
    client_id: str
    log_date: date
    calories: int = Field(0, ge=0)
    protein_g: int = Field(0, ge=0)
    weight_kg: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None

# Dashboard summaries
class DashboardSummary(BaseModel):
    user_id: str
    role: Role
    connected: bool
    clients: Optional[List[Dict]] = None
    active_workout_plans: int = 0
    active_meal_plans: int = 0
    streak_days: int = 0
