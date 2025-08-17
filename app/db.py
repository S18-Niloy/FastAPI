from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, DateTime, func

DATABASE_URL = "sqlite+aiosqlite:///./ai_task.db"

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class Answer(Base):
    __tablename__ = "answers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task: Mapped[str] = mapped_column(String(50))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(DateTime, server_default=func.now())

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
