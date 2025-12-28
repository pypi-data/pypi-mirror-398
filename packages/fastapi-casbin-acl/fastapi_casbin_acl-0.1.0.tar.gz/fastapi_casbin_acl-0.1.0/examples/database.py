"""
数据库连接和会话管理
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlmodel import SQLModel

# 数据库 URL (使用 aiosqlite)
DATABASE_URL = "sqlite+aiosqlite:///./example.db"

# 创建异步引擎
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # 打印 SQL 语句（开发环境）
    connect_args={"check_same_thread": False},  # SQLite 需要这个参数
)

# 创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncSession:
    """
    获取数据库会话的依赖函数
    """
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    """
    初始化数据库，创建所有表
    """
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def close_db():
    """
    关闭数据库连接
    """
    await engine.dispose()

