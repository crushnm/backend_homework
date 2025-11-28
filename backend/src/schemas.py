"""Pydantic schemas for request/response validation"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel,EmailStr, Field, field_validator
from .models import UserRole, TicketStatus


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str
    


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    username: str
    role: UserRole


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(UserBase):
    id: int
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Token Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


# Ticket Schemas
class TicketBase(BaseModel):
    expense_date: datetime
    amount: float = Field(gt=0, description="Amount must be greater than 0")
    description: str
    personnel: str
    purchase_link: Optional[str] = None


class TicketCreate(TicketBase):
    @field_validator('expense_date')
    @classmethod
    def remove_timezone(cls, v: datetime) -> datetime:
        """移除时区信息，确保与数据库兼容"""
        if v.tzinfo is not None:
            return v.replace(tzinfo=None)
        return v


class TicketUpdate(BaseModel):
    status: TicketStatus


class TicketResponse(TicketBase):
    id: int
    user_id: int
    status: TicketStatus
    created_at: datetime
    updated_at: datetime
    user: UserResponse

    class Config:
        from_attributes = True


# Employee Management Schemas
class EmployeeStatusUpdate(BaseModel):
    is_active: bool
