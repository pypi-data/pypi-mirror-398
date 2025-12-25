import pytest
from todolistz.toolkit import GoalAPIToolkit, TaskAPIToolkit
from todolistz.models import GoalModel, TaskModel, TaskState
from todolistz.database import SessionLocal



@pytest.fixture

def db():
    db = SessionLocal()
    return db

def test_goal_toolkit_create_goal():
    toolkit = GoalAPIToolkit()
    name = "Test Goal2"
    vision="Test Vision12"
    # 执行创建
    result = toolkit.create_goal(name=name, 
                                 vision=vision)
    
    db = SessionLocal()

    result = db.query(GoalModel).filter(GoalModel.name== name).first()

    assert result.vision == vision

# 测试 Goal.name 唯一


def test_goal_toolkit_list_goals(db):
    toolkit = GoalAPIToolkit()
    result = toolkit.list_goals()
    print(result)

def test_task_toolkit_mine_task_right(db): 
    toolkit = TaskAPIToolkit()
    
    result = toolkit.mine_task(goal_id="4a15d57e-e946-4dcf-a43e-b867a709c08f")
    print(result)


def test_task_toolkit_mine_task(db): 
    # 输入错误的goal-id
    toolkit = TaskAPIToolkit()
    
    result = toolkit.mine_task(goal_id="goal-1")
    print(result)



def test_task_toolkit_pull_task(db):
    toolkit = TaskAPIToolkit()

    result = toolkit.pull_task(goal_id="4a15d57e-e946-4dcf-a43e-b867a709c08f")
    print(result)
    

def test_task_toolkit_execute_task(mock_db):
    toolkit = TaskAPIToolkit()
    
    with patch("todolistz.toolkit.executor.execute_task") as mock_exec:
        mock_task = MockModel(id="task-1", state="learned")
        mock_exec.return_value = mock_task
        
        result = toolkit.execute_task(task_id="task-1")
        
        mock_exec.assert_called_once_with(mock_db, "task-1")
        assert result["id"] == "task-1"