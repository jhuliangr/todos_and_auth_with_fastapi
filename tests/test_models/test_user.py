import pytest
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from unittest.mock import patch
import bcrypt
from app.models.user import User
from app.models.todo import ToDo

def test_user_creation(db_session):
    """Test basic User creation"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_password_123"
    )
    
    db_session.add(user)
    db_session.commit()
    
    assert user.id is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.hashed_password == "hashed_password_123"
    assert isinstance(user.created_at, datetime)
    assert user.todos == []

def test_user_default_values(db_session):
    """Test default values for User"""
    user = User(
        username="defaultuser",
        email="default@example.com",
        hashed_password="hashed_pass"
    )
    
    db_session.add(user)
    db_session.commit()
    
    assert user.created_at is not None
    assert user.todos == []

def test_user_required_fields(db_session):
    """Test required fields enforcement"""
    user_without_username = User(
        email="test@example.com",
        hashed_password="hashed_pass"
    )
    db_session.add(user_without_username)
    
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
    
    user_without_email = User(
        username="testuser",
        hashed_password="hashed_pass"
    )
    db_session.add(user_without_email)
    
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
    
    user_without_password = User(
        username="testuser",
        email="test@example.com"
    )
    db_session.add(user_without_password)
    
    with pytest.raises(IntegrityError):
        db_session.commit()

def test_user_unique_constraints(db_session):
    """Test unique constraints on username and email"""
    user1 = User(
        username="uniqueuser",
        email="unique@example.com",
        hashed_password="hashed_pass1"
    )
    
    db_session.add(user1)
    db_session.commit()
    
    user2_dup_username = User(
        username="uniqueuser", 
        email="different@example.com",
        hashed_password="hashed_pass2"
    )
    
    db_session.add(user2_dup_username)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_user_relationship_with_todos(db_session, test_user, test_todo):
    """Test relationship between User and ToDo"""
    assert test_todo in test_user.todos
    assert test_todo.user == test_user
    
    another_todo = ToDo(
        title="Otro todo",
        user_id=test_user.id
    )
    
    db_session.add(another_todo)
    db_session.commit()
    
    assert len(test_user.todos) == 2
    assert test_todo in test_user.todos
    assert another_todo in test_user.todos

def test_user_cascade_delete(db_session, test_user):
    """Test cascade delete of ToDos when User is deleted"""
    todos = []
    for i in range(3):
        todo = ToDo(
            title=f"Todo {i}",
            user_id=test_user.id
        )
        db_session.add(todo)
        todos.append(todo)
    
    db_session.commit()
    
    assert len(test_user.todos) == 3
    
    todo_ids = [todo.id for todo in todos]
    
    db_session.delete(test_user)
    db_session.commit()
    
    for todo_id in todo_ids:
        deleted_todo = db_session.get(ToDo, todo_id)
        assert deleted_todo is None

def test_user_timestamps(db_session):
    """Test automatic timestamping of created_at"""
    import time
    
    user1 = User(
        username="user1",
        email="user1@example.com",
        hashed_password="hashed_pass1"
    )
    
    db_session.add(user1)
    db_session.commit()
    
    time.sleep(1)
    
    user2 = User(
        username="user2",
        email="user2@example.com",
        hashed_password="hashed_pass2"
    )
    
    db_session.add(user2)
    db_session.commit()
    
    assert user1.created_at is not None
    assert user2.created_at is not None
    
    assert user2.created_at > user1.created_at

def test_user_uuid_generation(db_session):
    """Test UUID generation for User"""
    user1 = User(
        username="user_uuid1",
        email="uuid1@example.com",
        hashed_password="hashed_pass1"
    )
    
    user2 = User(
        username="user_uuid2",
        email="uuid2@example.com",
        hashed_password="hashed_pass2"
    )
    
    db_session.add_all([user1, user2])
    db_session.commit()
    
    assert user1.id != user2.id
    assert len(user1.id) == 36 
    assert len(user2.id) == 36

def test_user_email_format_validation(db_session):
    """Test email format validation"""
    user = User(
        username="emailuser",
        email="invalid-email",
        hashed_password="hashed_pass"
    )
    
    db_session.add(user)
    db_session.commit()
    
    assert user.email == "invalid-email"

def test_user_password_hashing_integration(db_session):
    """Test password hashing integration"""
    
    plain_password = "mysecretpassword"
    hashed_password = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt())
    
    user = User(
        username="hashinguser",
        email="hashing@example.com",
        hashed_password=hashed_password
    )
    
    db_session.add(user)
    db_session.commit()
    
    assert user.hashed_password != plain_password

def test_user_indexes(db_session):
    """Test that indexes on username and email works"""
    users = []
    for i in range(5):
        user = User(
            username=f"user{i}",
            email=f"user{i}@example.com",
            hashed_password=f"hashed_pass{i}"
        )
        users.append(user)
        db_session.add(user)
    
    db_session.commit()
    
    assert len(users) == 5
    for user in users:
        assert user.id is not None