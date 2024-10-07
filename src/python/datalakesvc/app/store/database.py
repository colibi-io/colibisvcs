import os

# from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator

# from .models import Base  # Import your Base

# Load environment variables from .env file
# load_dotenv()

# Create the async engine
engine = create_async_engine(os.getenv("DB_ADDR"), echo=True)


# Create a configured "Session" class
async_session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# Dependency to get the session
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
