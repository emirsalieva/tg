from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def admin_main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 Управление учебным планом")],
            [KeyboardButton(text="🔗 Управление полезными ресурсами")],
            [KeyboardButton(text="📖 Управление словарем IT терминов")],
            [KeyboardButton(text="👥 Управление группой ИНИТ")],
            [KeyboardButton(text="⬅️ Назад в главное меню")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def manage_courses_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить курс")],
            [KeyboardButton(text="➖ Удалить курс")],
            [KeyboardButton(text="⬅️ Назад в админ панель")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def manage_resources_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить ресурс")],
            [KeyboardButton(text="➖ Удалить ресурс")],
            [KeyboardButton(text="⬅️ Назад в админ панель")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def manage_terms_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить термин")],
            [KeyboardButton(text="➖ Удалить термин")],
            [KeyboardButton(text="⬅️ Назад в админ панель")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def manage_groups_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить группу")],
            [KeyboardButton(text="➖ Удалить группу")],
            [KeyboardButton(text="⬅️ Назад в админ панель")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

# Клавиатура "Назад в админ панель"
def back_to_admin_panel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⬅️ Назад в админ панель")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
