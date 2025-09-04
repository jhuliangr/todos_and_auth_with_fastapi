import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.schemas.todo import TodoCreate

from app.crud.todo import (
    get_todos_by_user,
    get_todo_by_id,
    create_user_todo,
    update_todo,
    delete_todo
)
from app.models.todo import ToDo
from app.schemas.todo import TodoCreate, TodoUpdate


@pytest.mark.asyncio
async def test_get_todos_by_user(mock_db_session, test_todo):
    """Test for getting todos by user"""
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [test_todo]
    mock_db_session.execute.return_value = mock_result
    
    result = await get_todos_by_user(mock_db_session, "user123", skip=0, limit=10)
    
    mock_db_session.execute.assert_called_once()
    called_stmt = mock_db_session.execute.call_args[0][0]
    
    assert str(called_stmt).count("WHERE") == 1
    assert "todos.user_id = :user_id_1" in str(called_stmt)
    
    assert len(result) == 1
    assert result[0].id == "todo123"
    assert result[0].user_id == "user123"

@pytest.mark.asyncio
async def test_get_todos_by_user_empty(mock_db_session):
    """Test for getting todos by user when none exist"""
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = []
    mock_db_session.execute.return_value = mock_result
    
    result = await get_todos_by_user(mock_db_session, "user123")
    
    assert len(result) == 0
    mock_db_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_get_todos_by_user_with_pagination(mock_db_session, test_todo):
    """Test for getting todos by user with pagination"""
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [test_todo]
    mock_db_session.execute.return_value = mock_result
    
    result = await get_todos_by_user(mock_db_session, "user123", skip=5, limit=20)
    
    called_stmt = mock_db_session.execute.call_args[0][0]
    assert "LIMIT :param_1" in str(called_stmt)

@pytest.mark.asyncio
async def test_get_todo_by_id_found(mock_db_session, test_todo):
    """Test for getting a todo by ID when it exists"""
    mock_result = MagicMock()
    mock_result.scalars().first.return_value = test_todo
    mock_db_session.execute.return_value = mock_result
    
    result = await get_todo_by_id(mock_db_session, "todo123")
    
    mock_db_session.execute.assert_called_once()
    called_stmt = mock_db_session.execute.call_args[0][0]
    
    assert "todos.id = :id_1" in str(called_stmt)
    assert result.id == "todo123"
    assert result.title == "Test Todo"

@pytest.mark.asyncio
async def test_get_todo_by_id_not_found(mock_db_session):
    """Test for getting a todo by ID when it does not exist"""
    mock_result = MagicMock()
    mock_result.scalars().first.return_value = None
    mock_db_session.execute.return_value = mock_result
    
    result = await get_todo_by_id(mock_db_session, "nonexistent_id")
    
    assert result is None
    mock_db_session.execute.assert_called_once()

@pytest.mark.asyncio
async def test_create_user_todo(mock_db_session, test_todo):
    """Test for creating a todo"""
    todo_create = TodoCreate(title=test_todo.title, description=test_todo.description)
    
    mock_db_session.refresh.return_value = None
    
    result = await create_user_todo(mock_db_session, todo_create, "user123")
    
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once()
    
    added_todo = mock_db_session.add.call_args[0][0]
    assert isinstance(added_todo, ToDo)
    assert added_todo.title == "Test Todo"
    assert added_todo.user_id == "user123"
    assert added_todo.state == "pendiente"

@pytest.mark.asyncio
async def test_update_todo_found(mock_db_session, test_todo):
    """Test for updating an existing todo"""
    with patch('app.crud.todo.get_todo_by_id', AsyncMock(return_value=test_todo)):
        update_data = TodoUpdate(title="Updated Title", state="completado")
        
        result = await update_todo(mock_db_session, "todo123", update_data)
        
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(test_todo)
        
        assert result.title == "Updated Title"
        assert result.state == "completado"
        assert result.description == "Test Description" 

@pytest.mark.asyncio
async def test_update_todo_partial_data(mock_db_session, test_todo):
    """Test for updating a todo with partial data"""
    with patch('app.crud.todo.get_todo_by_id', AsyncMock(return_value=test_todo)):
        update_data = TodoUpdate(state="completado")
        
        result = await update_todo(mock_db_session, "todo123", update_data)
        
        mock_db_session.commit.assert_called_once()
        
        assert result.state == "completado"
        assert result.title == "Test Todo" 
        assert result.description == "Test Description"

@pytest.mark.asyncio
async def test_update_todo_not_found(mock_db_session):
    """Test for updating a todo that does not exist"""
    with patch('app.crud.todo.get_todo_by_id', AsyncMock(return_value=None)):
        update_data = TodoUpdate(title="Updated Title")
        
        result = await update_todo(mock_db_session, "nonexistent_id", update_data)
        
        mock_db_session.commit.assert_not_called()
        mock_db_session.refresh.assert_not_called()
        assert result is None

@pytest.mark.asyncio
async def test_update_todo_no_changes(mock_db_session, test_todo):
    """Test for updating a todo with no changes"""
    with patch('app.crud.todo.get_todo_by_id', AsyncMock(return_value=test_todo)):
        update_data = TodoUpdate()
        
        result = await update_todo(mock_db_session, "todo123", update_data)
        
        mock_db_session.commit.assert_called_once()
        assert result.title == "Test Todo"  

@pytest.mark.asyncio
async def test_delete_todo_found(mock_db_session, test_todo):
    """Test for deleting an existing todo"""
    with patch('app.crud.todo.get_todo_by_id', AsyncMock(return_value=test_todo)):
        result = await delete_todo(mock_db_session, "todo123")
        
        mock_db_session.delete.assert_called_once_with(test_todo)
        mock_db_session.commit.assert_called_once()
        
        assert result == test_todo

@pytest.mark.asyncio
async def test_delete_todo_not_found(mock_db_session):
    """Test for deleting a todo that does not exist"""
    with patch('app.crud.todo.get_todo_by_id', AsyncMock(return_value=None)):
        result = await delete_todo(mock_db_session, "nonexistent_id")
        
        mock_db_session.delete.assert_not_called()
        mock_db_session.commit.assert_not_called()
        assert result is None

@pytest.mark.asyncio
async def test_create_user_todo_exception_handling(mock_db_session, test_todo):
    """Test for exception handling during todo creation"""
    todo_create = TodoCreate(title=test_todo.title, description=test_todo.description)
    
    mock_db_session.commit.side_effect = Exception("Database error")
    
    with pytest.raises(Exception, match="Database error"):
        await create_user_todo(mock_db_session, todo_create, "user123")
    
    mock_db_session.add.assert_called_once()

@pytest.mark.asyncio
async def test_update_todo_exception_handling(mock_db_session, test_todo):
    """Test for exception handling during todo update"""
    with patch('app.crud.todo.get_todo_by_id', AsyncMock(return_value=test_todo)):
        update_data = TodoUpdate(title="Updated")
        
        mock_db_session.commit.side_effect = Exception("Update error")
        
        with pytest.raises(Exception, match="Update error"):
            await update_todo(mock_db_session, "todo123", update_data)
        
        assert test_todo.title == "Updated"

@pytest.mark.asyncio
async def test_crud_operations_with_different_states(mock_db_session, test_todo):
    """Test with different todo states"""
    states_to_test = ["pendiente", "completado"]
    
    for state in states_to_test:
        mock_db_session.reset_mock()
        mock_db_session.refresh.return_value = None
        
        todo_create = TodoCreate(title="State Test", description="Testing state", state=state)
        
        await create_user_todo(mock_db_session, todo_create, "user123")
        
        added_todo = mock_db_session.add.call_args[0][0]
        assert added_todo.state == state