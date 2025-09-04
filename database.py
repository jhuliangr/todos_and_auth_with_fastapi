
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from config import get_settings

settings = get_settings()

engine = create_async_engine(settings.DATABASE_URL, pool_size=20, max_overflow=10)
AsyncSessionLocal  = sessionmaker(class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

async  def get_db():
    async with AsyncSessionLocal() as session:
        yield session