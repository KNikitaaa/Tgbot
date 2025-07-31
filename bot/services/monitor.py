import asyncio
import logging
import re
from datetime import datetime, timedelta
from telethon.tl.types import Message
from db.service import DatabaseService
from core.telethon_client import TelethonClient
from core.config import settings

logger = logging.getLogger(__name__)


class ChannelMonitor:
    def __init__(self, db: DatabaseService, telethon: TelethonClient):
        self.db = db
        self.telethon = telethon
        self.is_running = False
        self.gift_pattern = re.compile(
            r"(подаро?к|gift).*?(\d{1,6})\s?(р|руб|₽)",
            re.IGNORECASE
        )

    async def start(self):
        """Main monitoring loop"""
        self.is_running = True
        logger.info(f"Starting monitoring for {len(settings.TARGET_CHANNELS)} channels")

        while self.is_running:
            try:
                await self._check_channels()
                await asyncio.sleep(settings.CHECK_INTERVAL)
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(60)

    async def stop(self):
        """Stop monitoring gracefully"""
        self.is_running = False
        logger.info("Monitoring stopped")

    async def _check_channels(self):
        """Check all target channels for new gifts"""
        for channel_id in settings.TARGET_CHANNELS:
            await self._process_channel(channel_id)

    async def _process_channel(self, channel_id: int):
        """Process a single channel"""
        try:
            messages = await self.telethon.get_messages(channel_id, limit=50)
            for msg in messages:
                if self._is_gift_message(msg):
                    await self._save_gift(msg)
        except Exception as e:
            logger.error(f"Error processing channel {channel_id}: {e}")

    def _is_gift_message(self, msg: Message) -> bool:
        """Check if message contains a gift"""
        if not isinstance(msg, Message) or not msg.text:
            return False

        is_recent = datetime.now() - msg.date < timedelta(hours=24)
        has_gift = any(word in msg.text.lower() for word in ["подарок", "gift"])
        has_price = self.gift_pattern.search(msg.text)

        return is_recent and has_gift and has_price

    async def _save_gift(self, msg: Message):
        """Save gift to database"""
        price_match = self.gift_pattern.search(msg.text)
        price = float(price_match.group(2))

        if price > settings.MAX_GIFT_PRICE:
            return

        gift_data = {
            'gift_id': f"{msg.chat_id}_{msg.id}",
            'name': self._extract_gift_name(msg.text),
            'price': price,
            'channel_id': msg.chat_id,
            'message_id': msg.id
        }

        await self.db.save_gift(gift_data)
        logger.info(f"New gift found: {gift_data['name']} - {price} руб.")

    def _extract_gift_name(self, text: str) -> str:
        """Extract gift name from message text"""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return next(
            (line for line in lines
             if any(word in line.lower() for word in ["подарок", "gift"])),
            "Неизвестный подарок"
        )[:100]  # Limit name length