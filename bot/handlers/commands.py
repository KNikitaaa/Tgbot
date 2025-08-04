from aiogram import Router, types, F
from aiogram.filters import Command
from bot.keyboards.main import main_menu, settings_menu, frequency_settings_menu, notification_settings_menu
from db.service import DatabaseService, logger

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "🔍 Бот для мониторинга подарков в Telegram\n"
        "Я автоматически отслеживаю новые подарки в указанных каналах\n"
        "Чтобы получить подарки введите /gifts",
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


@router.message(F.text == "🎁 Последние подарки")
async def handle_gifts_button(message: types.Message, db: DatabaseService):
    try:
        gifts = await db.get_recent_gifts(limit=5)
        if not gifts:
            return await message.answer(
                "🎁 Новых подарков не найдено",
                reply_markup=main_menu()
            )

        response = ["🎁 Последние подарки:"]
        for i, gift in enumerate(gifts, 1):
            response.append(
                f"{i}. {gift.name} - {gift.price} руб.\n"
                f"   Канал: {gift.channel_id}\n"
                f"   Дата: {gift.created_at.strftime('%d.%m.%Y %H:%M')}"
            )

        await message.answer(
            "\n".join(response)[:4000],
            reply_markup=main_menu()
        )
    except Exception as e:
        logger.error(f"Error getting gifts: {e}")
        await message.answer(
            "⚠️ Произошла ошибка при получении подарков",
            reply_markup=main_menu()
        )


@router.message(F.text == "⚙ Настройки")
async def handle_settings_button(message: types.Message):
    await message.answer(
        "⚙ Выберите действие:",
        reply_markup=settings_menu()
    )

@router.callback_query(F.data == "notification_settings")
async def handle_notification_settings(callback: types.CallbackQuery, db: DatabaseService):
    settings = await db.get_user_settings(callback.from_user.id)
    await callback.message.edit_text(
        "🔔 Настройки уведомлений:",
        reply_markup=notification_settings_menu(
            settings.notifications_enabled,
            settings.update_frequency
        )
    )
    await callback.answer()


@router.callback_query(F.data == "update_frequency")
async def handle_frequency_settings(callback: types.CallbackQuery, db: DatabaseService):
    settings = await db.get_user_settings(callback.from_user.id)
    await callback.message.edit_text(
        "📊 Выберите частоту обновления:",
        reply_markup=frequency_settings_menu(settings.update_frequency)
    )
    await callback.answer()

@router.callback_query(F.data == "settings_back")
async def back_to_settings(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "⚙ Выберите действие:",
        reply_markup=settings_menu()
    )
    await callback.answer()

@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(
        "Возврат. Выберите опцию из предложенных в клавиатуре.",
        reply_markup=main_menu()
    )
    await callback.answer()


@router.callback_query(F.data == "toggle_notifications")
async def toggle_notifications(callback: types.CallbackQuery, db: DatabaseService):
    try:

        settings = await db.get_user_settings(callback.from_user.id)

        new_status = not settings.notifications_enabled
        await db.toggle_notifications(callback.from_user.id)

        status_text = "🔔 Уведомления включены" if new_status else "🔕 Уведомления выключены"
        message_text = (
            f"{status_text}\n"
            f"Частота проверки: каждые {settings.update_frequency} мин"
        )

        new_keyboard = notification_settings_menu(new_status)

        current_text = callback.message.text or ""
        current_markup = callback.message.reply_markup

        if (current_text != message_text or
                str(current_markup) != str(new_keyboard)):
            await callback.message.edit_text(
                text=message_text,
                reply_markup=new_keyboard
            )
        else:
            await callback.answer(f"Уведомления уже {'включены' if new_status else 'выключены'}")
            return

        await callback.answer()

    except Exception as e:
        logger.error(f"Error toggling notifications: {e}")
        await callback.answer("⚠️ Произошла ошибка при изменении настроек", show_alert=True)

@router.callback_query(F.data.startswith("set_freq_"))
async def set_update_frequency(callback: types.CallbackQuery, db: DatabaseService):
    freq = int(callback.data.split("_")[-1])
    await db.set_update_frequency(callback.from_user.id, freq)

    settings = await db.get_user_settings(callback.from_user.id)
    status_text = "включены" if settings.notifications_enabled else "выключены"

    await callback.message.edit_text(
        f"🔔 Уведомления {status_text}\n"
        f"✅ Частота проверки: каждые {freq} мин",
        reply_markup=notification_settings_menu(settings.notifications_enabled)
    )
    await callback.answer(f"Частота обновления: {freq} мин")