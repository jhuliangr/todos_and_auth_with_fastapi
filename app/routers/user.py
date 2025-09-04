from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from app.schemas.user import User, UserCreate, UserUpdate, UserUpdateResponse
from app.crud.user import (
    create_user,
    get_user_by_email,
    update_user,
    delete_user
)
from app.crud.auth import get_current_user
from app.lib.utils import create_access_token

router = APIRouter(prefix="/user", tags=["users"])

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def user_create(
    user: UserCreate, 
    db: Session = Depends(get_db)
):
    return await create_user(db, user)

@router.get("/", response_model=User)
async def read_user(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user = await get_user_by_email(db, current_user["email"])
    if not user or user.id != current_user["id"]:
        raise HTTPException(status_code=400, detail="User not found or unauthorized")
    return user

@router.put("/", response_model=UserUpdateResponse)
async def update_user_by_email(
    user_update: UserUpdate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user = await get_user_by_email(db, current_user["email"])
    if not user or user.id != current_user["id"]:
        raise HTTPException(status_code=400, detail="User not found or unauthorized")
    
    updated_user = await update_user(db, current_user["email"], user_update)
    new_jwt = create_access_token(data={"sub": updated_user.username})
    return {"user": updated_user, "access_token": new_jwt}

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def user_delete(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user = await get_user_by_email(db, current_user["email"])
    if not user or user.id != current_user["id"]:
        raise HTTPException(status_code=400, detail="User not found or unauthorized")
    
    await delete_user(db, current_user["email"])
    return {"message": "User deleted successfully"}