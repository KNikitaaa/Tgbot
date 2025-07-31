from aiogram import Router, types
from aiogram.filters import Command
from bot.keyboards.main import main_menu
from db.service import DatabaseService, logger

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🔍 Бот для мониторинга подарков в Telegram\n"
        "Я автоматически отслеживаю новые подарки в указанных каналах",
        reply_markup=main_menu()
    )


@router.message(Command("gifts"))
async def cmd_gifts(message: types.Message, db: DatabaseService):
    try:
        gifts = await db.get_recent_gifts(limit=5)
        if not gifts:
            return await message.answer("🎁 Новых подарков не найдено")

        response = "🎁 Последние подарки:\n\n" + "\n".join(
            f"{g.name} - {g.price} руб. (канал: {g.channel_id})"
            for g in gifts
        )
        await message.answer(response[:4000])
    except Exception as e:
        logger.error(f"Error getting gifts: {e}")
        await message.answer("⚠️ Произошла ошибка при получении подарков")