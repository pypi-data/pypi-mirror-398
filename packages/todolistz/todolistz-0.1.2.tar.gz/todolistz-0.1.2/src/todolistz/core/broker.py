
from todolistz.models import TaskModel, TaskState, FactModel

def pull_ready_tasks_old(db, goal_id: str, wip_limit: int = 2):
    doing = db.query(TaskModel).filter(
        TaskModel.goal_id == goal_id,
        TaskModel.state == TaskState.DOING
    ).count()

    if doing >= wip_limit:
        return None

    task = db.query(TaskModel).filter(
        TaskModel.goal_id == goal_id,
        TaskModel.state == TaskState.PENDING
    ).first()

    if task:
        task.state = TaskState.READY
        db.commit()
        db.refresh(task)

    return task

def pull_ready_tasks(db, goal_id: str, wip_limit: int = 2):
    # 查看一下当前goal中正在执行的任务数量
    doing = db.query(TaskModel).filter(
        TaskModel.goal_id == goal_id,
        TaskModel.state == TaskState.DOING
    ).count()

    # 如果大于阈值,就停止拉取任务并退出
    if doing >= wip_limit:
        return None

    # 可以拉取, 开始拉取
    tasks = db.query(TaskModel).filter(
        TaskModel.goal_id == goal_id,
        TaskModel.state == TaskState.PENDING
    ).all()
    # 所有的pending 任务

    for task in tasks:
        if not task.required_fact:
            # 没有前置条件的, 直接ready 第一个 退出
            task.state = TaskState.READY
            db.commit()
            return task
        # 有前置条件的, 判断是否前置条件已经满足

        # 寻找所有以完成的事实当中, 是否有需要的潜质内容
        fact = db.query(FactModel).filter(
            FactModel.content == task.required_fact,
            FactModel.valid == True
        ).first()

        # 如果有 则ready 
        if fact:
            task.state = TaskState.READY
            db.commit()
            return task

    return None