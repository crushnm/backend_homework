"""SQLAlchemy 数据库模型"""
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Boolean,
    ForeignKey,
    Enum,
)
from sqlalchemy.orm import relationship
import enum
from .database import Base


class UserRole(str, enum.Enum):
    """用户角色枚举"""

    EMPLOYEE = "employee"
    EMPLOYER = "employer"


class TicketStatus(str, enum.Enum):
    """票据状态枚举"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class User(Base):
    """用户模型"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 关系
    tickets = relationship(
        "Ticket", back_populates="user", cascade="all, delete-orphan"
    )


class Ticket(Base):
    """报销票据模型"""

    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    expense_date = Column(DateTime, nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String, nullable=False)
    personnel = Column(String, nullable=False)  # 消费人员
    purchase_link = Column(String, nullable=True)  # 购买链接（可选）
    status = Column(Enum(TicketStatus), default=TicketStatus.PENDING, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)  # 软删除标记
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # 关系
    user = relationship("User", back_populates="tickets")
