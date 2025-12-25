from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from todolistz.database import SessionLocal
from todolistz import models, schemas

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=schemas.GoalOut)
def create_goal(goal: schemas.GoalCreate, db: Session = Depends(get_db)):
    g = models.GoalModel(**goal.dict())
    db.add(g)
    db.commit()
    db.refresh(g)
    return g
