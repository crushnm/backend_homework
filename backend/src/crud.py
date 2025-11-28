"""数据库CRUD操作"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from .models import User, Ticket, UserRole, TicketStatus
from .schemas import UserCreate, TicketCreate, TicketUpdate
from .auth import get_password_hash


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """根据邮箱获取用户"""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user: UserCreate) -> User:
    """创建新用户"""
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        role=user.role,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def get_all_users(db: AsyncSession) -> List[User]:
    """获取所有用户（仅雇主可用）"""
    result = await db.execute(select(User))
    return result.scalars().all()


async def update_user_status(
    db: AsyncSession, user_id: int, is_active: bool
) -> Optional[User]:
    """更新用户激活状态"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user:
        user.is_active = is_active

        # 如果用户被暂停，软删除其所有票据
        if not is_active:
            tickets_result = await db.execute(
                select(Ticket).where(Ticket.user_id == user_id)
            )
            tickets = tickets_result.scalars().all()
            for ticket in tickets:
                ticket.is_deleted = True
        else:
            # 如果用户被重新激活，恢复其票据
            tickets_result = await db.execute(
                select(Ticket).where(Ticket.user_id == user_id)
            )
            tickets = tickets_result.scalars().all()
            for ticket in tickets:
                ticket.is_deleted = False

        await db.commit()
        await db.refresh(user)

    return user


async def create_ticket(db: AsyncSession, ticket: TicketCreate, user_id: int) -> Ticket:
    """创建报销票据"""
    db_ticket = Ticket(
        user_id=user_id,
        expense_date=ticket.expense_date,
        amount=ticket.amount,
        description=ticket.description,
        personnel=ticket.personnel,
        purchase_link=ticket.purchase_link,
    )
    db.add(db_ticket)
    await db.commit()
    await db.refresh(db_ticket)

    # 加载关联的用户信息
    await db.refresh(db_ticket, ["user"])
    return db_ticket


async def get_user_tickets(db: AsyncSession, user_id: int) -> List[Ticket]:
    """获取用户的所有票据（不包括软删除的）"""
    result = await db.execute(
        select(Ticket)
        .options(selectinload(Ticket.user))
        .where(Ticket.user_id == user_id, Ticket.is_deleted == False)
        .order_by(Ticket.created_at.desc())
    )
    return result.scalars().all()


async def get_all_tickets(db: AsyncSession) -> List[Ticket]:
    """获取所有票据（不包括软删除的，仅雇主可用）"""
    result = await db.execute(
        select(Ticket)
        .options(selectinload(Ticket.user))
        .where(Ticket.is_deleted == False)
        .order_by(Ticket.created_at.desc())
    )
    return result.scalars().all()


async def update_ticket_status(
    db: AsyncSession, ticket_id: int, status: TicketStatus
) -> Optional[Ticket]:
    """更新票据状态（审批/驳回）"""
    result = await db.execute(
        select(Ticket)
        .options(selectinload(Ticket.user))
        .where(Ticket.id == ticket_id, Ticket.is_deleted == False)
    )
    ticket = result.scalar_one_or_none()

    if ticket:
        ticket.status = status
        await db.commit()
        await db.refresh(ticket)

    return ticket
