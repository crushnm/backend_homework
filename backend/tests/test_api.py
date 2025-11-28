"""集成测试 - 链式测试用户完整流程"""
import unittest
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.main import app
from src.database import Base, get_db
from src.models import UserRole, TicketStatus
from datetime import datetime

# 测试数据库URL - 使用内存 SQLite 数据库
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# 创建测试引擎
test_engine = create_async_engine(
    TEST_DATABASE_URL, echo=False, connect_args={"check_same_thread": False}
)
TestSessionLocal = async_sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db():
    """测试数据库依赖覆盖"""
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


app.dependency_overrides[get_db] = override_get_db


class TestExpenseTrackerAPI(unittest.TestCase):
    """链式集成测试"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        cls.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(cls.loop)
        cls.loop.run_until_complete(cls.async_setup())

    @classmethod
    async def async_setup(cls):
        """异步初始化数据库"""
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    @classmethod
    def tearDownClass(cls):
        """清理测试环境"""
        cls.loop.run_until_complete(cls.async_teardown())
        cls.loop.close()

    @classmethod
    async def async_teardown(cls):
        """异步清理数据库"""
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await test_engine.dispose()

    def test_01_complete_workflow(self):
        """链式测试：完整的用户工作流程"""
        self.loop.run_until_complete(self._test_complete_workflow())

    async def _test_complete_workflow(self):
        """异步测试完整工作流程"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. 注册员工账号
            employee_data = {
                "email": "employee@contoso.com",
                "password": "employee123",
                "username": "Test Employee",
                "role": UserRole.EMPLOYEE.value,
            }
            response = await client.post("/api/auth/register", json=employee_data)
            self.assertEqual(response.status_code, 201)
            employee_token = response.json()["access_token"]
            self.assertIsNotNone(employee_token)

            # 2. 注册雇主账号
            employer_data = {
                "email": "employer@contoso.com",
                "password": "employer123",
                "username": "Test Employer",
                "role": UserRole.EMPLOYER.value,
            }
            response = await client.post("/api/auth/register", json=employer_data)
            self.assertEqual(response.status_code, 201)
            employer_token = response.json()["access_token"]
            employer_id = response.json()["user"]["id"]

            # 3. 员工登录
            login_data = {"email": "employee@contoso.com", "password": "employee123"}
            response = await client.post("/api/auth/login", json=login_data)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["user"]["email"], "employee@contoso.com")

            # 4. 员工创建报销票据
            ticket_data = {
                "expense_date": datetime.utcnow().isoformat(),
                "amount": 150.50,
                "description": "Office supplies",
                "personnel": "Test Employee",
                "purchase_link": "https://example.com/order/123",
            }
            headers = {"Authorization": f"Bearer {employee_token}"}
            response = await client.post(
                "/api/tickets", json=ticket_data, headers=headers
            )
            self.assertEqual(response.status_code, 201)
            ticket_id = response.json()["id"]
            self.assertEqual(response.json()["status"], TicketStatus.PENDING.value)

            # 5. 员工查看自己的票据
            response = await client.get("/api/tickets", headers=headers)
            self.assertEqual(response.status_code, 200)
            tickets = response.json()
            self.assertEqual(len(tickets), 1)
            self.assertEqual(tickets[0]["id"], ticket_id)

            # 6. 雇主查看所有票据
            employer_headers = {"Authorization": f"Bearer {employer_token}"}
            response = await client.get("/api/tickets", headers=employer_headers)
            self.assertEqual(response.status_code, 200)
            all_tickets = response.json()
            self.assertGreaterEqual(len(all_tickets), 1)

            # 7. 雇主审批票据
            update_data = {"status": TicketStatus.APPROVED.value}
            response = await client.patch(
                f"/api/tickets/{ticket_id}", json=update_data, headers=employer_headers
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["status"], TicketStatus.APPROVED.value)

            # 8. 验证票据状态已更新
            response = await client.get("/api/tickets", headers=headers)
            self.assertEqual(response.status_code, 200)
            updated_ticket = response.json()[0]
            self.assertEqual(updated_ticket["status"], TicketStatus.APPROVED.value)

            # 9. 雇主查看员工列表
            response = await client.get("/api/employees", headers=employer_headers)
            self.assertEqual(response.status_code, 200)
            employees = response.json()
            self.assertGreaterEqual(len(employees), 2)

            # 10. 雇主暂停员工账号
            employee_id = None
            for emp in employees:
                if emp["email"] == "employee@contoso.com":
                    employee_id = emp["id"]
                    break

            self.assertIsNotNone(employee_id)
            suspend_data = {"is_active": False}
            response = await client.patch(
                f"/api/employees/{employee_id}",
                json=suspend_data,
                headers=employer_headers,
            )
            self.assertEqual(response.status_code, 200)
            self.assertFalse(response.json()["is_active"])

            # 11. 验证被暂停员工无法登录
            response = await client.post("/api/auth/login", json=login_data)
            self.assertEqual(response.status_code, 403)

            # 12. 验证被暂停员工的票据被软删除
            response = await client.get("/api/tickets", headers=employer_headers)
            self.assertEqual(response.status_code, 200)
            visible_tickets = [
                t
                for t in response.json()
                if t["user"]["email"] == "employee@contoso.com"
            ]
            self.assertEqual(len(visible_tickets), 0)

            # 13. 雇主重新激活员工
            activate_data = {"is_active": True}
            response = await client.patch(
                f"/api/employees/{employee_id}",
                json=activate_data,
                headers=employer_headers,
            )
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.json()["is_active"])

            # 14. 验证员工可以重新登录
            response = await client.post("/api/auth/login", json=login_data)
            self.assertEqual(response.status_code, 200)

            # 15. 验证票据恢复可见
            response = await client.get("/api/tickets", headers=employer_headers)
            self.assertEqual(response.status_code, 200)
            visible_tickets = [
                t
                for t in response.json()
                if t["user"]["email"] == "employee@contoso.com"
            ]
            self.assertGreater(len(visible_tickets), 0)

    def test_02_authorization(self):
        """测试权限控制"""
        self.loop.run_until_complete(self._test_authorization())

    async def _test_authorization(self):
        """异步测试权限"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 注册员工
            employee_data = {
                "email": "employee2@contoso.com",
                "password": "password123",
                "username": "Employee 2",
                "role": UserRole.EMPLOYEE.value,
            }
            response = await client.post("/api/auth/register", json=employee_data)
            employee_token = response.json()["access_token"]
            headers = {"Authorization": f"Bearer {employee_token}"}

            # 员工尝试访问员工列表（应该失败）
            response = await client.get("/api/employees", headers=headers)
            self.assertEqual(response.status_code, 403)

            # 员工尝试审批票据（应该失败）
            update_data = {"status": TicketStatus.APPROVED.value}
            response = await client.patch(
                "/api/tickets/1", json=update_data, headers=headers
            )
            self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
