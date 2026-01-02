from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from uuid import uuid4
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class UserBase(BaseModel):
    email: EmailStr
    is_active: bool = True
    is_verified: bool = False
    roles: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(from_attributes=True)
    mfa_enabled: bool = False

class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=12)

class UserRead(UserBase):
    """Schema for returning user data (sanitized)."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.now(timezone.utc))

class UserInDB(UserRead):
    """Internal schema that includes the sensitive hash."""
    hashed_password: str
    mfa_secret: Optional[str] = None