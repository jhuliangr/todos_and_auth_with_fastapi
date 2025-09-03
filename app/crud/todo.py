from sqlalchemy.orm import Session
from app.models.todo import ToDo
from app.schemas.todo import TodoCreate, TodoUpdate
from sqlalchemy import func

def get_todos_by_user(db: Session, user_id: str, skip: int = 0, limit: int = 100):
    return db.query(ToDo).filter(ToDo.user_id == user_id).offset(skip).limit(limit).all()

def get_todo_by_id(db: Session, todo_id: str):
    return db.query(ToDo).filter(ToDo.id == todo_id).first()

def create_user_todo(db: Session, todo: TodoCreate, user_id: str):
    db_todo = ToDo(**todo.dict(), user_id=user_id)
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo

def update_todo(db: Session, todo_id: str, todo_update: TodoUpdate):
    db_todo = get_todo_by_id(db, todo_id)
    if db_todo:
        update_data = todo_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_todo, field, value)
        db.commit()
        db.refresh(db_todo)
    return db_todo

def delete_todo(db: Session, todo_id: str):
    db_todo = get_todo_by_id(db, todo_id)
    if db_todo:
        db.delete(db_todo)
        db.commit()
    return db_todo

def get_todo_count_by_state(db: Session, user_id: str):
    result = db.query(ToDo.state, func.count(ToDo.id)).filter(
        ToDo.user_id == user_id
    ).group_by(ToDo.state).all()
    return dict(result)