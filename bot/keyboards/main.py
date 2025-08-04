from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎁 Последние подарки")],
            [KeyboardButton(text="⚙ Настройки")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def settings_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔔 Уведомления", callback_data="notification_settings")],
            [InlineKeyboardButton(text="📊 Частота обновления", callback_data="update_frequency")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
        ]
    )


def notification_settings_menu(notifications_enabled: bool, current_freq: int = None) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(
                text=f"{'🔕 Выключить' if notifications_enabled else '🔔 Включить'} уведомления",
                callback_data="toggle_notifications"
            )
        ],
        [InlineKeyboardButton(text="📊 Частота обновления", callback_data="update_frequency")]
    ]

    if current_freq:
        buttons.insert(1, [InlineKeyboardButton(
            text=f"🔄 Текущая частота: {current_freq} мин",
            callback_data="show_frequency"
        )])

    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="settings_back")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def frequency_settings_menu(current_freq: int) -> InlineKeyboardMarkup:
    frequencies = [
        ("15 минут", 15),
        ("1 час", 60),
        ("3 часа", 180),
        ("1 день", 1440)
    ]

    buttons = []
    for text, freq in frequencies:
        selected = "✅ " if freq == current_freq else ""
        buttons.append([InlineKeyboardButton(
            text=f"{selected}{text}",
            callback_data=f"set_freq_{freq}"
        )])

    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="notification_settings")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

def cancel_button() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )