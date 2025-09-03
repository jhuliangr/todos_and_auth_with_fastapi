from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
from app.lib.utils import generate_uuid

class ToDo(Base):
    __tablename__ = "todos"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    state = Column(String(20), default="pendiente") 
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    user = relationship("User", back_populates="todos")