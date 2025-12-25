from pydantic import BaseModel
from typing import Optional
from todolistz.models import TaskState

class GoalCreate(BaseModel):
    name: str
    vision: str


class GoalOut(GoalCreate):
    id: str

    class Config:
        from_attributes = True


class TaskOut(BaseModel):
    id: str
    goal_id: str
    title: str
    hypothesis: str
    state: TaskState

    class Config:
        from_attributes = True
