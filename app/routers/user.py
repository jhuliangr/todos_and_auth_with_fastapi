from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from app.schemas.user import User, UserCreate, UserUpdate
from app.crud.user import (
    create_user,
    get_user_by_email,
    update_user,
    delete_user
)
from app.crud.auth import get_current_user

router = APIRouter(prefix="/user", tags=["users"])

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
def user_create(
    user: UserCreate, 
    db: Session = Depends(get_db)
):
    return create_user(db, user)

@router.get("/", response_model=User)
def read_user(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user = get_user_by_email(db, current_user["email"])
    if not user or user.id != current_user["id"]:
        raise HTTPException(status_code=400, detail="User not found or unauthorized")
    return user

@router.put("/", response_model=User)
def update_user_by_email(
    user_update: UserUpdate, 
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user = get_user_by_email(db, current_user["email"])
    if not user or user.id != current_user["id"]:
        raise HTTPException(status_code=400, detail="User not found or unauthorized")
    
    return update_user(db, current_user["email"], user_update)

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def user_delete(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user = get_user_by_email(db, current_user["email"])
    if not user or user.id != current_user["id"]:
        raise HTTPException(status_code=400, detail="User not found or unauthorized")
    
    delete_user(db, current_user["email"])
    return {"message": "User deleted successfully"}