import asyncio
import logging
from bot.loader import load_bot
from bot.middlewares.throttle import ThrottlingMiddleware
from bot.middlewares.user import UserMiddleware

from bot.handlers import admin, commands
from bot.services.monitor import ChannelMonitor
from core.telethon_client import TelethonClient
from db.service import DatabaseService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)


async def main():
    bot, dp = load_bot()
    db = DatabaseService()
    await db.init()

    telethon = TelethonClient()
    await telethon.start()

    # Установка зависимостей
    dp["db"] = db
    dp["telethon"] = telethon

    monitor = ChannelMonitor(db, telethon)
    monitor_task = asyncio.create_task(monitor.start())

    # Регистрация middleware
    user_middleware = UserMiddleware()
    throttle_middleware = ThrottlingMiddleware()

    dp.message.middleware.register(user_middleware)
    dp.message.middleware.register(throttle_middleware)

    # Регистрация обработчиков
    dp.include_router(commands.router)
    dp.include_router(admin.router)

    try:
        await dp.start_polling(bot)
    finally:
        await monitor.stop()
        await telethon.stop()
        await db.close()
        monitor_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())