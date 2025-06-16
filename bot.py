import logging
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
import os
import asyncio

from handlers.main_handler import router as handlers_router
from handlers.admin_handlers import router as admin_router
from database.db_manager import init_db
from handlers.admin_handlers import check_admin_access  
from database.db_manager import get_items_page, get_total_items_count  
from utils.pagination_admin import register_pagination_handlers 
from utils.pagination import router as pagination_router

logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

async def main():
    """Основная функция запуска бота"""
    try:
        BOT_TOKEN = os.getenv("BOT_TOKEN")
        if not BOT_TOKEN:
            raise ValueError("BOT_TOKEN не найден в переменных окружения.")
        
        bot = Bot(token=BOT_TOKEN)
        dp = Dispatcher()

        dp.include_router(handlers_router)
        dp.include_router(admin_router)
        dp.include_router(pagination_router)

        register_pagination_handlers(admin_router, check_admin_access, get_items_page, get_total_items_count)

        try:
            init_db()
        except Exception as db_error:
            logger.error(f"Ошибка инициализации БД: {db_error}")
            raise

        await dp.start_polling(bot)

    except KeyboardInterrupt:
        logger.error("Бот остановлен пользователем.")
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}")
        raise
    finally:
        logger.error("Завершение работы бота...")
        await bot.close() if 'bot' in locals() else None

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.error("Программа завершена пользователем.")
    except Exception as e:
        logger.critical(f"Фатальная ошибка: {e}")
