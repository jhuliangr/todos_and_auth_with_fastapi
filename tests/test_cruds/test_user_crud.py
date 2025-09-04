import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import bcrypt

from app.crud.user import (
    get_user_by_username,
    get_user_by_email,
    create_user,
    update_user,
    delete_user,
    authenticate_user
)
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

@pytest.mark.asyncio
async def test_get_user_by_username_found(mock_db_session, test_user):
    """Test for getting user by existing username"""
    mock_result = MagicMock()
    mock_result.scalars().first.return_value = test_user
    mock_db_session.execute.return_value = mock_result
    
    result = await get_user_by_username(mock_db_session, "testuser")
    
    mock_db_session.execute.assert_called_once()
    called_stmt = mock_db_session.execute.call_args[0][0]
    
    assert "users.username = :username_1" in str(called_stmt)
    assert result.username == "testuser"
    assert result.email == "test@example.com"

@pytest.mark.asyncio
async def test_get_user_by_username_not_found(mock_db_session):
    """Test for getting user by username that does not exist"""
    mock_result = MagicMock()
    mock_result.scalars().first.return_value = None
    mock_db_session.execute.return_value = mock_result
    
    result = await get_user_by_username(mock_db_session, "nonexistent")
    
    assert result is None
    mock_db_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_get_user_by_email_found(mock_db_session, test_user):
    """Test for getting user by existing email"""
    mock_result = MagicMock()
    mock_result.scalars().first.return_value = test_user
    mock_db_session.execute.return_value = mock_result
    
    result = await get_user_by_email(mock_db_session, "test@example.com")
    
    mock_db_session.execute.assert_called_once()
    called_stmt = mock_db_session.execute.call_args[0][0]
    
    assert "users.email = :email_1" in str(called_stmt)
    assert result.email == "test@example.com"
    assert result.username == "testuser"

@pytest.mark.asyncio
async def test_get_user_by_email_not_found(mock_db_session):
    """Test for getting user by email that does not exist"""
    mock_result = MagicMock()
    mock_result.scalars().first.return_value = None
    mock_db_session.execute.return_value = mock_result
    
    result = await get_user_by_email(mock_db_session, "nonexistent@example.com")
    
    assert result is None
    mock_db_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_create_user_success(mock_db_session, test_user):
    """Test for successful user creation"""
    user_create = UserCreate(username=test_user.username, email=test_user.email, password="plainpassword123")
    mock_db_session.refresh.return_value = None
    
    result = await create_user(mock_db_session, user_create)
    
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once()
    
    added_user = mock_db_session.add.call_args[0][0]
    assert isinstance(added_user, User)
    assert added_user.username == "testuser"
    assert added_user.email == "test@example.com"
    assert added_user.hashed_password != "plainpassword123"
    assert bcrypt.checkpw("plainpassword123".encode('utf-8'), added_user.hashed_password.encode('utf-8'))

@pytest.mark.asyncio
async def test_create_user_password_hashing(mock_db_session):
    """Test for password hashing during user creation"""
    user_data = {
        "username": "hashing_test",
        "email": "hashing@test.com",
        "password": "differentpassword"
    }
    user_create = UserCreate(**user_data)
    mock_db_session.refresh.return_value = None
    
    await create_user(mock_db_session, user_create)
    
    added_user = mock_db_session.add.call_args[0][0]
    assert added_user.hashed_password != "differentpassword"
    assert bcrypt.checkpw("differentpassword".encode('utf-8'), added_user.hashed_password.encode('utf-8'))
    assert not bcrypt.checkpw("wrongpassword".encode('utf-8'), added_user.hashed_password.encode('utf-8'))

@pytest.mark.asyncio
async def test_update_user_found(mock_db_session, test_user):
    """Test for updating an existing user"""
    with patch('app.crud.user.get_user_by_email', AsyncMock(return_value=test_user)):
        update_data = UserUpdate(
            username="updateduser",
            password="newpassword123"
        )
        
        result = await update_user(mock_db_session, "test@example.com", update_data)
        

        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(test_user)
        
        assert result.username == "updateduser"
        assert bcrypt.checkpw("newpassword123".encode('utf-8'), result.hashed_password.encode('utf-8'))
        assert result.email == "test@example.com"


@pytest.mark.asyncio
async def test_update_user_only_password(mock_db_session, test_user):
    """Test for updating only the password"""
    with patch('app.crud.user.get_user_by_email', AsyncMock(return_value=test_user)):
        original_username = test_user.username
        original_email = test_user.email
        
        update_data = UserUpdate(password="brandnewpassword")
        
        result = await update_user(mock_db_session, "test@example.com", update_data)
        
        assert result.username == original_username
        assert result.email == original_email
        assert bcrypt.checkpw("brandnewpassword".encode('utf-8'), result.hashed_password.encode('utf-8'))
        assert not bcrypt.checkpw("plainpassword123".encode('utf-8'), result.hashed_password.encode('utf-8'))

@pytest.mark.asyncio
async def test_delete_user_found(mock_db_session, test_user):
    """Test for deleting an existing user"""
    with patch('app.crud.user.get_user_by_email', AsyncMock(return_value=test_user)):
        result = await delete_user(mock_db_session, "test@example.com")
        
        mock_db_session.delete.assert_called_once_with(test_user)
        mock_db_session.commit.assert_called_once()
        
        assert result == test_user

@pytest.mark.asyncio
async def test_delete_user_not_found(mock_db_session):
    """Test for deleting a user that does not exist"""
    with patch('app.crud.user.get_user_by_email', AsyncMock(return_value=None)):
        result = await delete_user(mock_db_session, "nonexistent@example.com")
        
        mock_db_session.delete.assert_not_called()
        mock_db_session.commit.assert_not_called()
        assert result is None

@pytest.mark.asyncio
async def test_authenticate_user_nonexistent_user(mock_db_session):
    """Test for authenticating with a username that does not exist"""
    with patch('app.crud.user.get_user_by_username', AsyncMock(return_value=None)):
        result = await authenticate_user(mock_db_session, "nonexistent", "anypassword")
        
        assert result is False

@pytest.mark.asyncio
async def test_create_user_exception_handling(mock_db_session, test_user):
    """Test for exception handling during user creation"""
    user_create = UserCreate(username=test_user.username, email=test_user.email, password="plainpassword123")
    
    mock_db_session.commit.side_effect = Exception("Database error")
    
    with pytest.raises(Exception, match="Database error"):
        await create_user(mock_db_session, user_create)
    
    mock_db_session.add.assert_called_once()


@pytest.mark.asyncio
async def test_bcrypt_round_trip(mock_db_session):
    """Test to verify bcrypt hashing and checking works end-to-end"""
    from app.crud.user import create_user, authenticate_user
    
    mock_db_session.refresh.return_value = None
    user_create = UserCreate(
        username="bcrypt_test",
        email="bcrypt@test.com",
        password="testpassword123"
    )
    
    await create_user(mock_db_session, user_create)
    
    created_user = mock_db_session.add.call_args[0][0]
    
    with patch('app.crud.user.get_user_by_username', AsyncMock(return_value=created_user)):
        auth_result = await authenticate_user(mock_db_session, "bcrypt_test", "testpassword123")
        assert auth_result == created_user
        
        auth_result_wrong = await authenticate_user(mock_db_session, "bcrypt_test", "wrongpassword")
        assert auth_result_wrong is False