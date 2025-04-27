from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram import Router, F
from aiogram import Bot
from aiogram.types import BotCommand

router = Router()

def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 Учебный план"), KeyboardButton(text="🔗 Полезные ресурсы")],
            
            [KeyboardButton(text="📖 Словарь IT терминов"), KeyboardButton(text="👥 Группа ИНИТ")]
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



