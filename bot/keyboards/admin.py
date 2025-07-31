from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def admin_panel() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
            [InlineKeyboardButton(text="⚙ Настройки мониторинга", callback_data="admin_settings")]
        ]
    )

def monitoring_settings() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Изменить каналы", callback_data="edit_channels")],
            [InlineKeyboardButton(text="💰 Изменить лимит цены", callback_data="edit_price_limit")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")]
        ]
    )