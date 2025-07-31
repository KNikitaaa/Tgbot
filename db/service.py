import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from core.config import settings
from core.exceptions import DatabaseError
from db.models.base import Base
from db.models.gift import Gift

logger = logging.getLogger(__name__)


class DatabaseService:
    def __init__(self):
        self.engine = None
        self.session_factory = None

    async def init(self):
        """Initialize database connection"""
        try:
            # Преобразуем PostgresDsn в строку явно
            db_url = str(settings.POSTGRES_DSN)
            self.engine = create_async_engine(db_url)

            self.session_factory = sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )

            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise DatabaseError("Could not connect to database")

    async def get_session(self) -> AsyncSession:
        return self.session_factory()

    async def save_gift(self, gift_data: dict):
        """Save new gift to database"""
        async with self.get_session() as session:
            try:
                gift = Gift(
                    gift_id=gift_data['gift_id'],
                    name=gift_data['name'],
                    price=gift_data['price'],
                    channel_id=gift_data['channel_id'],
                    message_id=gift_data['message_id']
                )
                session.add(gift)
                await session.commit()
                logger.debug(f"Gift saved: {gift_data['gift_id']}")
            except Exception as e:
                await session.rollback()
                logger.error(f"Error saving gift: {e}")
                raise DatabaseError("Failed to save gift")

    async def get_recent_gifts(self, limit: int = 10) -> list[Gift]:
        session = self.session_factory()
        try:
            result = await session.execute(
                select(Gift)
                .order_by(Gift.created_at.desc())
                .limit(limit)
            )
            return result.scalars().all()
        finally:
            await session.close()

    async def close(self):
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed")