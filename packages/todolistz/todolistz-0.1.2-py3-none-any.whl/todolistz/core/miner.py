from todolistz.models import TaskModel, TaskState

def simple_discovery_old(db, goal_id: str):
    exists = db.query(TaskModel).filter(
        TaskModel.goal_id == goal_id,
        TaskModel.state == TaskState.PENDING
    ).first()

    if exists:
        return None

    task = TaskModel(
        goal_id=goal_id,
        title="探索下一步",
        hypothesis="执行这个任务可以减少当前最大不确定性"
    )

    db.add(task)
    db.commit()
    db.refresh(task)
    return task

def simple_discovery(db, goal_id: str):
    print(111)
    exists = db.query(TaskModel).filter(
        TaskModel.goal_id == goal_id,
        TaskModel.state == TaskState.PENDING
    ).first()

    print(222)
    # 若已存在待处理任务，直接返回该任务，避免 FastAPI response_model 校验报错
    if exists:
        return exists
    
    # 1. 根据 goal_id 查询 Goal 当前情况
    #    包括：目标愿景 + 已有任务（用于判断进展与不确定性）
    from todolistz.models import GoalModel

    goal = db.query(GoalModel).filter(GoalModel.id == goal_id).first()
    if not goal:
        return None

    tasks = db.query(TaskModel).filter(TaskModel.goal_id == goal_id).all()

    # 2. 调用 Agent 智能体（当前为规则型占位实现）
    #    输入：Goal 愿景 + 任务数量 + 已完成情况
    done_cnt = len([t for t in tasks if t.state in (TaskState.DONE, TaskState.LEARNED)])
    pending_cnt = len([t for t in tasks if t.state == TaskState.PENDING])

    # --- Agent 推理策略（可无缝替换为 LLM） ---

    import re

    def extract_(text: str, pattern_key = r"json",multi = False):
        pattern = r"```"+ pattern_key + r"([\s\S]*?)```"
        matches = re.findall(pattern, text)
        if multi:
            [match.strip() for match in matches]
            if matches:
                return [match.strip() for match in matches]    
            else:
                return ""  # 返回空字符串或抛出异常，此处返回空字符串
        else:
            if matches:
                return matches[0].strip()  # 添加strip()去除首尾空白符
            else:
                return ""  # 返回空字符串或抛出异常，此处返回空字符串


    from modusched.core import Adapter

    ada = Adapter(model_name="doubao-1-5-pro-32k-250115",type = 'ark')

    result = ada.predict(f"""你是一个任务拆解专家,
    {goal.name}
    {goal.vision}
    将当前的复杂任务, 拆解为可以开始行动的第一步的任务, 
    输出 title 和其 hypothesis (执行这个任务会有什么改进)
    输出格式:
    ```json
        "title":
        "hypothesis":
    ```
""")
    import json
    print(result,'result')

    result_json = json.loads(extract_(result))

    print(f'result_json : {result_json}')

    # print(f"version : {goal.name}:")

    # print(f"version : {goal.vision}:")
    # if done_cnt == 0:
    #     title = "拆解目标的第一步"
    #     hypothesis = f"通过澄清『{goal.name}』的第一步行动，可以降低整体方向不确定性"
    # elif pending_cnt == 0:
    #     title = "推进当前目标的关键阻塞点"
    #     hypothesis = f"识别并突破当前阻碍『{goal.name}』推进的最大瓶颈"
    # else:
    #     title = "验证当前进展是否有效"
    #     hypothesis = "通过执行该任务，可以验证已有行动是否在正确轨道上"

    title = result_json.get("title")
    hypothesis = result_json.get("hypothesis")


    task = TaskModel(
        goal_id=goal_id,
        title=title,
        hypothesis=hypothesis
    )

    db.add(task)
    db.commit()
    db.refresh(task)
    return task
