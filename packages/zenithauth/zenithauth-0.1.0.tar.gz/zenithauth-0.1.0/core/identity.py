from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class UserBase(BaseModel):
    """Base schema for User data."""
    email: EmailStr
    is_active: bool = True
    is_verified: bool = False
    roles: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(from_attributes=True)

class UserCreate(UserBase):
    """Schema for creating a new user (Registration)."""
    password: str = Field(..., min_length=12, description="Password must be at least 12 characters")

class UserRead(UserBase):
    """Schema for reading user data (sent back to clients)."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserInDB(UserRead):
    """Internal schema that includes the hashed password."""
    hashed_password: str