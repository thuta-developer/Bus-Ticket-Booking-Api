# app/core/database.py
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
    AsyncEngine
)
from typing import AsyncGenerator
from app.core.config import settings

# PostgreSQL Async Connection String (SQLAlchemy 2.0 format)
# သတိပြုရန်: postgresql+asyncpg:// လို့ ပေးရပါမယ်။
DATABASE_URL = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Engine ကို Configure လုပ်ခြင်း
engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=settings.DEBUG,  # Development မှာ SQL query တွေပြရန်
    future=True,          # SQLAlchemy 2.0 style ကိုသုံးရန်
    pool_size=10,         # Connection pool size (production မှာ ချိန်ညှိရန်)
    max_overflow=20,      # Pool ပြည့်သွားရင် ထပ်ဆောင်းခွင့်ပြုမည့် connection အရေအတွက်
    pool_pre_ping=True,   # Connection မသုံးခင် ping ဆွဲပြီး အသက်ရှိမရှိစစ်ရန် (အရမ်းအရေးကြီး)
    pool_recycle=3600,    # 1 နာရီကြာတိုင်း connection အသစ်လဲရန် (PostgreSQL timeout ကိုရှောင်ရန်)
)

# Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # commit လုပ်ပြီးသား object တွေကို ပြန်မဆွဲပါနဲ့ (performance အတွက်)
    autocommit=False,
    autoflush=False,
)


# Dependency Injection အတွက် Database Session Generator
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency အနေနဲ့ သုံးပါ။
    Request တစ်ခုစီအတွက် session အသစ်ဖွင့်ပေးပြီး၊ ပြီးသွားရင် ပိတ်ပေးပါတယ်။
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Health Check အတွက် Database Connection စစ်ဆေးရန် function
async def check_db_connection() -> bool:
    """Database ဆက်သွယ်မှု အသက်ရှိမရှိ စစ်ဆေးရန်"""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
