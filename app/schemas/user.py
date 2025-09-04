from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: str
    created_at: datetime
    
    class Config:
        from_attributes = True
        orm_mode = True
        extra = 'forbid'

class UserUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None