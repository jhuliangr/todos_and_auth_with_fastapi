from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal

class TodoBase(BaseModel):
    title: str
    description: Optional[str] = None
    state: Literal[
        "pendiente",
        "completado" 
    ] = "pendiente"

class TodoCreate(TodoBase):
    pass

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    state: Optional[str] = None

class Todo(TodoBase):
    id: str
    created_at: datetime
    user_id: str
    class Config:
        from_attributes = True