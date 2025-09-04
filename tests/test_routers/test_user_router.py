import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.crud.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from datetime import datetime

@pytest.fixture
def current_user():
    """Actual user for authentication"""
    return {"id": "user123", "email": "test@example.com", "username": "testuser"}

@pytest.fixture
def sample_user(current_user):
    """Example user object"""
    return User(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user["email"],
        hashed_password="hashed_password", 
        created_at=datetime(2023, 1, 1, 12, 0, 0)
    )

@pytest.fixture
def sample_user_data():
    """Data for creating a new user"""
    return {
        "username": "newuser",
        "email": "new@example.com",
        "password": "password123"
    }

@pytest.fixture
def sample_user_update():
    """Data for updating an user"""
    return {
        "username": "updateduser",
        "password": "newpassword123"
    }

@pytest.mark.asyncio
async def test_user_create_success(mock_db_session, sample_user_data, sample_user):
    """Test for successful user creation"""
    from app.routers.user import user_create
    
    user_create_data = UserCreate(**sample_user_data)
    
    with patch('app.routers.user.create_user', AsyncMock(return_value=sample_user)):
        
        result = await user_create(user=user_create_data, db=mock_db_session)
        
        assert result.id == "user123"
        assert result.email == "test@example.com"
        
        from app.routers.user import create_user
        create_user.assert_called_once_with(mock_db_session, user_create_data)

@pytest.mark.asyncio
async def test_user_create_minimal_data(mock_db_session):
    """Test for user creation with minimal data"""
    from app.routers.user import user_create
    
    user_data = UserCreate(
        username="minimaluser",
        email="minimal@example.com",
        password="minimalpass"
    )
    
    created_user = User(
        id="minimal123",
        username="minimaluser",
        email="minimal@example.com",
        hashed_password="hashed_minimal"
    )
    
    with patch('app.routers.user.create_user', AsyncMock(return_value=created_user)):
        
        result = await user_create(user=user_data, db=mock_db_session)
        
        assert result.username == "minimaluser"
        assert result.email == "minimal@example.com"

@pytest.mark.asyncio
async def test_read_user_success(mock_db_session, current_user, sample_user):
    """Test for successful user retrieval"""
    from app.routers.user import read_user
    
    with patch('app.routers.user.get_user_by_email', AsyncMock(return_value=sample_user)):
        
        result = await read_user(db=mock_db_session, current_user=current_user)
        
        assert result.id == current_user["id"]
        assert result.email == current_user["email"]
        
        from app.routers.user import get_user_by_email
        get_user_by_email.assert_called_once_with(mock_db_session, "test@example.com")

@pytest.mark.asyncio
async def test_read_user_not_found(mock_db_session, current_user):
    """Test for user not found"""
    from app.routers.user import read_user
    
    with patch('app.routers.user.get_user_by_email', AsyncMock(return_value=None)):
        
        with pytest.raises(HTTPException) as exc_info:
            await read_user(db=mock_db_session, current_user=current_user)
        
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "User not found or unauthorized"

@pytest.mark.asyncio
async def test_read_user_id_mismatch(mock_db_session, current_user):
    """Test for user ID mismatch"""
    from app.routers.user import read_user
    
    wrong_user = User(
        id="different_id",
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_pass"
    )
    
    with patch('app.routers.user.get_user_by_email', AsyncMock(return_value=wrong_user)):
        
        with pytest.raises(HTTPException) as exc_info:
            await read_user(db=mock_db_session, current_user=current_user)
        
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "User not found or unauthorized"

@pytest.mark.asyncio
async def test_update_user_by_email_success(mock_db_session, current_user, sample_user, sample_user_update):
    """Test for successful user update"""
    from app.routers.user import update_user_by_email
    
    user_update_data = UserUpdate(**sample_user_update)
    updated_user = User(
        id=current_user["id"],
        username="updateduser",
        email=current_user["email"],
        hashed_password="new_hashed_password"
    )
    
    with patch('app.routers.user.get_user_by_email', AsyncMock(return_value=sample_user)), \
         patch('app.routers.user.update_user', AsyncMock(return_value=updated_user)), \
         patch('app.routers.user.create_access_token', return_value="new_jwt_token"):
        
        result = await update_user_by_email(
            user_update=user_update_data, 
            db=mock_db_session, 
            current_user=current_user
        )
        
        assert "user" in result
        assert "access_token" in result
        assert result["user"].username == "updateduser"
        assert result["access_token"] == "new_jwt_token"
        
        from app.routers.user import update_user, create_access_token
        update_user.assert_called_once_with(mock_db_session, "test@example.com", user_update_data)
        create_access_token.assert_called_once_with(data={"sub": "updateduser"})

@pytest.mark.asyncio
async def test_update_user_by_email_not_found(mock_db_session, current_user, sample_user_update):
    """Test for updating a non-existent user"""
    from app.routers.user import update_user_by_email
    
    user_update_data = UserUpdate(**sample_user_update)
    
    with patch('app.routers.user.get_user_by_email', AsyncMock(return_value=None)):
        
        with pytest.raises(HTTPException) as exc_info:
            await update_user_by_email(
                user_update=user_update_data, 
                db=mock_db_session, 
                current_user=current_user
            )
        
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "User not found or unauthorized"

@pytest.mark.asyncio
async def test_update_user_by_email_id_mismatch(mock_db_session, current_user, sample_user_update):
    """Test for user update with ID mismatch"""
    from app.routers.user import update_user_by_email
    
    user_update_data = UserUpdate(**sample_user_update)
    
    wrong_user = User(
        id="different_id",
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_pass"
    )
    
    with patch('app.routers.user.get_user_by_email', AsyncMock(return_value=wrong_user)):
        
        with pytest.raises(HTTPException) as exc_info:
            await update_user_by_email(
                user_update=user_update_data, 
                db=mock_db_session, 
                current_user=current_user
            )
        
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "User not found or unauthorized"

@pytest.mark.asyncio
async def test_update_user_by_email_partial(mock_db_session, current_user, sample_user):
    """Test for partial user update (only username)"""
    from app.routers.user import update_user_by_email
    
    partial_update = UserUpdate(username="newusername")
    updated_user = User(
        id=current_user["id"],
        username="newusername",
        email=current_user["email"],
        hashed_password=sample_user.hashed_password
    )
    
    with patch('app.routers.user.get_user_by_email', AsyncMock(return_value=sample_user)), \
         patch('app.routers.user.update_user', AsyncMock(return_value=updated_user)), \
         patch('app.routers.user.create_access_token', return_value="partial_token"):
        
        result = await update_user_by_email(
            user_update=partial_update, 
            db=mock_db_session, 
            current_user=current_user
        )
        
        assert result["user"].username == "newusername"
        assert result["user"].email == current_user["email"]  

@pytest.mark.asyncio
async def test_update_user_by_email_only_password(mock_db_session, current_user, sample_user):
    """Test for updating only the password"""
    from app.routers.user import update_user_by_email
    
    password_update = UserUpdate(password="newpassword123")
    updated_user = User(
        id=current_user["id"],
        username=sample_user.username,
        email=current_user["email"],
        hashed_password="new_hashed_password"
    )
    
    with patch('app.routers.user.get_user_by_email', AsyncMock(return_value=sample_user)), \
         patch('app.routers.user.update_user', AsyncMock(return_value=updated_user)), \
         patch('app.routers.user.create_access_token', return_value="password_token"):
        
        result = await update_user_by_email(
            user_update=password_update, 
            db=mock_db_session, 
            current_user=current_user
        )
        
        assert result["user"].username == sample_user.username 
        from app.routers.user import create_access_token
        create_access_token.assert_called_once_with(data={"sub": sample_user.username})

@pytest.mark.asyncio
async def test_user_delete_success(mock_db_session, current_user, sample_user):
    """Test for successful user deletion"""
    from app.routers.user import user_delete
    
    with patch('app.routers.user.get_user_by_email', AsyncMock(return_value=sample_user)), \
         patch('app.routers.user.delete_user', AsyncMock(return_value=sample_user)):
        
        result = await user_delete(db=mock_db_session, current_user=current_user)
        
        assert result == {"message": "User deleted successfully"}
        
        from app.routers.user import delete_user
        delete_user.assert_called_once_with(mock_db_session, "test@example.com")

@pytest.mark.asyncio
async def test_user_delete_not_found(mock_db_session, current_user):
    """Test for deleting a non-existent user"""
    from app.routers.user import user_delete
    
    with patch('app.routers.user.get_user_by_email', AsyncMock(return_value=None)):
        
        with pytest.raises(HTTPException) as exc_info:
            await user_delete(db=mock_db_session, current_user=current_user)
        
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "User not found or unauthorized"

@pytest.mark.asyncio
async def test_user_delete_id_mismatch(mock_db_session, current_user):
    """Test for user deletion with ID mismatch"""
    from app.routers.user import user_delete
    
    wrong_user = User(
        id="different_id",
        username="testuser",
        email="test@example.com",
        hashed_password="hashed_pass"
    )
    
    with patch('app.routers.user.get_user_by_email', AsyncMock(return_value=wrong_user)):
        
        with pytest.raises(HTTPException) as exc_info:
            await user_delete(db=mock_db_session, current_user=current_user)
        
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail == "User not found or unauthorized"


async def mock_get_current_user():
    return {"id": "user123", "email": "test@example.com"}

@pytest.fixture
def test_client():
    """Client for testing the FastAPI app"""
    from main import app
    app.dependency_overrides[get_current_user] = mock_get_current_user
    return TestClient(app)        

@pytest.mark.asyncio
async def test_integration_user_crud(test_client, current_user, sample_user):
    """Integration test for user CRUD operations"""
    
    with patch('app.routers.user.get_current_user', AsyncMock(return_value=current_user)), \
         patch('app.routers.user.get_user_by_email', AsyncMock(return_value=sample_user)), \
         patch('app.routers.user.update_user', AsyncMock(return_value=sample_user)), \
         patch('app.routers.user.delete_user', AsyncMock(return_value=sample_user)), \
         patch('app.routers.user.create_access_token', return_value="test_token"):
        
        response = test_client.get("/api/v1/user/", headers={"Authorization": "Bearer mock_token"})
        assert response.status_code == 200
        assert response.json()["email"] == current_user["email"]
        
        update_data = {"username": "updateduser", "password": "newpass123"}
        update_response = test_client.put(
            "/api/v1/user/", 
            json=update_data, 
            headers={"Authorization": "Bearer mock_token"}
        )
        assert update_response.status_code == 200
        assert "user" in update_response.json()
        assert "access_token" in update_response.json()
        
        delete_response = test_client.delete(
            "/api/v1/user/", 
            headers={"Authorization": "Bearer mock_token"}
        )
        assert delete_response.status_code == 204
