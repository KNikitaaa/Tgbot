import logging
from telethon import TelegramClient
from telethon.sessions import StringSession
from core.config import settings
from core.exceptions import TelethonError

logger = logging.getLogger(__name__)


class TelethonClient:
    def __init__(self):
        self.client = None

    async def start(self):
        """Initialize Telethon client with session validation"""
        try:
            session_string = str(settings.TELETHON_SESSION_STRING).strip()

            if not session_string or len(session_string) < 10:
                raise ValueError("Invalid session string length")

            self.client = TelegramClient(
                StringSession(session_string),
                int(settings.TELETHON_API_ID),
                str(settings.TELETHON_API_HASH)
            )

            await self.client.start()
            logger.info("Telethon client started successfully")

        except Exception as e:
            logger.error(f"Telethon startup failed: {str(e)}")
            raise TelethonError(f"Telethon initialization error: {str(e)}")

    async def stop(self):
        """Disconnect Telethon client"""
        if self.client:
            try:
                await self.client.disconnect()
                logger.info("Telethon client stopped")
            except Exception as e:
                logger.error(f"Error stopping Telethon: {str(e)}")
    async def get_messages(self, channel_id: int, limit: int = 50):
        """Get messages from channel"""
        try:
            return await self.client.get_messages(channel_id, limit=limit)
        except Exception as e:
            logger.error(f"Error getting messages from {channel_id}: {e}")
            return []