from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💡 Идеи постов"), KeyboardButton(text="✍️ Создать пост")],
            [KeyboardButton(text="🖼 Создать изображение"), KeyboardButton(text="👀 Предпросмотр")],
            [KeyboardButton(text="❌ Отменить")],
        ],
        resize_keyboard=True,
    )


def actions_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Перегенерировать текст", callback_data="regen_text")],
        [InlineKeyboardButton(text="🎨 Перегенерировать изображение", callback_data="regen_image")],
        [InlineKeyboardButton(text="✅ Опубликовать", callback_data="publish_request")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")],
    ])


def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, опубликовать", callback_data="publish_confirm")],
        [InlineKeyboardButton(text="↩️ Нет, вернуться", callback_data="publish_abort")],
    ])

