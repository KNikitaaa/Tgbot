from typing import Union
import re
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from core.config import settings
from bot.keyboards.admin import admin_panel, monitoring_settings
from db.service import DatabaseService, logger

router = Router()

class AdminStates(StatesGroup):
    WAITING_FOR_PRICE_LIMIT = State()
    WAITING_FOR_CHANNEL_ADD = State()
    WAITING_FOR_CHANNEL_REMOVE = State()

def cancel_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back")]
        ]
    )


@router.message(Command("admin"))
async def admin_cmd(message: types.Message):
    if message.from_user.id not in settings.ADMIN_IDS:
        return await message.answer("⛔ Доступ запрещен")
    await message.answer("Админ-панель:", reply_markup=admin_panel())


@router.callback_query(F.data == "admin_stats")
async def show_stats(callback: types.CallbackQuery, db: DatabaseService):
    try:
        stats = await db.get_stats()
        await callback.message.edit_text(
            f"📊 Статистика:\n\n"
            f"• Всего подарков: {stats['total_gifts']}\n"
            f"• Средняя цена: {stats['avg_price']} руб.\n"
            f"• Каналов отслеживается: {stats['tracked_channels']}",
            reply_markup=admin_panel()
        )
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        await callback.message.edit_text("⚠️ Ошибка при получении статистики")
    finally:
        await callback.answer()


@router.callback_query(F.data == "admin_settings")
async def admin_settings(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "Настройки мониторинга:",
        reply_markup=monitoring_settings()
    )
    await callback.answer()


@router.callback_query(F.data == "edit_channels")
async def edit_channels(callback: types.CallbackQuery, db: DatabaseService):
    try:
        channels = await db.get_channels()
        channels_text = "\n".join(f"• {ch}" for ch in channels) if channels else "Нет отслеживаемых каналов"

        await callback.message.edit_text(
            f"📢 Отслеживаемые каналы:\n{channels_text}\n\n"
            "Выберите действие:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="➕ Добавить канал", callback_data="add_channel")],
                    [InlineKeyboardButton(text="➖ Удалить канал", callback_data="remove_channel")],
                    [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_settings")]
                ]
            )
        )
    except Exception as e:
        logger.error(f"Error getting channels: {e}")
        await callback.message.edit_text("⚠️ Ошибка при получении списка каналов")
    finally:
        await callback.answer()


@router.callback_query(F.data == "edit_price_limit")
async def edit_price_limit(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "💰 Введите новый лимит цены (только число, в рублях):",
        reply_markup=cancel_inline_keyboard()
    )
    await state.set_state(AdminStates.WAITING_FOR_PRICE_LIMIT)
    await callback.answer()


@router.message(AdminStates.WAITING_FOR_PRICE_LIMIT)
async def process_price_limit(message: types.Message, state: FSMContext, db: DatabaseService):
    input_text = message.text.strip()

    if not input_text:
        await message.answer("⚠️ Введите число, поле не может быть пустым")
        return

    if not re.fullmatch(r'^-?\d+([.,]\d+)?$', input_text):
        await message.answer(
            "⚠️ Некорректный формат числа. Примеры:\n"
            "• 5500\n"
            "• 5500.50\n"
            "• 5,500",
            reply_markup=cancel_inline_keyboard()
        )
        return

    normalized = input_text.replace(',', '.')

    try:
        price_limit = float(normalized)

        if price_limit <= 0:
            await message.answer("⚠️ Цена должна быть больше 0")
            return
        if price_limit > 1_000_000:
            await message.answer("⚠️ Максимальный лимит - 1 000 000 руб.")
            return

        await db.update_price_limit(price_limit)

        formatted_price = f"{price_limit:.2f}".replace('.00', '') if price_limit.is_integer() else f"{price_limit:.2f}"

        await message.answer(
            f"✅ Лимит успешно обновлён: {formatted_price} руб.",
            reply_markup=admin_panel()
        )
        await state.clear()

    except Exception as e:
        logger.error(f"Ошибка обновления лимита: {e}")
        await message.answer(
            "⚠️ Произошла ошибка при сохранении",
            reply_markup=admin_panel()
        )
        await state.clear()


@router.callback_query(F.data == "add_channel")
async def add_channel_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Введите ID канала для добавления (например, @channel или -10012345678):",
        reply_markup=cancel_inline_keyboard()
    )
    await state.set_state(AdminStates.WAITING_FOR_CHANNEL_ADD)
    await callback.answer()


@router.message(AdminStates.WAITING_FOR_CHANNEL_ADD)
async def process_add_channel(message: types.Message, state: FSMContext, db: DatabaseService):
    try:
        channel_id = message.text.strip()
        await db.add_channel(channel_id)
        await message.answer(
            f"✅ Канал {channel_id} добавлен в мониторинг",
            reply_markup=admin_panel()
        )
        await state.clear()
    except Exception as e:
        logger.error(f"Error adding channel: {e}")
        await message.answer("⚠️ Ошибка при добавлении канала")
        await state.clear()


@router.callback_query(F.data == "remove_channel")
async def remove_channel_start(callback: types.CallbackQuery, state: FSMContext, db: DatabaseService):
    try:
        channels = await db.get_channels()
        if not channels:
            await callback.message.edit_text(
                "Нет каналов для удаления",
                reply_markup=admin_panel()  # Возвращаем админ-панель
            )
            await callback.answer()
            return

        await callback.message.edit_text(
            "Введите ID канала для удаления:",
            reply_markup=cancel_inline_keyboard()
        )
        await state.set_state(AdminStates.WAITING_FOR_CHANNEL_REMOVE)
    except Exception as e:
        logger.error(f"Error getting channels: {e}")
        await callback.message.edit_text(
            "⚠️ Ошибка при получении списка каналов",
            reply_markup=admin_panel()  # Возвращаем в админ-панель при ошибке
        )
    finally:
        await callback.answer()

@router.message(AdminStates.WAITING_FOR_CHANNEL_REMOVE)
async def process_remove_channel(message: types.Message, state: FSMContext, db: DatabaseService):
    try:
        channel_id = message.text.strip()
        await db.remove_channel(channel_id)
        await message.answer(
            f"✅ Канал {channel_id} удален из мониторинга",
            reply_markup=admin_panel()
        )
        await state.clear()
    except Exception as e:
        logger.error(f"Error removing channel: {e}")
        await message.answer("⚠️ Ошибка при удалении канала")
        await state.clear()


@router.callback_query(F.data == "admin_back")
async def back_to_admin(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "Админ-панель:",
        reply_markup=admin_panel()
    )
    await callback.answer()

@router.callback_query(F.data == "cancel")
@router.message(F.text == "❌ Отмена")
async def cancel_action(message: Union[types.Message, types.CallbackQuery], state: FSMContext):
    await state.clear()
    if isinstance(message, types.CallbackQuery):
        await message.message.edit_text(
            "Действие отменено",
            reply_markup=admin_panel()
        )
        await message.answer()
    else:
        await message.answer(
            "Действие отменено",
            reply_markup=admin_panel()
        )