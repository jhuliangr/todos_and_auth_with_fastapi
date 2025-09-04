import pytest
from fastapi import HTTPException, status
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt
from app.crud.auth import get_current_user, oauth2_scheme
from app.models.user import User


@pytest.mark.asyncio
async def test_get_current_user_valid_token(mock_db_session, valid_token, test_user, mock_dependencies):
    """Test of valid token"""
    _, mock_get_user = mock_dependencies
    
    mock_get_user.return_value = test_user
    
    with patch('app.crud.auth.oauth2_scheme') as mock_oauth:
        mock_oauth.return_value = valid_token
        
        result = await get_current_user(token=valid_token, db=mock_db_session)
        
        mock_get_user.assert_called_once_with(mock_db_session, username="testuser")
        assert result == {"id": "user123", "email": "test@example.com"}

@pytest.mark.asyncio
async def test_get_current_user_invalid_token_signature(mock_db_session, invalid_token):
    """Test of invalid token signature"""
    with patch('app.crud.auth.oauth2_scheme') as mock_oauth:
        mock_oauth.return_value = invalid_token
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=invalid_token, db=mock_db_session)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Invalid credentials"

@pytest.mark.asyncio
async def test_get_current_user_malformed_token(mock_db_session):
    """Test of malformed token"""
    malformed_token = "not.a.jwt.token"
    
    with patch('app.crud.auth.oauth2_scheme') as mock_oauth:
        mock_oauth.return_value = malformed_token
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=malformed_token, db=mock_db_session)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Invalid credentials"

@pytest.mark.asyncio
async def test_get_current_user_token_without_sub(mock_db_session):
    """Test of token without 'sub' claim"""
    payload = {"other_field": "value"}
    token_without_sub = jwt.encode(payload, "test_secret_key", algorithm="HS256")
    
    with patch('app.crud.auth.oauth2_scheme') as mock_oauth:
        mock_oauth.return_value = token_without_sub
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token_without_sub, db=mock_db_session)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Invalid credentials"

@pytest.mark.asyncio
async def test_get_current_user_none_subject(mock_db_session):
    """Test of token with 'sub' as None"""
    payload = {"sub": None}
    token_none_sub = jwt.encode(payload, "test_secret_key", algorithm="HS256")
    
    with patch('app.crud.auth.oauth2_scheme') as mock_oauth:
        mock_oauth.return_value = token_none_sub
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token_none_sub, db=mock_db_session)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Invalid credentials"

@pytest.mark.asyncio
async def test_get_current_user_nonexistent_user(mock_db_session, valid_token, mock_dependencies):
    """Test of valid token but user does not exist in DB"""
    _, mock_get_user = mock_dependencies
    
    mock_get_user.return_value = None
    
    with patch('app.crud.auth.oauth2_scheme') as mock_oauth:
        mock_oauth.return_value = valid_token
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=valid_token, db=mock_db_session)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Invalid credentials"
        mock_get_user.assert_called_once_with(mock_db_session, username="testuser")

@pytest.mark.asyncio
async def test_get_current_user_empty_token(mock_db_session):
    """Test empty token"""
    with patch('app.crud.auth.oauth2_scheme') as mock_oauth:
        mock_oauth.return_value = ""
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token="", db=mock_db_session)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Invalid credentials"

@pytest.mark.asyncio
async def test_get_current_user_none_token(mock_db_session):
    """Test with token=None"""
    with patch('app.crud.auth.oauth2_scheme') as mock_oauth:
        mock_oauth.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=None, db=mock_db_session)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Invalid credentials"

@pytest.mark.asyncio
async def test_get_current_user_different_algorithm(mock_db_session):
    """Test of token signed with a different algorithm"""
    payload = {"sub": "testuser"}

    token_different_alg = jwt.encode(payload, "test_secret_key", algorithm="HS384")
    
    with patch('app.crud.auth.oauth2_scheme') as mock_oauth:
        mock_oauth.return_value = token_different_alg
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=token_different_alg, db=mock_db_session)
        
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Invalid credentials"

@pytest.mark.asyncio
async def test_get_current_user_with_additional_claims(mock_db_session, test_user, mock_dependencies):
    """Test of token with additional claims"""
    
    payload = {
        "sub": "testuser",
        "extra_claim": "extra_value",
        "aud": "audience",
        "iss": "issuer"
    }
    token_with_extra_claims = jwt.encode(payload, "test_secret_key", algorithm="HS256")
        
    with patch('app.crud.auth.oauth2_scheme') as mock_oauth:
        mock_oauth.return_value = token_with_extra_claims
        with pytest.raises(HTTPException):
            await get_current_user(token=token_with_extra_claims, db=mock_db_session)

@pytest.mark.asyncio
async def test_get_current_user_exception_headers(mock_db_session, invalid_token):
    """Test which checks WWW-Authenticate header in exception"""
    with patch('app.crud.auth.oauth2_scheme') as mock_oauth:
        mock_oauth.return_value = invalid_token
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(token=invalid_token, db=mock_db_session)
        
        assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}

@pytest.mark.asyncio
async def test_get_current_user_integration_with_real_jwt(mock_db_session, test_user, mock_dependencies):
    """Test of integration with real JWT encoding/decoding"""
    _, mock_get_user = mock_dependencies
    
    payload = {"sub": "testuser"}
    real_token = jwt.encode(payload, "test_secret_key", algorithm="HS256")
    
    mock_get_user.return_value = test_user
    
    with patch('app.crud.auth.oauth2_scheme') as mock_oauth:
        mock_oauth.return_value = real_token
        
        result = await get_current_user(token=real_token, db=mock_db_session)
        
        assert result == {"id": "user123", "email": "test@example.com"}

@pytest.mark.asyncio
async def test_get_current_user_database_error(mock_db_session, valid_token, mock_dependencies):
    """Test of handling database error"""
    _, mock_get_user = mock_dependencies
    
    mock_get_user.side_effect = Exception("Database connection error")
    
    with patch('app.crud.auth.oauth2_scheme') as mock_oauth:
        mock_oauth.return_value = valid_token
        
        with pytest.raises(Exception) as exc_info:
            await get_current_user(token=valid_token, db=mock_db_session)
        assert str(exc_info.value) == "Database connection error"