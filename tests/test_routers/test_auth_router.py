import pytest
from fastapi import status, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.routers.auth import router, login_for_access_token
from app.models.user import User


@pytest.mark.asyncio
async def test_login_successful(mock_db_session, test_user, valid_login_form):
    """Test of login with valid credentials"""
    with patch('app.routers.auth.authenticate_user', AsyncMock(return_value=test_user)), \
         patch('app.routers.auth.create_access_token', return_value="mock_jwt_token"):
        
        response = await login_for_access_token(valid_login_form, mock_db_session)
        
        assert response == {"access_token": "mock_jwt_token", "token_type": "bearer"}
        
        from app.routers.auth import authenticate_user
        authenticate_user.assert_called_once_with(mock_db_session, "testuser", "correctpassword")
        
        from app.routers.auth import create_access_token
        create_access_token.assert_called_once_with(data={"sub": "testuser"})

@pytest.mark.asyncio
async def test_login_invalid_credentials(mock_db_session, invalid_login_form):
    """Test of login with invalid credentials"""
    with patch('app.routers.auth.authenticate_user', AsyncMock(return_value=False)):
        
        with pytest.raises(HTTPException) as exc_info:
            await login_for_access_token(invalid_login_form, mock_db_session)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Usuario o contraseña incorrectos"
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}

@pytest.mark.asyncio
async def test_login_nonexistent_user(mock_db_session, invalid_login_form):
    """Test of login with non-existent user"""
    with patch('app.routers.auth.authenticate_user', AsyncMock(return_value=False)):
        
        with pytest.raises(HTTPException) as exc_info:
            await login_for_access_token(invalid_login_form, mock_db_session)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Usuario o contraseña incorrectos"

@pytest.mark.asyncio
async def test_login_empty_username(mock_db_session):
    """Test of login with empty username"""
    empty_username_form = OAuth2PasswordRequestForm(
        username="",
        password="somepassword",
        scope=""
    )
    
    with patch('app.routers.auth.authenticate_user', AsyncMock(return_value=False)):
        
        with pytest.raises(HTTPException) as exc_info:
            await login_for_access_token(empty_username_form, mock_db_session)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_login_empty_password(mock_db_session):
    """Test of login with empty password"""
    empty_password_form = OAuth2PasswordRequestForm(
        username="testuser",
        password="",
        scope=""
    )
    
    with patch('app.routers.auth.authenticate_user', AsyncMock(return_value=False)):
        
        with pytest.raises(HTTPException) as exc_info:
            await login_for_access_token(empty_password_form, mock_db_session)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_login_token_creation_error(mock_db_session, test_user, valid_login_form):
    """Test of login when token creation fails"""
    with patch('app.routers.auth.authenticate_user', AsyncMock(return_value=test_user)), \
         patch('app.routers.auth.create_access_token', side_effect=Exception("Token error")):
        
        with pytest.raises(Exception) as exc_info:
            await login_for_access_token(valid_login_form, mock_db_session)
        
        assert "Token error" in str(exc_info.value)

@pytest.mark.asyncio
async def test_login_with_different_username_cases(mock_db_session, test_user):
    """Test of login with different username cases"""
    def mock_authenticate(db, username, password):
        return test_user if username == "testuser" else False
    
    with patch('app.routers.auth.authenticate_user', AsyncMock(side_effect=mock_authenticate)), \
         patch('app.routers.auth.create_access_token', return_value="mock_token"):
        
        correct_case_form = OAuth2PasswordRequestForm(
            username="testuser",
            password="correctpassword",
            scope=""
        )
        
        response = await login_for_access_token(correct_case_form, mock_db_session)
        assert response["access_token"] == "mock_token"
        
        wrong_case_form = OAuth2PasswordRequestForm(
            username="TestUser", 
            password="correctpassword",
            scope=""
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await login_for_access_token(wrong_case_form, mock_db_session)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_login_response_structure(mock_db_session, test_user, valid_login_form):
    """Test of the structure of the login response"""
    with patch('app.routers.auth.authenticate_user', AsyncMock(return_value=test_user)), \
         patch('app.routers.auth.create_access_token', return_value="test_jwt_token_123"):
        
        response = await login_for_access_token(valid_login_form, mock_db_session)
        
        assert "access_token" in response
        assert "token_type" in response
        assert response["access_token"] == "test_jwt_token_123"
        assert response["token_type"] == "bearer"
        assert len(response) == 2 

@pytest.mark.asyncio
async def test_integration_login_endpoint(test_client, test_user):
    """Test of integration for /login endpoint with valid credentials"""
    
    with patch('app.routers.auth.authenticate_user', AsyncMock(return_value=test_user)), \
         patch('app.routers.auth.create_access_token', return_value="integration_token"):
        
        form_data = {
            "username": "testuser",
            "password": "correctpassword"
        }
        
        response = test_client.post("/api/v1/login", data=form_data)
        
        assert response.status_code == 200
        assert response.json() == {
            "access_token": "integration_token",
            "token_type": "bearer"
        }

@pytest.mark.asyncio
async def test_integration_login_endpoint_invalid(test_client):
    """integration test for /login endpoint with invalid credentials"""
    with patch('app.routers.auth.authenticate_user', AsyncMock(return_value=False)):
        
        form_data = {
            "username": "testuser",
            "password": "wrongpassword"
        }
        
        response = test_client.post("/api/v1/login", data=form_data)
        
        assert response.status_code == 401
        assert response.json() == {"detail": "Usuario o contraseña incorrectos"}
        assert "WWW-Authenticate" in response.headers
        assert response.headers["WWW-Authenticate"] == "Bearer"

@pytest.mark.asyncio
async def test_integration_login_endpoint_missing_fields(test_client):
    """integration test for /login endpoint with missing fields"""

    form_data = {"username": "testuser"}
    response = test_client.post("/api/v1/login", data=form_data)
    assert response.status_code == 422
    
    form_data = {"password": "testpassword"}
    response = test_client.post("/api/v1/login", data=form_data)
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_router_configuration():
    """Test configuration of the auth router"""
    assert router.tags == ["authentication"]
    assert len(router.routes) == 1
    
    route = router.routes[0]
    assert route.path == "/login"
    assert route.methods == {"POST"}


@pytest.mark.asyncio
async def test_login_with_special_characters(mock_db_session):
    """Test of login with special characters in username and password"""
    special_user = User(
        id="special123",
        username="userñáéíóú",
        email="special@test.com",
        hashed_password="hashed_special"
    )
    
    with patch('app.routers.auth.authenticate_user', AsyncMock(return_value=special_user)), \
         patch('app.routers.auth.create_access_token', return_value="special_token"):
        
        special_form = OAuth2PasswordRequestForm(
            username="userñáéíóú",
            password="passwordñáéíóú",
            scope=""
        )
        
        response = await login_for_access_token(special_form, mock_db_session)
        assert response["access_token"] == "special_token"
        
        from app.routers.auth import authenticate_user
        authenticate_user.assert_called_once_with(mock_db_session, "userñáéíóú", "passwordñáéíóú")

@pytest.mark.asyncio
async def test_login_with_long_credentials(mock_db_session, test_user):
    """Test of login with very long username and password"""
    long_username = "a" * 100
    long_password = "b" * 100
    
    with patch('app.routers.auth.authenticate_user', AsyncMock(return_value=test_user)), \
         patch('app.routers.auth.create_access_token', return_value="long_token"):
        
        long_form = OAuth2PasswordRequestForm(
            username=long_username,
            password=long_password,
            scope=""
        )
        
        response = await login_for_access_token(long_form, mock_db_session)
        assert response["access_token"] == "long_token"
        
        from app.routers.auth import authenticate_user
        authenticate_user.assert_called_once_with(mock_db_session, long_username, long_password)