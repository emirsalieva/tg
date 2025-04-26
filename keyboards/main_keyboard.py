from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Router, F
from aiogram.types import CallbackQuery
import json
from aiogram import Bot
from aiogram.types import BotCommand

router = Router()

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



