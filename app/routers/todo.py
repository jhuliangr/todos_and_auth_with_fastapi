from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from app.schemas.todo import Todo, TodoCreate, TodoUpdate
from app.crud.todo import (
    get_todos_by_user, 
    create_user_todo, 
    get_todo_by_id, 
    update_todo, 
    delete_todo,
    get_todo_count_by_state
)
from app.crud.auth import get_current_user

router = APIRouter(prefix="/task", tags=["todos"])

@router.get("/", response_model=List[Todo])
def read_todos(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    todos = get_todos_by_user(db, user_id=current_user["id"], skip=skip, limit=limit)
    return todos

@router.post("/", response_model=Todo, status_code=status.HTTP_201_CREATED)
def create_todo(
    todo: TodoCreate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return create_user_todo(db, todo, current_user["id"])

@router.get("/{todo_id}", response_model=Todo)
def read_todo(
    todo_id: str, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    todo = get_todo_by_id(db, todo_id)
    if not todo or todo.user_id != current_user["id"]:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo

@router.put("/{todo_id}", response_model=Todo)
def update_todo_item(
    todo_id: str, 
    todo_update: TodoUpdate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    todo = get_todo_by_id(db, todo_id)
    if not todo or todo.user_id != current_user["id"]:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    return update_todo(db, todo_id, todo_update)

@router.delete("/{todo_id}")
def delete_todo_item(
    todo_id: str, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    todo = get_todo_by_id(db, todo_id)
    if not todo or todo.user_id != current_user["id"]:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    delete_todo(db, todo_id)
    return {"message": "Todo deleted successfully"}

@router.get("/stats/count")
def get_todo_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    return get_todo_count_by_state(db, current_user["id"])