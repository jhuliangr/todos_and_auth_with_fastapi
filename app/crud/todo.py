from sqlalchemy.ext.asyncio import AsyncSession
from app.models.todo import ToDo
from app.schemas.todo import TodoCreate, TodoUpdate
from sqlalchemy import func, select

async def get_todos_by_user(db: AsyncSession, user_id: str, skip: int = 0, limit: int = 100):
    stmt = select(ToDo).where(ToDo.user_id == user_id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

async def get_todo_by_id(db: AsyncSession, todo_id: str):
    stmt = select(ToDo).where(ToDo.id == todo_id)
    result = await db.execute(stmt)
    return result.scalars().first()

async def create_user_todo(db: AsyncSession, todo: TodoCreate, user_id: str):
    db_todo = ToDo(**todo.model_dump(), user_id=user_id)
    db.add(db_todo)
    await db.commit()
    await db.refresh(db_todo)
    return db_todo

async def update_todo(db: AsyncSession, todo_id: str, todo_update: TodoUpdate):
    db_todo = await get_todo_by_id(db, todo_id)
    if db_todo:
        update_data = todo_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_todo, field, value)
        await db.commit()
        await db.refresh(db_todo)
    return db_todo

async def delete_todo(db: AsyncSession, todo_id: str):
    db_todo = await get_todo_by_id(db, todo_id)
    if db_todo:
        await db.delete(db_todo)
        await db.commit()
    return db_todo