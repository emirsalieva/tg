from aiogram import types, F, Router
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters import StateFilter
from aiogram.fsm.state import State, StatesGroup
import sqlite3

router = Router()

ITEMS_PER_PAGE = 5
TERMS_PER_PAGE = 10

class GotoPage(StatesGroup):
    waiting_for_page_number = State()

# ---------- БАЗОВАЯ ПАГИНАЦИЯ ----------
def get_pagination_keyboard(page: int, total_pages: int, prefix: str) -> InlineKeyboardMarkup:
    buttons = []

    if page > 0:
        buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"{prefix}:{page - 1}"))
    if page < total_pages - 1:
        buttons.append(InlineKeyboardButton(text="➡️ Вперёд", callback_data=f"{prefix}:{page + 1}"))
    buttons.append(InlineKeyboardButton(text="🔢 Перейти к странице", callback_data=f"{prefix}:goto"))

    keyboard = [buttons[:-1], [buttons[-1]]] if len(buttons) > 2 else [buttons]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def send_paginated_data(message: Message, items: list, formatter, callback_prefix: str, page: int = 0):
    total_pages = (len(items) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    current_items = items[start:end]

    text = "\n\n".join(formatter(item) for item in current_items)
    text += f"\n\n📄 Страница {page + 1} из {total_pages}"

    keyboard = get_pagination_keyboard(page, total_pages, callback_prefix)
    await message.answer(text, reply_markup=keyboard)

# ---------- ТЕРМИНЫ: ФУНКЦИИ И КЛАВИАТУРА ----------
def get_terms_pagination_keyboard(letter: str, page: int, has_next_page: bool) -> InlineKeyboardMarkup:
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"terms_letter:{letter}:{page - 1}"))
    buttons.append(InlineKeyboardButton(text="Все термины", callback_data="terms_all:0"))
    if has_next_page:
        buttons.append(InlineKeyboardButton(text="➡️ Вперёд", callback_data=f"terms_letter:{letter}:{page + 1}"))
    return InlineKeyboardMarkup(inline_keyboard=[buttons])

def get_terms_by_letter(letter: str, offset: int = 0):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute(
        'SELECT term, definition FROM terms WHERE UPPER(SUBSTR(term, 1, 1)) = ? ORDER BY term LIMIT ? OFFSET ?',
        (letter.upper(), TERMS_PER_PAGE + 1, offset)
    )
    terms = cursor.fetchall()
    conn.close()
    return terms

def get_all_terms(offset: int = 0):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute(
        'SELECT term, definition FROM terms ORDER BY term LIMIT ? OFFSET ?',
        (TERMS_PER_PAGE + 1, offset)
    )
    terms = cursor.fetchall()
    conn.close()
    return terms

def format_terms_response(terms: list, title: str) -> str:
    response = f"📖 IT термины ({title}):\n\n"
    for term in terms:
        response += f"<b>{term[0]}</b>\n{term[1]}\n\n"
    return response.strip()

# ---------- СЛОВАРЬ ----------
@router.message(F.text == "📖 Словарь IT терминов")
async def show_terms_menu(message: Message):
    await message.answer(
        "🔤 Введите букву для поиска IT терминов (английскую или русскую):\n"
        "Или введите 'все' для полного списка терминов"
    )

@router.message(F.text.func(lambda text: len(text.strip()) == 1 and text.strip().isalpha()))
async def show_terms_by_letter(message: Message):
    letter = message.text.strip().upper()
    terms = get_terms_by_letter(letter)
    if not terms:
        await message.answer(f"😕 Терминов на букву '{letter}' не найдено")
        return

    has_next_page = len(terms) > TERMS_PER_PAGE
    response = format_terms_response(terms[:TERMS_PER_PAGE], f"на букву {letter}")
    keyboard = get_terms_pagination_keyboard(letter, 0, has_next_page)

    await message.answer(response, parse_mode="HTML", reply_markup=keyboard)

@router.callback_query(F.data.startswith("terms_letter:"))
async def handle_terms_letter_pagination(call: CallbackQuery):
    _, letter, page_str = call.data.split(":")
    page = int(page_str)
    terms = get_terms_by_letter(letter, page * TERMS_PER_PAGE)
    if not terms:
        await call.answer("😕 Больше терминов не найдено")
        return

    has_next_page = len(terms) > TERMS_PER_PAGE
    response = format_terms_response(terms[:TERMS_PER_PAGE], f"на букву {letter} (страница {page + 1})")
    keyboard = get_terms_pagination_keyboard(letter, page, has_next_page)

    await call.message.edit_text(response, parse_mode="HTML", reply_markup=keyboard)
    await call.answer()

@router.message(F.text.strip().lower() == "все")
async def show_all_terms(message: Message):
    terms = get_all_terms()
    if not terms:
        await message.answer("😕 В словаре пока нет терминов")
        return

    has_next_page = len(terms) > TERMS_PER_PAGE
    response = format_terms_response(terms[:TERMS_PER_PAGE], "все")
    buttons = [
        InlineKeyboardButton(text="➡️ Вперёд", callback_data="terms_all:1")
    ] if has_next_page else []
    buttons.append(InlineKeyboardButton(text="🔙 По буквам", callback_data="terms_letters_back"))
    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])

    await message.answer(response, parse_mode="HTML", reply_markup=keyboard)

@router.callback_query(F.data.startswith("terms_all:"))
async def handle_all_terms_pagination(call: CallbackQuery):
    _, page_str = call.data.split(":")
    page = int(page_str)
    terms = get_all_terms(page * TERMS_PER_PAGE)
    if not terms:
        await call.answer("😕 Больше терминов не найдено")
        return

    has_next_page = len(terms) > TERMS_PER_PAGE
    response = format_terms_response(terms[:TERMS_PER_PAGE], f"все (страница {page + 1})")

    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"terms_all:{page - 1}"))
    if has_next_page:
        buttons.append(InlineKeyboardButton(text="➡️ Вперёд", callback_data=f"terms_all:{page + 1}"))
    buttons.append(InlineKeyboardButton(text="🔙 По буквам", callback_data="terms_letters_back"))

    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
    await call.message.edit_text(response, parse_mode="HTML", reply_markup=keyboard)
    await call.answer()

@router.callback_query(F.data == "terms_letters_back")
async def handle_letters_back(call: CallbackQuery):
    await call.message.answer(
        "🔤 Введите букву для поиска IT терминов (английскую или русскую):\n"
        "Или введите 'все' для полного списка терминов"
    )
    await call.answer()

@router.message(F.text.func(lambda text: len(text.strip()) > 1 and text.strip().isalpha()))
async def handle_multiple_letters(message: Message):
    await message.answer("ℹ️ Пожалуйста, введите только одну букву для поиска терминов")

# ---------- ОБЩАЯ ПАГИНАЦИЯ ----------
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

@router.callback_query(F.data.regexp(r'^(courses|resources|terms):goto$'))
async def goto_page_prompt(call: CallbackQuery, state: FSMContext):
    prefix = call.data.split(":")[0]
    await state.update_data(prefix=prefix)
    await state.set_state(GotoPage.waiting_for_page_number)
    await call.message.answer("🔢 Введите номер страницы, на которую хотите перейти:")
    await call.answer()

@router.message(StateFilter(GotoPage.waiting_for_page_number))
async def process_goto_page(message: Message, state: FSMContext):
    user_data = await state.get_data()
    prefix = user_data.get("prefix")

    try:
        page = int(message.text.strip()) - 1
        if page < 0:
            raise ValueError

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
    except ValueError:
        await message.answer("🚫 Неверный номер страницы. Попробуйте снова.")

#Группа
async def send_grouped_blocks(message: Message, items: list, formatter, block_size: int = 5, parse_mode=None):
    for i in range(0, len(items), block_size):
        block = items[i:i + block_size]
        text = "\n\n".join(formatter(item) for item in block)
        await message.answer(text, parse_mode=parse_mode)
