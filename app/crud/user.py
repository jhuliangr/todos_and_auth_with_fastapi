from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
import bcrypt


async def get_user_by_username(db: AsyncSession, username: str):
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    return result.scalars().first()

async def get_user_by_email(db: AsyncSession, email: str):
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    return result.scalars().first()

async def create_user(db: AsyncSession, user: UserCreate):
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password.decode('utf-8')
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def update_user(db: AsyncSession, user_email: str, user_update: UserUpdate):
    db_user = await get_user_by_email(db, user_email)
    hashed_password = bcrypt.hashpw(user_update.password.encode('utf-8'), bcrypt.gensalt())
    if db_user:
        update_data = user_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "password":
                setattr(db_user, "hashed_password", hashed_password.decode('utf-8'))
            else:
                setattr(db_user, field, value)
        await db.commit()
        await db.refresh(db_user)
    return db_user

async def delete_user(db: AsyncSession, user_email: str):
    db_user = await get_user_by_email(db, user_email)
    if db_user:
        await db.delete(db_user)
        await db.commit()
    return db_user

async def authenticate_user(db: AsyncSession, username: str, password: str):
    user = await get_user_by_username(db, username)
    if not user:
        return False
    if not bcrypt.checkpw(password.encode('utf-8'), user.hashed_password.encode('utf-8')):
        return False
    return user