
from agno.tools.toolkit import Toolkit






# ----------------------------
# Task API Toolkit
# ----------------------------

from todolistz.database import SessionLocal
from todolistz.core import miner, broker, executor


class TaskAPIToolkit(Toolkit):
    """
    A toolkit wrapper for server task APIs.
    Mirrors FastAPI endpoints in `todolistz.server` / `todolistz.api.tasks`.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            name="TaskAPIToolkit",
            tools=[
                self.mine_task,
                self.pull_task,
                self.execute_task,
            ],
            *args,
            **kwargs
        )

    def _get_db(self):
        db = SessionLocal()
        try:
            return db
        except Exception:
            db.close()
            raise

    def mine_task(self, goal_id: str) -> dict:
        """
        Mirror API: POST /tasks/{goal_id}/mine

        Args:
            goal_id (str): Goal ID to mine tasks for
        """
        db = SessionLocal()
        try:
            task = miner.simple_discovery(db, goal_id)
            return task.__dict__ if hasattr(task, "__dict__") else task
        finally:
            db.close()

    def pull_task(self, goal_id: str) -> dict | None:
        """
        Mirror API: POST /tasks/{goal_id}/pull

        Args:
            goal_id (str): Goal ID to pull ready tasks
        """
        db = SessionLocal()
        try:
            task = broker.pull_ready_tasks(db, goal_id)
            if task is None:
                return None
            return task.__dict__ if hasattr(task, "__dict__") else task
        finally:
            db.close()

    def execute_task(self, task_id: str) -> dict:
        """
        Mirror API: POST /tasks/{task_id}/execute

        Args:
            task_id (str): Task ID to execute
        """
        db = SessionLocal()
        try:
            task = executor.execute_task(db, task_id)
            return task.__dict__ if hasattr(task, "__dict__") else task
        finally:
            db.close()


# ----------------------------
# Goal Toolkit
# ----------------------------

from todolistz.database import SessionLocal
from todolistz import models


class GoalAPIToolkit(Toolkit):
    """
    Toolkit wrapper for Goal lifecycle.
    Includes both execution (create) and discovery (list) tools.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(
            name="GoalAPIToolkit",
            tools=[
                self.create_goal,
                self.list_goals,
            ],
            *args,
            **kwargs
        )

    def create_goal(self, name: str, vision: str) -> dict:
        """
        Mirror API: POST /goals/

        Args:
            name (str): Goal name
            vision (str): Goal description / long-term intent
        """
        db = SessionLocal()
        try:
            g = models.GoalModel(name=name, vision=vision)
            db.add(g)
            db.commit()
            db.refresh(g)
            return {
                "goal_id": g.id,
                "name": g.name,
                "vision": g.vision,
            }
        finally:
            db.close()

    def list_goals(self) -> list[dict]:
        """
        Discovery tool.
        Allows Agent to find existing goal_ids.
        """
        db = SessionLocal()
        try:
            goals = db.query(models.GoalModel).all()
            return [
                {
                    "goal_id": g.id,
                    "name": g.name,
                    "vision": g.vision,
                }
                for g in goals
            ]
        finally:
            db.close()

