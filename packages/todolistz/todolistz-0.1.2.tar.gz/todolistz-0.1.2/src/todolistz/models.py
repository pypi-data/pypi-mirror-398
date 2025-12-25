import uuid
from sqlalchemy import Column, String, Integer, Enum, Text, Boolean
from todolistz.database import Base
from enum import Enum as PyEnum

class TaskState(PyEnum):
    PENDING = "pending"
    READY = "ready"
    DOING = "doing"
    DONE = "done"
    LEARNED = "learned"
    INVALIDATED = "invalidated"


class GoalModel(Base):
    __tablename__ = "goals"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    vision = Column(Text, nullable=False)


class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    goal_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    hypothesis = Column(Text, nullable=False)
    state = Column(Enum(TaskState), default=TaskState.PENDING)
    estimate_minutes = Column(Integer, default=30)
    required_fact = Column(String, nullable=False)

class FactModel(Base):
    __tablename__ = "facts"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    goal_id = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    source_task_id = Column(String, nullable=True)
    valid = Column(Boolean, default=True)