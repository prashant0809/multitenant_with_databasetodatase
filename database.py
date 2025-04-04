from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# my personal database url for configuration
MASTER_DATABASE_URL = "postgresql+asyncpg://postgres:admin@127.0.0.1:5433/master_db"
master_engine = create_async_engine(MASTER_DATABASE_URL, echo=True)
MasterSessionLocal = sessionmaker(bind=master_engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()

# database connection dep..
async def get_db():
    async with MasterSessionLocal() as session:
        yield session
