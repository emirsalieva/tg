from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
import json
from aiogram import Bot
from aiogram.types import BotCommand

router = Router()

# Функция для получения клавиатуры с курсами (без БД)
def get_study_plan_keyboard():
    courses = [
        "Информатика",
        "Информационные системы",
        "Операционные системы",
        "Основы алгоритмизации и программирования",
        "Web-программирование",
        "Инженерная графика",
        "Компьютерная графика",
        "Компьютерная информатика",
        "Алгоритмический язык",
        "Программирование",
    ]

    buttons = []
    for course_name in courses:
        callback_data = f"btn_course:{course_name[:64]}".replace(" ", "_").replace("-", "_").lower()
        buttons.append(InlineKeyboardButton(text=course_name, callback_data=callback_data))

    # Создаем клавиатуру с row_width=2
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(*buttons)

    # Выводим структуру клавиатуры для отладки
    print("Структура клавиатуры (без БД):")
    print(json.dumps(keyboard.model_dump(by_alias=True), indent=2, ensure_ascii=False))

    return keyboard

# Показывает учебный план
@router.message(F.text == "📚 Учебный план")
async def show_study_plan(message: Message):
    await message.answer("Выберите предмет:", reply_markup=get_study_plan_keyboard())

# Показывает информацию по предмету (оставим пока без изменений)
@router.callback_query(F.data.startswith("btn_course:"))
async def show_course_info(callback: CallbackQuery):
    course_name = callback.data.split(":")[1]
    course_name = course_name.replace("_", " ")
    text = f"Информация по предмету: {course_name} (данные из БД будут позже)"
    await callback.message.answer(text)
    await callback.answer()

def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 Учебный план")],
            [KeyboardButton(text="🔗 Полезные ресурсы")],
            [KeyboardButton(text="📖 Словарь IT терминов")],
            [KeyboardButton(text="👥 Группа ИНИТ")]
        ],
        resize_keyboard=True
    )
    return keyboard



async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="help", description="ℹ️ Справка"),
        BotCommand(command="support", description="📩 Связь с администратором"),
        BotCommand(command="about", description="🤖 О боте"),
    ]
    await bot.set_my_commands(commands)



