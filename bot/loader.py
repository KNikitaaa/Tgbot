from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from core.config import settings
from db.service import DatabaseService
from core.telethon_client import TelethonClient
from bot.services.monitor import ChannelMonitor

def load_bot():
    """Initialize bot with new syntax for Aiogram 3.7.0+"""
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )
    dp = Dispatcher()
    return bot, dp


async def setup_services(dp):
    db = DatabaseService()
    await db.init()

    telethon = TelethonClient()
    await telethon.start()

    monitor = ChannelMonitor(db, telethon)

    return {
        'db': db,
        'telethon': telethon,
        'monitor': monitor
    }