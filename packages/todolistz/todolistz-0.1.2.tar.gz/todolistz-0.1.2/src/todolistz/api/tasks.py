from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from todolistz.database import SessionLocal
from todolistz.core import miner, broker, executor
from todolistz.schemas import TaskOut

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/{goal_id}/mine", response_model=TaskOut)
def mine_task(goal_id: str, db: Session = Depends(get_db)):
    return miner.simple_discovery(db, goal_id)


@router.post("/{goal_id}/pull", response_model=TaskOut | None)
def pull_task(goal_id: str, db: Session = Depends(get_db)):
    return broker.pull_ready_tasks(db, goal_id)


@router.post("/{task_id}/execute", response_model=TaskOut)
def execute(task_id: str, db: Session = Depends(get_db)):
    return executor.execute_task(db, task_id)
