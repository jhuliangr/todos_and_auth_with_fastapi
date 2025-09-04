import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from jose import jwt
from main import app
from database import Base, get_db
from app.models.user import User
from app.models.todo import ToDo
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Creates a new database session for a test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    connection.close()

@pytest.fixture(scope="function")
def test_user(db_session):
    """Fixture for a test user"""
    user = User(
        id="user123",
        email="test@example.com",
        hashed_password="hashedpassword123",
        username="testuser"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def test_todo(db_session, test_user):
    """Fixture for a test ToDo"""
    todo = ToDo(
        id="todo123",
        title="Test Todo",
        description="Test Description",
        user_id=test_user.id
    )
    db_session.add(todo)
    db_session.commit()
    db_session.refresh(todo)
    return todo

@pytest.fixture(scope="function")
def test_todos_batch(db_session, test_user):
    """Fixture for multiple test ToDos"""
    todos = []
    for i in range(3):
        todo = ToDo(
            title=f"Test Todo {i}",
            description=f"Test Description {i}",
            state="pendiente",
            user_id=test_user.id
        )
        db_session.add(todo)
        todos.append(todo)
    
    db_session.commit()
    
    for todo in todos:
        db_session.refresh(todo)
    
    return todos

@pytest.fixture
def valid_token():
    """Generates a valid JWT token for testing"""
    payload = {"sub": "testuser"}
    return jwt.encode(payload, "test_secret_key", algorithm="HS256")

@pytest.fixture
def invalid_token():
    """Invalid token with wrong signature"""
    payload = {"sub": "testuser"}
    return jwt.encode(payload, "wrong_secret_key", algorithm="HS256")

@pytest.fixture
def expired_token():
    """Expired token"""
    payload = {"sub": "testuser"}
    return jwt.encode(payload, "test_secret_key", algorithm="HS256")

@pytest.fixture
def mock_db_session():
    """Mock of the async database session"""
    return AsyncMock(spec=AsyncSession)

@pytest.fixture(autouse=True)
def mock_dependencies():
    """Mock of dependencies like get_settings and get_user_by_username"""
    with patch('app.crud.auth.get_settings') as mock_settings, \
         patch('app.crud.auth.get_user_by_username') as mock_get_user:
        
        mock_settings_instance = MagicMock()
        mock_settings_instance.SECRET_KEY = "test_secret_key"
        mock_settings_instance.ALGORITHM = "HS256"
        mock_settings.return_value = mock_settings_instance
        
        mock_get_user.coro = AsyncMock()
        
        yield mock_settings, mock_get_user

@pytest.fixture
def valid_login_form():
    """Valid login form"""
    return OAuth2PasswordRequestForm(
        username="testuser",
        password="correctpassword",
        scope=""
    )

@pytest.fixture
def invalid_login_form():
    """Invalid login form with wrong password"""
    return OAuth2PasswordRequestForm(
        username="testuser",
        password="wrongpassword",
        scope=""
    )

@pytest.fixture
def test_client():
    """Client for testing the FastAPI app"""
    from main import app
    return TestClient(app)

@pytest.fixture
def current_user():
    """Current authenticated user"""
    return {"id": "user123", "email": "test@example.com"}

@pytest.fixture
def other_user():
    """Another user (not the current one)"""
    return {"id": "user456", "email": "other@example.com"}

@pytest.fixture
def other_user_todo(other_user):
    """Todo belonging to another user"""
    return ToDo(
        id="todo456",
        title="Other User Todo",
        description="Other Description",
        state="pendiente",
        user_id=other_user["id"]
    )

@pytest.fixture
def sample_todo_data():
    """Data for creating a new todo"""
    return {
        "title": "New Todo",
        "description": "New Description",
        "state": "pendiente"
    }

@pytest.fixture
def sample_todo_update():
    """Data to update a todo"""
    return {
        "title": "Updated Todo",
        "state": "completado"
    }