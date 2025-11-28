"""FastAPI 应用主入口"""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from typing import List

from .database import get_db, init_db
from .models import User, UserRole
from .schemas import (
    UserLogin,
    UserCreate,
    UserResponse,
    Token,
    TicketCreate,
    TicketResponse,
    TicketUpdate,
    EmployeeStatusUpdate,
)
from .auth import (
    verify_password,
    create_access_token,
    get_current_user,
    get_current_employer,
)
from .config import settings
from . import crud


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    await init_db()
    yield
    # 关闭时的清理工作（如果需要）


app = FastAPI(
    title=settings.app_name,
    description="Employee expense tracking system for Contoso Ltd",
    version=settings.app_version,
    lifespan=lifespan,
    debug=settings.debug,
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录（如果存在）
static_dir = Path("static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")
else:
    # 本地开发环境，尝试使用 frontend 目录
    frontend_dir = Path(__file__).parent.parent.parent / "frontend"
    if frontend_dir.exists():
        app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "version": settings.app_version}


@app.post("/api/auth/login", response_model=Token)
async def login(user_login: UserLogin, db: AsyncSession = Depends(get_db)):
    """用户登录"""
    user = await crud.get_user_by_email(db, user_login.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not registered. Please register first.",
        )

    if not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Account is suspended"
        )

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer", "user": user}


@app.post(
    "/api/auth/register", response_model=Token, status_code=status.HTTP_201_CREATED
)
async def register(user_create: UserCreate, db: AsyncSession = Depends(get_db)):
    """用户注册"""
    existing_user = await crud.get_user_by_email(db, user_create.email)

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    user = await crud.create_user(db, user_create)

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer", "user": user}


@app.get("/api/auth/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user


@app.post(
    "/api/tickets", response_model=TicketResponse, status_code=status.HTTP_201_CREATED
)
async def create_ticket(
    ticket: TicketCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建报销票据（员工）"""
    return await crud.create_ticket(db, ticket, current_user.id)


@app.get("/api/tickets", response_model=List[TicketResponse])
async def get_tickets(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """获取票据列表
    - 员工：仅返回自己的票据
    - 雇主：返回所有票据
    """
    if current_user.role == UserRole.EMPLOYER:
        return await crud.get_all_tickets(db)
    else:
        return await crud.get_user_tickets(db, current_user.id)


@app.patch("/api/tickets/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: int,
    ticket_update: TicketUpdate,
    current_user: User = Depends(get_current_employer),
    db: AsyncSession = Depends(get_db),
):
    """更新票据状态（审批/驳回，仅雇主）"""
    ticket = await crud.update_ticket_status(db, ticket_id, ticket_update.status)

    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found"
        )

    return ticket


@app.get("/api/employees", response_model=List[UserResponse])
async def get_employees(
    current_user: User = Depends(get_current_employer),
    db: AsyncSession = Depends(get_db),
):
    """获取所有员工列表（仅雇主）"""
    return await crud.get_all_users(db)


@app.patch("/api/employees/{user_id}", response_model=UserResponse)
async def update_employee_status(
    user_id: int,
    status_update: EmployeeStatusUpdate,
    current_user: User = Depends(get_current_employer),
    db: AsyncSession = Depends(get_db),
):
    """更新员工激活状态（暂停/激活，仅雇主）"""
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify your own status",
        )

    user = await crud.update_user_status(db, user_id, status_update.is_active)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return user


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
