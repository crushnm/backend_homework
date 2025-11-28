"""数据库初始化脚本"""
import asyncio
import sys
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import init_db


async def main():
    """初始化数据库表"""
    print("正在初始化数据库...")
    try:
        await init_db()
        print("✓ 数据库初始化成功！")
    except Exception as e:
        print(f"✗ 数据库初始化失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
