import logging
from datetime import datetime
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func, distinct
from core.config import settings
from core.exceptions import DatabaseError
from db.models.base import Base
from db.models.gift import Gift
from db.models.settings import UserSettings

logger = logging.getLogger(__name__)


class DatabaseService:
    def __init__(self):
        self.engine = None
        self.session_factory = None

    async def init(self):
        """Initialize database connection"""
        try:
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

    async def _get_session(self) -> AsyncSession:
        """Internal method to get session"""
        if not self.session_factory:
            raise DatabaseError("Database not initialized")
        return self.session_factory()

    async def save_gift(self, gift_data: dict):
        """Save new gift to database"""
        async with await self._get_session() as session:
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

    async def get_recent_gifts(self, since: datetime = None, limit: int = 10) -> Sequence[Gift]:
        async with await self._get_session() as session:
            query = select(Gift).order_by(Gift.created_at.desc())

            if since:
                query = query.where(Gift.created_at > since)
            if limit:
                query = query.limit(limit)

            result = await session.execute(query)
            return result.scalars().all()

    async def get_stats(self) -> dict:
        """Get monitoring statistics"""
        async with await self._get_session() as session:
            try:
                total_gifts = await session.scalar(select(func.count(Gift.id)))

                avg_price = await session.scalar(select(func.avg(Gift.price)))

                channel_count = await session.scalar(
                    select(func.count(distinct(Gift.channel_id))))

                return {
                    'total_gifts': total_gifts or 0,
                    'avg_price': round(float(avg_price or 0), 2),
                    'tracked_channels': channel_count or 0
                }
            except Exception as e:
                logger.error(f"Error getting stats: {e}")
                raise DatabaseError("Failed to get statistics")

    async def get_channels(self) -> list[str]:
        """Get list of monitored channels"""
        async with await self._get_session() as session:
            try:
                result = await session.execute(
                    select(distinct(Gift.channel_id)))
                return [row[0] for row in result.all()]
            except Exception as e:
                logger.error(f"Error getting channels: {e}")
                raise DatabaseError("Failed to get channels")

    @staticmethod
    async def add_channel(channel_id: str):
        """Add new channel to monitoring"""
        logger.info(f"Channel {channel_id} added to monitoring")
        return True

    @staticmethod
    async def remove_channel(channel_id: str):
        """Remove channel from monitoring"""
        logger.info(f"Channel {channel_id} removed from monitoring")
        return True

    @staticmethod
    async def update_price_limit(new_limit: float):
        """Update price limit in settings"""
        settings.PRICE_LIMIT = new_limit
        logger.info(f"Price limit updated to {new_limit}")
        return True

    async def get_user_settings(self, user_id: int) -> UserSettings:
        async with await self._get_session() as session:
            settings = await session.get(UserSettings, user_id)
            if not settings:
                settings = UserSettings(user_id=user_id)
                session.add(settings)
                await session.commit()
            return settings

    async def toggle_notifications(self, user_id: int) -> bool:
        async with await self._get_session() as session:
            settings = await self.get_user_settings(user_id)
            settings.notifications_enabled = not settings.notifications_enabled
            await session.commit()
            return settings.notifications_enabled

    async def set_update_frequency(self, user_id: int, frequency: int) -> int:
        async with await self._get_session() as session:
            settings = await self.get_user_settings(user_id)
            settings.update_frequency = frequency
            await session.commit()
            return frequency

    async def get_users_for_notification(self):
        async with await self._get_session() as session:
            result = await session.execute(
                select(UserSettings).where(
                    UserSettings.notifications_enabled == True
                )
            )
            return result.scalars().all()

    async def close(self):
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connections closed")