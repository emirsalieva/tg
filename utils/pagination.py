from aiogram import types, F, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.fsm.state import State, StatesGroup
import sqlite3

router = Router()

ITEMS_PER_PAGE = 5

# Функция для экранирования текста Markdown
def escape_markdown(text: str) -> str:
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    return ''.join(['\\' + c if c in escape_chars else c for c in text])

# Класс для работы с состоянием FSM для перехода по страницам
class GotoPage(StatesGroup):
    waiting_for_page_number = State()

# Клавиатура пагинации
def get_pagination_keyboard(page: int, total_pages: int, prefix: str) -> InlineKeyboardMarkup:
    buttons = []

    if page > 0:
        buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"{prefix}:{page - 1}"))
    if page < total_pages - 1:
        buttons.append(InlineKeyboardButton(text="➡️ Вперёд", callback_data=f"{prefix}:{page + 1}"))
    buttons.append(InlineKeyboardButton(text="🔢 Перейти к странице", callback_data=f"{prefix}:goto"))

    # Разбиваем на две строки
    keyboard = []
    if len(buttons) > 2:
        keyboard.append(buttons[:-1])  # кнопки Назад/Вперёд
        keyboard.append([buttons[-2]])  # кнопка Перейти
    else:
        keyboard.append(buttons)

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Отправка пагинированных данных
async def send_paginated_data(message: Message, items: list, formatter, callback_prefix: str, page: int = 0):
    total_pages = (len(items) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    current_items = items[start:end]

    text = "\n\n".join(formatter(item) for item in current_items)
    text += f"\n\n📄 Страница {page + 1} из {total_pages}"

    keyboard = get_pagination_keyboard(page, total_pages, callback_prefix)

    await message.answer(text, reply_markup=keyboard)

# Отправка пагинированных данных
async def send_paginated_data(message: Message, items: list, formatter, callback_prefix: str, page: int = 0):
    total_pages = (len(items) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    if page >= total_pages: 
        await message.answer("🚫 Страница не существует.")
        return

    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    current_items = items[start:end]

    # Проверка, если на текущей странице нет элементов
    if not current_items:
        await message.answer("🚫 Нет данных на этой странице.")
        return

    text = "\n\n".join(formatter(item) for item in current_items)
    text += f"\n\n📄 Страница {page + 1} из {total_pages}"

    keyboard = get_pagination_keyboard(page, total_pages, callback_prefix)

    await message.answer(text, reply_markup=keyboard)


# Обработка перехода по страницам
@router.callback_query(F.data.regexp(r'^(courses|resources|terms):(\d+)$'))
async def paginate_callback(call: CallbackQuery):
    prefix, page = call.data.split(":")
    page = int(page)
    if prefix == "courses":
        from handlers.main_handler import load_courses
        await load_courses(call.message, page=page)
    elif prefix == "resources":
        from handlers.main_handler import load_resources
        await load_resources(call.message, page=page)
    elif prefix == "terms":
        from handlers.main_handler import load_terms
        await load_terms(call.message, page=page)

    await call.answer()

# Кнопка "Перейти к странице"
@router.callback_query(F.data.regexp(r'^(courses|resources|terms):goto$'))
async def goto_page_prompt(call: CallbackQuery, state: FSMContext):
    prefix = call.data.split(":")[0]

    await state.update_data(prefix=prefix)
    await state.set_state(GotoPage.waiting_for_page_number)

    await call.message.answer("🔢 Введите номер страницы, на которую хотите перейти:")
    await call.answer()

# Обработка ввода номера страницы
@router.message(StateFilter(GotoPage.waiting_for_page_number))
async def process_goto_page(message: Message, state: FSMContext):
    user_data = await state.get_data()
    prefix = user_data.get("prefix")

    try:
        page = int(message.text.strip()) - 1
        if page < 0:
            raise ValueError

    except ValueError:
        await message.answer("🚫 Неверный номер страницы. Попробуйте снова.")
        return

    # Переходим к нужной странице
    if prefix == "courses":
        from handlers.main_handler import load_courses
        await load_courses(message, page=page)
    elif prefix == "resources":
        from handlers.main_handler import load_resources
        await load_resources(message, page=page)
    elif prefix == "terms":
        from handlers.main_handler import load_terms
        await load_terms(message, page=page)

    await state.clear()

# Группированная отправка (без пагинации)
async def send_grouped_blocks(message: Message, items: list, formatter, block_size: int = 5, parse_mode=None):
    for i in range(0, len(items), block_size):
        block = items[i:i + block_size]
        text = "\n\n".join(formatter(item) for item in block)
        await message.answer(text, parse_mode=parse_mode)

# Загрузка курсов, ресурсов и терминов
async def load_courses(message: Message, page: int = 0):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, description FROM courses")
    courses = cursor.fetchall()
    conn.close()

    if not courses:
        await message.answer("Информация о курсах отсутствует.")
        return

    # Форматируем данные и отправляем с пагинацией
    await send_paginated_data(message, courses, lambda course: f"*{escape_markdown(course[0])}*\n{escape_markdown(course[1])}", "courses", page)

async def load_resources(message: Message, page: int = 0):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, description, link FROM resources")
    resources = cursor.fetchall()
    conn.close()

    if not resources:
        await message.answer("Ресурсы отсутствуют.")
        return

    # Форматируем данные и отправляем с пагинацией
    await send_paginated_data(message, resources, lambda resource: f"*{escape_markdown(resource[0])}*\n{escape_markdown(resource[1])}\n[Ссылка]({escape_markdown(resource[2])})", "resources", page)

async def load_terms(message: Message, page: int = 0):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT term, definition FROM it_terms")
    terms = cursor.fetchall()
    conn.close()

    if not terms:
        await message.answer("Термины не найдены.")
        return

    # Форматируем данные и отправляем с пагинацией
    await send_paginated_data(message, terms, lambda term: f"*{escape_markdown(term[0])}*\n{escape_markdown(term[1])}", "terms", page)
