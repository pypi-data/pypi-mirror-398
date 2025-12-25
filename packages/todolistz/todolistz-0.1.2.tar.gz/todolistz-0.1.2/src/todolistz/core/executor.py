import random
from todolistz.models import TaskModel, TaskState, FactModel

def execute_task_old(db, task_id: str):
    task = db.query(TaskModel).get(task_id)
    if not task:
        return None

    task.state = TaskState.DOING
    db.commit()

    invalid = random.choice([False, True, False])
    if invalid:
        task.state = TaskState.INVALIDATED
    else:
        task.state = TaskState.LEARNED

    db.commit()
    db.refresh(task)
    return task

def execute_task(db, task_id: str):
    task = db.query(TaskModel).get(task_id)
    task.state = TaskState.DOING
    db.commit()

    # 选择是否废弃-> 
    invalid = random.choice([False, True, False])

    if invalid:
        task.state = TaskState.INVALIDATED # 已废弃
    else:
        # 不废弃, 添加完成事件, goal独立
        fact = FactModel(
            goal_id=task.goal_id,
            content=f"learned_from_{task.id[:6]}",
            source_task_id=task.id
        )
        db.add(fact)
        task.state = TaskState.LEARNED

    db.commit()
    db.refresh(task)
    return task