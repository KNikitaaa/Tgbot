from aiogram import Router, types
from aiogram.filters import Command
from core.config import settings
from bot.keyboards.admin import admin_panel, monitoring_settings

router = Router()


@router.message(Command("admin"))
async def admin_cmd(message: types.Message):
    if message.from_user.id not in settings.ADMIN_IDS:
        return await message.answer("⛔ Доступ запрещен")

    await message.answer("Админ-панель:", reply_markup=admin_panel())


@router.callback_query(lambda c: c.data == "admin_settings")
async def admin_settings(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "Настройки мониторинга:",
        reply_markup=monitoring_settings()
    )
    await callback.answer()