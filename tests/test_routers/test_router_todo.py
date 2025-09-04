import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from app.crud.auth import get_current_user

from app.models.todo import ToDo
from app.schemas.todo import TodoCreate, TodoUpdate


@pytest.mark.asyncio
async def test_read_todos_success(mock_db_session, current_user, test_todo):
    """Test for successfully retrieving all todos"""
    from app.routers.todo import read_todos
    
    with patch('app.routers.todo.get_todos_by_user', AsyncMock(return_value=[test_todo])):
        
        result = await read_todos(skip=0, limit=10, db=mock_db_session, current_user=current_user)
        
        assert len(result) == 1
        assert result[0].id == "todo123"
        assert result[0].user_id == current_user["id"]
        
        from app.routers.todo import get_todos_by_user
        get_todos_by_user.assert_called_once_with(mock_db_session, user_id="user123", skip=0, limit=10)

@pytest.mark.asyncio
async def test_read_todos_empty(mock_db_session, current_user):
    """Test for retrieving todos when none exist"""
    from app.routers.todo import read_todos
    
    with patch('app.routers.todo.get_todos_by_user', AsyncMock(return_value=[])):
        
        result = await read_todos(db=mock_db_session, current_user=current_user)
        
        assert len(result) == 0
        assert result == []

@pytest.mark.asyncio
async def test_read_todos_pagination(mock_db_session, current_user, test_todo):
    """Test for pagination parameters in retrieving todos"""
    from app.routers.todo import read_todos
    
    with patch('app.routers.todo.get_todos_by_user', AsyncMock(return_value=[test_todo])):
        
        result = await read_todos(skip=5, limit=20, db=mock_db_session, current_user=current_user)
        
        from app.routers.todo import get_todos_by_user
        get_todos_by_user.assert_called_once_with(mock_db_session, user_id="user123", skip=5, limit=20)

@pytest.mark.asyncio
async def test_create_todo_success(mock_db_session, current_user, sample_todo_data, test_todo):
    """Test for successfully creating a new todo"""
    from app.routers.todo import create_todo
    
    todo_create = TodoCreate(**sample_todo_data)
    
    with patch('app.routers.todo.create_user_todo', AsyncMock(return_value=test_todo)):
        
        result = await create_todo(todo=todo_create, db=mock_db_session, current_user=current_user)
        
        assert result.id == "todo123"
        assert result.user_id == current_user["id"]
        
        from app.routers.todo import create_user_todo
        create_user_todo.assert_called_once_with(mock_db_session, todo_create, "user123")

@pytest.mark.asyncio
async def test_create_todo_minimal_data(mock_db_session, current_user):
    """Test for creating a todo with minimal required data"""
    from app.routers.todo import create_todo
    
    minimal_data = TodoCreate(title="Minimal Todo")
    created_todo = ToDo(
        id="todo_min",
        title="Minimal Todo",
        user_id=current_user["id"]
    )
    
    with patch('app.routers.todo.create_user_todo', AsyncMock(return_value=created_todo)):
        
        result = await create_todo(todo=minimal_data, db=mock_db_session, current_user=current_user)
        
        assert result.title == "Minimal Todo"
        assert result.description is None

@pytest.mark.asyncio
async def test_read_todo_success(mock_db_session, current_user, test_todo):
    """Test for successfully retrieving a specific todo"""
    from app.routers.todo import read_todo
    
    with patch('app.routers.todo.get_todo_by_id', AsyncMock(return_value=test_todo)):
        
        result = await read_todo(todo_id="todo123", db=mock_db_session, current_user=current_user)
        
        assert result.id == "todo123"
        assert result.user_id == current_user["id"]
        
        from app.routers.todo import get_todo_by_id
        get_todo_by_id.assert_called_once_with(mock_db_session, "todo123")

@pytest.mark.asyncio
async def test_read_todo_not_found(mock_db_session, current_user):
    """Test for retrieving a non-existent todo"""
    from app.routers.todo import read_todo
    
    with patch('app.routers.todo.get_todo_by_id', AsyncMock(return_value=None)):
        
        with pytest.raises(HTTPException) as exc_info:
            await read_todo(todo_id="nonexistent", db=mock_db_session, current_user=current_user)
        
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Todo not found"

@pytest.mark.asyncio
async def test_read_todo_other_user(mock_db_session, current_user, other_user_todo):
    """Test for retrieving a todo belonging to another user"""
    from app.routers.todo import read_todo
    
    with patch('app.routers.todo.get_todo_by_id', AsyncMock(return_value=other_user_todo)):
        
        with pytest.raises(HTTPException) as exc_info:
            await read_todo(todo_id="todo456", db=mock_db_session, current_user=current_user)
        
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Todo not found"

@pytest.mark.asyncio
async def test_update_todo_item_success(mock_db_session, current_user, test_todo, sample_todo_update):
    """Test for successfully updating a todo"""
    from app.routers.todo import update_todo_item
    
    todo_update = TodoUpdate(**sample_todo_update)
    updated_todo = ToDo(
        id="todo123",
        title="Updated Todo",
        description="Test Description",
        state="completado",
        user_id=current_user["id"]
    )
    
    with patch('app.routers.todo.get_todo_by_id', AsyncMock(return_value=test_todo)), \
         patch('app.routers.todo.update_todo', AsyncMock(return_value=updated_todo)):
        
        result = await update_todo_item(
            todo_id="todo123", 
            todo_update=todo_update, 
            db=mock_db_session, 
            current_user=current_user
        )
        
        assert result.title == "Updated Todo"
        assert result.state == "completado"
        
        from app.routers.todo import update_todo
        update_todo.assert_called_once_with(mock_db_session, "todo123", todo_update)

@pytest.mark.asyncio
async def test_update_todo_item_not_found(mock_db_session, current_user, sample_todo_update):
    """Test for updating a non-existent todo"""
    from app.routers.todo import update_todo_item
    
    todo_update = TodoUpdate(**sample_todo_update)
    
    with patch('app.routers.todo.get_todo_by_id', AsyncMock(return_value=None)):
        
        with pytest.raises(HTTPException) as exc_info:
            await update_todo_item(
                todo_id="nonexistent", 
                todo_update=todo_update, 
                db=mock_db_session, 
                current_user=current_user
            )
        
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Todo not found"

@pytest.mark.asyncio
async def test_update_todo_item_other_user(mock_db_session, current_user, other_user_todo, sample_todo_update):
    """Test for updating a todo belonging to another user"""
    from app.routers.todo import update_todo_item
    
    todo_update = TodoUpdate(**sample_todo_update)
    
    with patch('app.routers.todo.get_todo_by_id', AsyncMock(return_value=other_user_todo)):
        
        with pytest.raises(HTTPException) as exc_info:
            await update_todo_item(
                todo_id="todo456", 
                todo_update=todo_update, 
                db=mock_db_session, 
                current_user=current_user
            )
        
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Todo not found"

@pytest.mark.asyncio
async def test_update_todo_item_partial(mock_db_session, current_user, test_todo):
    """Test for partially updating a todo (only state)"""
    from app.routers.todo import update_todo_item
    
    partial_update = TodoUpdate(state="en_progreso")
    updated_todo = ToDo(
        id="todo123",
        title="Test Todo",  
        description="Test Description",
        state="en_progreso", 
        user_id=current_user["id"]
    )
    
    with patch('app.routers.todo.get_todo_by_id', AsyncMock(return_value=test_todo)), \
         patch('app.routers.todo.update_todo', AsyncMock(return_value=updated_todo)):
        
        result = await update_todo_item(
            todo_id="todo123", 
            todo_update=partial_update, 
            db=mock_db_session, 
            current_user=current_user
        )
        
        assert result.state == "en_progreso"
        assert result.title == "Test Todo" 

@pytest.mark.asyncio
async def test_delete_todo_item_success(mock_db_session, current_user, test_todo):
    """Test for successfully deleting a todo"""
    from app.routers.todo import delete_todo_item
    
    with patch('app.routers.todo.get_todo_by_id', AsyncMock(return_value=test_todo)), \
         patch('app.routers.todo.delete_todo', AsyncMock(return_value=test_todo)):
        
        result = await delete_todo_item(
            todo_id="todo123", 
            db=mock_db_session, 
            current_user=current_user
        )
        
        assert result == {"message": "Todo deleted successfully"}
        
        from app.routers.todo import delete_todo
        delete_todo.assert_called_once_with(mock_db_session, "todo123")

@pytest.mark.asyncio
async def test_delete_todo_item_not_found(mock_db_session, current_user):
    """Test for deleting a non-existent todo"""
    from app.routers.todo import delete_todo_item
    
    with patch('app.routers.todo.get_todo_by_id', AsyncMock(return_value=None)):
        
        with pytest.raises(HTTPException) as exc_info:
            await delete_todo_item(
                todo_id="nonexistent", 
                db=mock_db_session, 
                current_user=current_user
            )
        
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Todo not found"

@pytest.mark.asyncio
async def test_delete_todo_item_other_user(mock_db_session, current_user, other_user_todo):
    """Test for deleting a todo belonging to another user"""
    from app.routers.todo import delete_todo_item
    
    with patch('app.routers.todo.get_todo_by_id', AsyncMock(return_value=other_user_todo)):
        
        with pytest.raises(HTTPException) as exc_info:
            await delete_todo_item(
                todo_id="todo456", 
                db=mock_db_session, 
                current_user=current_user
            )
        
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail == "Todo not found"

async def mock_get_current_user():
    return {"id": "user123", "email": "test@example.com"}


@pytest.fixture
def test_client():
    """Client for testing the FastAPI app"""
    from main import app
    app.dependency_overrides[get_current_user] = mock_get_current_user
    return TestClient(app)

@pytest.mark.asyncio
async def test_integration_todo_crud(test_client, current_user):
    """Test of the full CRUD flow for todos"""
    
    mock_todo_obj = MagicMock()
    mock_todo_obj.id = "todo123"
    mock_todo_obj.title = "Test Todo"
    mock_todo_obj.description = "Test description"
    mock_todo_obj.state = "pendiente"
    mock_todo_obj.user_id = current_user["id"]
    mock_todo_obj.created_at = "2025-09-04T17:26:31.937468Z"
    expected_todo_dict = {
        "id": "todo123",
        "title": "Test Todo",
        "description": "Test description",
        "state": "pendiente",
        "user_id": current_user["id"],
        "created_at": "2025-09-04T17:26:31.937468Z"
    }

    mock_todo_list = [mock_todo_obj]

    with patch('app.routers.todo.get_current_user', AsyncMock(return_value=current_user)), \
         patch('app.routers.todo.get_todos_by_user', AsyncMock(return_value=mock_todo_list)), \
         patch('app.routers.todo.create_user_todo', AsyncMock(return_value=mock_todo_obj)), \
         patch('app.routers.todo.get_todo_by_id', AsyncMock(return_value=mock_todo_obj)), \
         patch('app.routers.todo.update_todo', AsyncMock(return_value=mock_todo_obj)), \
         patch('app.routers.todo.delete_todo', AsyncMock(return_value=mock_todo_obj)):

        response = test_client.get("/api/v1/tasks/", headers={"Authorization": "Bearer mock_token"})
        assert response.status_code == 200
        assert response.json() == [expected_todo_dict]

        todo_data = {"title": "Integration Todo", "description": "Test integration"}
        create_response = test_client.post(
            "/api/v1/tasks/",
            json=todo_data,
            headers={"Authorization": "Bearer mock_token"}
        )
        assert create_response.status_code == 201
        assert create_response.json() == expected_todo_dict

        get_response = test_client.get(
            f"/api/v1/tasks/{mock_todo_obj['id']}",
            headers={"Authorization": "Bearer mock_token"}
        )
        assert get_response.status_code == 200
        assert get_response.json() == expected_todo_dict

        update_data = {"title": "Updated Todo", "description": "Updated description", "state": "completado"}
        update_response = test_client.put(
            f"/api/v1/tasks/{mock_todo_obj['id']}",
            json=update_data,
            headers={"Authorization": "Bearer mock_token"}
        )
        assert update_response.status_code == 200
        assert update_response.json() == expected_todo_dict

        delete_response = test_client.delete(
            f"/api/v1/tasks/{mock_todo_obj['id']}",
            headers={"Authorization": "Bearer mock_token"}
        )
        assert delete_response.status_code == 200
        assert delete_response.json() == {"message": "Todo deleted successfully"}

