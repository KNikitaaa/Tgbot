import asyncio
import logging
from datetime import datetime
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
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


async def check_updates(bot: Bot, db: DatabaseService):
    """Проверка новых подарков и отправка уведомлений"""
    try:
        users = await db.get_users_for_notification()

        for user_settings in users:
            last_check = user_settings.last_check or datetime.min
            if (datetime.now() - last_check).total_seconds() >= user_settings.update_frequency * 60:
                new_gifts = await db.get_recent_gifts(since=last_check)

                if new_gifts:
                    await bot.send_message(
                        user_settings.user_id,
                        "🎁 Новые подарки!\n" + "\n".join(
                            f"• {g.name} - {g.price} руб." for g in new_gifts[:5]
                        ),
                        reply_markup=commands.main_menu()
                    )

                # Обновляем время последней проверки
                async with await db._get_session() as session:
                    user_settings.last_check = datetime.now()
                    await session.commit()
    except Exception as e:
        logging.error(f"Ошибка в check_updates: {e}")


async def on_startup(bot: Bot, db: DatabaseService):
    """Запуск фоновых задач при старте"""
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_updates,
        'interval',
        minutes=1,
        args=(bot, db)
    )
    scheduler.start()


async def main():
    bot, dp = load_bot()
    db = DatabaseService()
    await db.init()

    telethon = TelethonClient()
    await telethon.start()

    dp["db"] = db
    dp["telethon"] = telethon

    monitor = ChannelMonitor(db, telethon)
    monitor_task = asyncio.create_task(monitor.start())
    await on_startup(bot, db)

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