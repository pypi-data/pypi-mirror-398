from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.core.config import DATABASE_URL_SYNC, DATABASE_URL_ASYNC

# -------- SYNC DB --------
engine = create_engine(DATABASE_URL_SYNC, echo=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)

def get_db_sync():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------- ASYNC DB --------
async_engine = create_async_engine(DATABASE_URL_ASYNC, echo=True)
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db_async():
    async with AsyncSessionLocal() as session:
        yield session