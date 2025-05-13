from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
import sqlite3
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import CallbackQuery
from keyboards.main_keyboard import get_main_keyboard
from utils.pagination import get_all_terms, send_paginated_data, send_grouped_blocks

router = Router()

# Команда /start
@router.message(Command("start"))
async def cmd_start(message: Message):
    first_name = message.from_user.first_name

    greeting = (
        "🧠 Добро пожаловать в интеллектуальное пространство.\n\n"
        f"Здравствуйте, {first_name}.\n"
        "🔍 Я — ваш цифровой помощник, созданный для того, чтобы помочь вам погрузиться"
        "в учебный процесс и уверенно пройти путь первого курса в ИНИТ.\n\n"
        "🧭 Здесь вы найдёте структурированную информацию, полезные ресурсы и чёткие ответы.\n"
        "Готовы двигаться вперёд? Выберите интересующий раздел ниже ⬇️"
    )
    

    await message.answer(
        greeting,
        reply_markup=get_main_keyboard()
    )
   
# Команда /help
@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "🌟 **Добро пожаловать в вашего персонального помощника!** 🌟\n\n"
        "Этот бот создан, чтобы помочь вам легко ориентироваться в учебных материалах. 📚💻\n\n"
        "Вот что я могу для вас сделать:\n\n"
        "✨ **/start** — начни путешествие с ботом! 🚀\n"
        "✨ **/help** — нужна помощь? Я здесь, чтобы объяснить все! 💡\n"
        "✨ **/support** — свяжитесь с администратором, если возникнут вопросы! 📩\n"
        "✨ **/about** — узнайте больше о том, как я могу помочь вам в учебе! 🤖\n\n"
        "🔍 **Не забудьте воспользоваться кнопками на клавиатуре для быстрого доступа к разделам.** 🖱️",
        parse_mode="Markdown"
    )

# Команда /support
@router.message(Command("support"))
async def cmd_support(message: Message):
    await message.answer(
        "📩 Связь с администратором\n\n"
        "[Написать администратору](https://t.me/yokai_di)",
        parse_mode="Markdown"
    )

# Команда /about
@router.message(Command("about"))
async def cmd_about(message: Message):
    await message.answer(
        "🤖 **О боте**\n\n"
        "Привет! Я — твой персональный помощник для учебы в IT! 🎓💻\n\n"
        "Этот бот создан для первокурсников IT-направления университета КГУ, чтобы ты мог легко ориентироваться в учебных материалах и всегда быть на связи с самыми актуальными источниками. 🚀\n\n"
        "Вот что я могу предложить:\n\n"
        "📚 **Учебный план** — все курсы и лекции в одном месте. Строим план обучения вместе!\n"
        "📖 **Словарь IT-терминов** — запоминай термины, как профи, с объяснениями!\n"
        "🔗 **Полезные ресурсы** — переходи по ссылкам и открывай для себя мир IT!\n"
        "👥 **Информация о группе** — для знакомства и общения с твоими однокурсниками! Присоединяйся, делись опытом и находи новых друзей. 🤝"
        "💡 **Бот постоянно обновляется**, чтобы ты был в курсе самых последних изменений. И если у тебя есть идеи по улучшению — не стесняйся, пиши в /support! 😊",
        parse_mode="Markdown"
    )
  
# Показать учебный план
@router.message(lambda msg: msg.text == "📚 Учебный план")
async def show_study_plan(message: Message):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, description, link FROM courses')
    course_records = cursor.fetchall()
    conn.close()

    courses = [(name, description, link if link else "Ссылки нет") for _, name, description, link in course_records]

    await send_paginated_data(
        message=message,
        items=courses,
        formatter=lambda c: f"📚 {c[0]}\n{c[1]}\n{c[2]}",
        callback_prefix="courses"
    )

# Показать ресурсы
@router.message(lambda msg: msg.text == "🔗 Полезные ресурсы")
async def show_resources(message: Message):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute('SELECT name, description, link FROM resources')
    resources = cursor.fetchall()
    conn.close()

    await send_paginated_data(
        message=message,
        items=resources,
        formatter=lambda r: f"🔗 {r[0]}\n{r[1]}\n{r[2]}",
        callback_prefix="resources"
    )

# Показать словарь терминов
@router.message(F.text == "📖 Словарь IT терминов")
async def show_terms_menu(message: Message):
    # Клавиатура с выбором поиска
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔤 Поиск по букве", callback_data="terms_by_letter"),
            InlineKeyboardButton(text="📄 Все термины", callback_data="terms_all")
        ]
    ])

    await message.answer(
        "🔤 Выберите способ поиска IT терминов:",
        reply_markup=keyboard
    )
@router.callback_query(F.data == "terms_by_letter")
async def terms_by_letter(call: CallbackQuery):
    await call.message.answer(
        "Добро пожаловать в IT-словарь! \n\n"
        "🔤 Введите букву, чтобы увидеть термины на неё (английскую или русскую). \n\n"
        "📖 Вы можете вводить буквы сколько угодно — бот не ограничивает поиск. \n\n"
        "🔘 Используйте кнопки навигации для удобного просмотра:\n\n"
        "«Все термины», «Вперёд», «Назад». \n\n",
        parse_mode="Markdown"
    )
    await call.answer()

@router.callback_query(F.data == "terms_all")
async def terms_all(call: CallbackQuery):
    # Загружаем все термины из БД
    terms = get_all_terms()
    
    if not terms:
        await call.message.answer("😕 В словаре пока нет терминов.")
        return

    # Отправляем данные с пагинацией
    await send_paginated_data(
        message=call.message,
        items=terms,
        formatter=lambda t: f"<b>{t[0]}</b>\n{t[1]}",
        callback_prefix="terms_all"
    )
    await call.answer()


# Показать группы
@router.message(lambda msg: msg.text == "👥 Группа ИНИТ")
async def show_groups(message: Message):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute('SELECT name, description, link FROM groups')
    groups = cursor.fetchall()
    conn.close()

    if not groups:
        await message.answer("Информация отсутствует.")
        return

    def escape_markdown(text: str) -> str:
        escape_chars = r'\_*[]()~`>#+-=|{}.!'
        return ''.join(['\\' + c if c in escape_chars else c for c in text])

    await send_grouped_blocks(
        message,
        items=groups,
        formatter=lambda group: f"*{escape_markdown(group[0])}*\n{escape_markdown(group[1])}\n[Ссылка]({escape_markdown(group[2])})",
        block_size=5,
        parse_mode="MarkdownV2"
    )


async def load_courses(message: Message, page: int = 0):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, description, link FROM courses')
    course_records = cursor.fetchall()
    conn.close()

    courses = [(name, description, link or "Ссылки нет") for _, name, description, link in course_records]

    await send_paginated_data(
        message=message,
        items=courses,
        formatter=lambda c: f"📚 {c[0]}\n{c[1]}\n{c[2]}",
        callback_prefix="courses",
        page=page
    )

async def load_resources(message: Message, page: int = 0):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute('SELECT name, description, link FROM resources')
    resources = cursor.fetchall()
    conn.close()

    await send_paginated_data(
        message=message,
        items=resources,
        formatter=lambda r: f"🔗 {r[0]}\n{r[1]}\n{r[2]}",
        callback_prefix="resources",
        page=page
    )

async def load_terms(message: Message, page: int = 0):
    conn = sqlite3.connect("bot.db")
    cursor = conn.cursor()
    cursor.execute('SELECT term, definition FROM terms')
    terms = cursor.fetchall()
    conn.close()

    await send_paginated_data(
        message=message,
        items=terms,
        formatter=lambda t: f"🧠 {t[0]}\n{t[1]}",
        callback_prefix="terms",
        page=page
    )
