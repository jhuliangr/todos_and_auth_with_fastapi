import pytest
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from app.models.todo import ToDo

def test_todo_creation(db_session, test_user):
    """Test basic ToDo creation"""
    todo = ToDo(
        title="Comprar Pan",
        description="Ir al supermercado",
        state="pendiente",
        user_id=test_user.id
    )
    
    db_session.add(todo)
    db_session.commit()
    
    assert todo.id is not None
    assert todo.title == "Comprar Pan"
    assert todo.description == "Ir al supermercado"
    assert todo.state == "pendiente"
    assert todo.user_id == test_user.id
    assert isinstance(todo.created_at, datetime)
    assert todo.user == test_user

def test_todo_default_values(db_session, test_user):
    """Test default values for ToDo"""
    todo = ToDo(
        title="Tarea sin descripción",
        user_id=test_user.id
    )
    
    db_session.add(todo)
    db_session.commit()
    
    assert todo.description is None
    assert todo.state == "pendiente"
    assert todo.created_at is not None

def test_todo_required_fields(db_session, test_user):
    """Test required fields enforcement"""
    todo_without_title = ToDo(user_id=test_user.id)
    db_session.add(todo_without_title)
    
    with pytest.raises(IntegrityError):
        db_session.commit()
    
    db_session.rollback()
    
    todo_without_user = ToDo(title="Tarea sin usuario")
    db_session.add(todo_without_user)
    
    with pytest.raises(IntegrityError):
        db_session.commit()

def test_todo_state_validation(db_session, test_user):
    """Test state field validation"""
    todo = ToDo(
        title="Tarea completada",
        state="completado",
        user_id=test_user.id
    )
    
    db_session.add(todo)
    db_session.commit()
    
    assert todo.state == "completado"
    
    todo2 = ToDo(
        title="Tarea en progreso",
        state="pendiente",
        user_id=test_user.id
    )
    
    db_session.add(todo2)
    db_session.commit()
    
    assert todo2.state == "pendiente"


def test_todo_relationship_with_user(db_session, test_user):
    """Test relationship between ToDo and User"""
    todo = ToDo(
        title="Tarea con usuario",
        user_id=test_user.id
    )
    
    db_session.add(todo)
    db_session.commit()
    db_session.refresh(todo)
    
    assert todo.user == test_user
    assert todo in test_user.todos

def test_todo_timestamps(db_session, test_user):
    """Test automatic timestamping"""
    import time
    
    todo1 = ToDo(
        title="Tarea 1",
        user_id=test_user.id
    )
    
    db_session.add(todo1)
    db_session.commit()
    
    time.sleep(1)
    
    todo2 = ToDo(
        title="Tarea 2",
        user_id=test_user.id
    )
    
    db_session.add(todo2)
    db_session.commit()
    
    assert todo1.created_at is not None
    assert todo2.created_at is not None
    
    assert todo2.created_at > todo1.created_at

def test_todo_uuid_generation(db_session, test_user):
    """Test UUID generation for ToDo"""
    todo1 = ToDo(
        title="Tarea UUID 1",
        user_id=test_user.id
    )
    
    todo2 = ToDo(
        title="Tarea UUID 2",
        user_id=test_user.id
    )
    
    db_session.add_all([todo1, todo2])
    db_session.commit()
    
    assert todo1.id != todo2.id
    assert len(todo1.id) == 36
    assert len(todo2.id) == 36


def test_todo_delete_cascade(db_session, test_user):
    """Behavior on user deletion"""
    todo = ToDo(
        title="Tarea para eliminar",
        user_id=test_user.id
    )
    
    db_session.add(todo)
    db_session.commit()
    
    todo_id = todo.id
    
    db_session.delete(test_user)
    db_session.commit()
    
    deleted_todo = db_session.get(ToDo, todo_id)
    assert deleted_todo is None or deleted_todo.user_id is None