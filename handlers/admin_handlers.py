# handlers/admin_handler.py
from aiogram import Router, F, Bot 
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from dotenv import load_dotenv
import os
import logging
import math 
from utils.pagination_admin import create_paginated_keyboard, ADMIN_DELETE_ITEMS_PER_PAGE
from keyboards.admin_keyboard import (
    admin_main_menu,
    manage_courses_keyboard,
    manage_resources_keyboard,
    manage_terms_keyboard,
    manage_groups_keyboard
)
from database.db_manager import (
    add_course, delete_course,
    add_resource,  delete_resource,
    add_term, delete_term,
    add_group,  delete_group,
    get_items_page, get_total_items_count
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
router = Router()

# Класс для управления состояниями FSM 
class AdminStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_link = State()
    waiting_for_goto_page_number = State()
  
# Функция для проверки прав администратора
async def check_admin_access(event: Message | CallbackQuery) -> bool:
    try:
        admin_ids_str = os.getenv("ADMIN_IDS")
        if not admin_ids_str:
             logger.error("Переменная окружения ADMIN_IDS не установлена.")
             if isinstance(event, Message):
                  await event.answer("⚠️ Ошибка конфигурации бота. ADMIN_IDS не установлен.")
             elif isinstance(event, CallbackQuery):
                  await event.answer("⚠️ Ошибка конфигурации бота. ADMIN_IDS не установлен.", show_alert=True)
             return False

        ADMIN_IDS = [int(id.strip()) for id in admin_ids_str.split(",")]
        user_id = event.from_user.id

        if user_id not in ADMIN_IDS:
            if isinstance(event, Message):
                 await event.answer("⛔ У вас нет доступа к этой команде.")
            elif isinstance(event, CallbackQuery):
                 await event.answer("⛔ У вас нет доступа к этой команде.", show_alert=True)
            return False
        return True
    except ValueError:
         logger.error(f"Ошибка при парсинге ADMIN_IDS: {os.getenv('ADMIN_IDS')}. Убедитесь, что это числа, разделенные запятыми.")
         if isinstance(event, Message):
              await event.answer("⚠️ Ошибка конфигурации бота. Неверный формат ADMIN_IDS.")
         elif isinstance(event, CallbackQuery):
              await event.answer("⚠️ Ошибка конфигурации бота. Неверный формат ADMIN_IDS.", show_alert=True)
         return False
    except Exception as e:
        logger.error(f"Ошибка проверки прав: {e}")
        if isinstance(event, Message):
             await event.answer("⚠️ Произошла ошибка при проверке прав доступа.")
        elif isinstance(event, CallbackQuery):
             await event.answer("⚠️ Произошла ошибка при проверке прав доступа.", show_alert=True)
        return False

# --- Обработчики главного меню админ-панели ---
@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not await check_admin_access(message): return
    await message.answer("👨‍💻 Добро пожаловать в админ-панель!", reply_markup=admin_main_menu())

@router.message(F.text == "📚 Управление учебным планом")
async def manage_courses(message: Message):
    if not await check_admin_access(message): return
    await message.answer("📚 Управление учебным планом:", reply_markup=manage_courses_keyboard())

@router.message(F.text == "🔗 Управление полезными ресурсами")
async def manage_resources(message: Message):
    if not await check_admin_access(message): return
    await message.answer("🔗 Управление полезными ресурсами:", reply_markup=manage_resources_keyboard())

@router.message(F.text == "📖 Управление словарем IT терминов")
async def manage_terms(message: Message):
    if not await check_admin_access(message): return
    await message.answer("📖 Управление словарем IT терминов:", reply_markup=manage_terms_keyboard())

@router.message(F.text == "👥 Управление группой ИНИТ")
async def manage_groups(message: Message):
    if not await check_admin_access(message): return
    await message.answer("👥 Управление группой ИНИТ:", reply_markup=manage_groups_keyboard())

# --- Обработчики добавления элементов  ---
@router.message(F.text.in_(["➕ Добавить курс", "➕ Добавить ресурс", "➕ Добавить термин", "➕ Добавить группу"]))
async def add_entity_start(message: Message, state: FSMContext):
    if not await check_admin_access(message): return
    await state.set_data({"action": message.text})
    await state.set_state(AdminStates.waiting_for_name)
    await message.answer("📝 Введите название:", reply_markup=ReplyKeyboardRemove()) 

@router.message(StateFilter(AdminStates.waiting_for_name))
async def handle_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if not name:
        await message.answer("⚠️ Название не может быть пустым. Попробуйте еще раз:")
        return
    await state.update_data(name=name)
    await state.set_state(AdminStates.waiting_for_description)
    await message.answer("📄 Введите описание:")

@router.message(StateFilter(AdminStates.waiting_for_description))
async def handle_description(message: Message, state: FSMContext):
    description = message.text.strip()
    await state.update_data(description=description)

    data = await state.get_data()
    action = data["action"]

    if action == "➕ Добавить термин":
        try:
            success = add_term(data["name"], data["description"]) 
            if success:
                await message.answer(f"✅ Термин '{data['name']}' добавлен!", reply_markup=admin_main_menu())
            else:
                await message.answer(f"❌ Не удалось добавить термин '{data['name']}'. Возможно, он уже существует.", reply_markup=admin_main_menu())
        except Exception as e:
             logger.error(f"Ошибка добавления термина: {e}")
             await message.answer("⚠️ Произошла ошибка при добавлении термина.")
        finally:
            await state.clear()
    else:
        await state.set_state(AdminStates.waiting_for_link)
        await message.answer("🔗 Введите ссылку (http:// или https://):")

@router.message(StateFilter(AdminStates.waiting_for_link))
async def handle_link(message: Message, state: FSMContext):
    link = message.text.strip()
    data = await state.get_data()
    action = data.get("action")

    if action in ["➕ Добавить курс", "➕ Добавить ресурс", "➕ Добавить группу"]:
        if not link.startswith(("http://", "https://")):
            await message.answer("⚠️ Ссылка должна начинаться с http:// или https://. Попробуйте снова:")
            return

    if not link: 
         await message.answer("⚠️ Ссылка не может быть пустой для этого элемента. Попробуйте снова:")
         return

    name = data.get("name")
    description = data.get("description")

    try:
        success = False
        if action == "➕ Добавить курс":
            success = add_course(name, description, link) 
        elif action == "➕ Добавить ресурс":
            success = add_resource(name, description, link) 
        elif action == "➕ Добавить группу":
             success = add_group(name, description, link)
        else:
             logger.warning(f"Неизвестное действие в handle_link: {action}")
             await message.answer("⚠️ Неизвестное действие. Произошла внутренняя ошибка.")
             success = False

        if success:
            await message.answer(f"✅ '{name}' успешно добавлен!", reply_markup=admin_main_menu())
        else:
            await message.answer(f"❌ Ошибка при добавлении '{name}'.", reply_markup=admin_main_menu())
    except Exception as e:
        logger.error(f"Ошибка добавления элемента в handle_link: {e}")
        await message.answer("⚠️ Произошла ошибка при добавлении.")
    finally:
        await state.clear()

# --- Обработчики начала удаления (с пагинацией) ---
@router.message(F.text == "➖ Удалить курс")
async def delete_course_start(message: Message):
    if not await check_admin_access(message): return
    category = "course"
    total_items = await get_total_items_count(category)
    current_page_items = await get_items_page(category, 1, ADMIN_DELETE_ITEMS_PER_PAGE)

    if not current_page_items and total_items > 0:
         await message.answer("ℹ️ Курсы отсутствуют или произошла ошибка загрузки.", reply_markup=manage_courses_keyboard())
         return
    elif not current_page_items and total_items == 0:
         await message.answer("ℹ️ Курсы отсутствуют.", reply_markup=manage_courses_keyboard()) 
         return

    # Используем функцию создания клавиатуры из pagination_utils
    keyboard = await create_paginated_keyboard(
        items=current_page_items,
        page=1,
        items_per_page=ADMIN_DELETE_ITEMS_PER_PAGE,
        total_items=total_items,
        pagination_callback_prefix=f"navigate_delete_{category}", 
        item_callback_prefix=f"del_{category}_by_id", 
        item_id_index=0,
        item_name_index=1 
    )
    await message.answer("🗑️ Выберите курс для удаления:", reply_markup=keyboard)


@router.message(F.text == "➖ Удалить ресурс")
async def delete_resource_start(message: Message):
    if not await check_admin_access(message): return
    category = "resource"
    total_items = await get_total_items_count(category)
    current_page_items = await get_items_page(category, 1, ADMIN_DELETE_ITEMS_PER_PAGE)

    if not current_page_items and total_items > 0:
         await message.answer("ℹ️ Ресурсы отсутствуют или произошла ошибка загрузки.", reply_markup=manage_resources_keyboard())
         return
    elif not current_page_items and total_items == 0:
         await message.answer("ℹ️ Ресурсы отсутствуют.", reply_markup=manage_resources_keyboard())
         return

    keyboard = await create_paginated_keyboard(
        items=current_page_items,
        page=1,
        items_per_page=ADMIN_DELETE_ITEMS_PER_PAGE,
        total_items=total_items,
        pagination_callback_prefix=f"navigate_delete_{category}",
        item_callback_prefix=f"del_{category}_by_id",
        item_id_index=0, 
        item_name_index=1, 
    )
    await message.answer("🗑️ Выберите ресурс для удаления:", reply_markup=keyboard)


@router.message(F.text == "➖ Удалить термин")
async def delete_term_start(message: Message):
    if not await check_admin_access(message): return
    category = "term"
    total_items = await get_total_items_count(category)
    current_page_items = await get_items_page(category, 1, ADMIN_DELETE_ITEMS_PER_PAGE)

    if not current_page_items and total_items > 0:
         await message.answer("ℹ️ Термины отсутствуют или произошла ошибка загрузки.", reply_markup=manage_terms_keyboard())
         return
    elif not current_page_items and total_items == 0:
         await message.answer("ℹ️ Термины отсутствуют.", reply_markup=manage_terms_keyboard())
         return

    keyboard = await create_paginated_keyboard(
        items=current_page_items,
        page=1,
        items_per_page=ADMIN_DELETE_ITEMS_PER_PAGE,
        total_items=total_items,
        pagination_callback_prefix=f"navigate_delete_{category}",
        item_callback_prefix=f"del_{category}_by_name", 
        item_id_index=0,
        item_name_index=0, 
    )
    await message.answer("🗑️ Выберите термин для удаления:", reply_markup=keyboard)


@router.message(F.text == "➖ Удалить группу")
async def delete_group_start(message: Message):
    if not await check_admin_access(message): return
    category = "group"
    total_items = await get_total_items_count(category)
    current_page_items = await get_items_page(category, 1, ADMIN_DELETE_ITEMS_PER_PAGE)

    if not current_page_items and total_items > 0:
         await message.answer("ℹ️ Группы отсутствуют или произошла ошибка загрузки.", reply_markup=manage_groups_keyboard())
         return
    elif not current_page_items and total_items == 0:
         await message.answer("ℹ️ Группы отсутствуют.", reply_markup=manage_groups_keyboard())
         return

    # Используем функцию создания клавиатуры из pagination_utils
    keyboard = await create_paginated_keyboard(
        items=current_page_items,
        page=1,
        items_per_page=ADMIN_DELETE_ITEMS_PER_PAGE,
        total_items=total_items,
        pagination_callback_prefix=f"navigate_delete_{category}",
        item_callback_prefix=f"del_{category}_by_id",
        item_id_index=0, 
        item_name_index=1,
    )
    await message.answer("🗑️ Выберите группу для удаления:", reply_markup=keyboard)


@router.callback_query(F.data.startswith("del_course_by_id:"))
async def handle_delete_course_by_id(callback: CallbackQuery):
    if not await check_admin_access(callback): return
    category = "course"
    try:
        parts = callback.data.split(":")
        course_id = int(parts[1])
        current_page = 1 
        if len(parts) > 3 and parts[2] == 'page':
             current_page = int(parts[3])


        success = delete_course(course_id) 
        if success:
            await callback.answer(f"Курс (ID: {course_id}) успешно удален!", show_alert=True)
            total_items = await get_total_items_count(category)
            total_pages = math.ceil(total_items / ADMIN_DELETE_ITEMS_PER_PAGE) if total_items > 0 else 1 
            target_page = current_page
            if total_items > 0 and target_page > total_pages:
                 target_page = total_pages 
            if target_page < 1 and total_items > 0: target_page = 1
            if total_items == 0: target_page = 1 


            current_page_items = await get_items_page(category, target_page, ADMIN_DELETE_ITEMS_PER_PAGE)


            if not current_page_items and total_items > 0:
                 from keyboards.admin_keyboard import manage_courses_keyboard 
                 await callback.message.edit_text("ℹ️ Курсы отсутствуют.", reply_markup=manage_courses_keyboard())

            elif not current_page_items and total_items == 0:
                  from keyboards.admin_keyboard import manage_courses_keyboard
                  await callback.message.edit_text("ℹ️ Курсы отсутствуют.", reply_markup=manage_courses_keyboard())
            else:
                 keyboard = await create_paginated_keyboard(
                     items=current_page_items,
                     page=target_page,
                     items_per_page=ADMIN_DELETE_ITEMS_PER_PAGE,
                     total_items=total_items,
                     pagination_callback_prefix=f"navigate_delete_{category}",
                     item_callback_prefix=f"del_{category}_by_id",
                     item_id_index=0, item_name_index=1,
                 )
                 await callback.message.edit_reply_markup(reply_markup=keyboard)


        else:
             await callback.answer(f"Не удалось удалить курс с ID {course_id}. Возможно, он уже удален.", show_alert=True)
    except (ValueError, IndexError) as e:
         logger.error(f"Неверный формат данных в callback_data удаления курса: {callback.data} - {e}")
         await callback.answer("⚠️ Ошибка: Неверный формат данных для удаления курса.", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка удаления курса по ID: {e}")
        await callback.answer("⚠️ Произошла ошибка при удалении курса.", show_alert=True)


@router.callback_query(F.data.startswith("del_resource_by_id:"))
async def handle_delete_resource_by_id(callback: CallbackQuery):
    if not await check_admin_access(callback): return
    category = "resource"
    try:
        parts = callback.data.split(":")
        resource_id = int(parts[1])
        current_page = 1
        if len(parts) > 3 and parts[2] == 'page':
             current_page = int(parts[3])

        success = delete_resource(resource_id) 

        if success:
            await callback.answer(f"Ресурс (ID: {resource_id}) успешно удален!", show_alert=True)

            total_items = await get_total_items_count(category)
            total_pages = math.ceil(total_items / ADMIN_DELETE_ITEMS_PER_PAGE) if total_items > 0 else 1
            target_page = current_page
            if total_items > 0 and target_page > total_pages:
                 target_page = total_pages
            if target_page < 1 and total_items > 0: target_page = 1
            if total_items == 0: target_page = 1

            current_page_items = await get_items_page(category, target_page, ADMIN_DELETE_ITEMS_PER_PAGE)

            if not current_page_items and total_items > 0:
                 from keyboards.admin_keyboard import manage_resources_keyboard
                 await callback.message.edit_text("ℹ️ Ресурсы отсутствуют.", reply_markup=manage_resources_keyboard())
            elif not current_page_items and total_items == 0:
                  from keyboards.admin_keyboard import manage_resources_keyboard
                  await callback.message.edit_text("ℹ️ Ресурсы отсутствуют.", reply_markup=manage_resources_keyboard())
            else:
                 keyboard = await create_paginated_keyboard(
                     items=current_page_items,
                     page=target_page,
                     items_per_page=ADMIN_DELETE_ITEMS_PER_PAGE,
                     total_items=total_items,
                     pagination_callback_prefix=f"navigate_delete_{category}",
                     item_callback_prefix=f"del_{category}_by_id",
                     item_id_index=0, item_name_index=1,
                 )
                 await callback.message.edit_reply_markup(reply_markup=keyboard)

        else:
            await callback.answer(f"Не удалось удалить ресурс с ID {resource_id}. Возможно, он уже удален.", show_alert=True)
    except (ValueError, IndexError) as e:
         logger.error(f"Неверный формат данных в callback_data удаления ресурса: {callback.data} - {e}")
         await callback.answer("⚠️ Ошибка: Неверный формат данных для удаления ресурса.", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка удаления ресурса по ID: {e}")
        await callback.answer("⚠️ Произошла ошибка при удалении ресурса.", show_alert=True)


@router.callback_query(F.data.startswith("del_term_by_name:"))
async def handle_delete_term_by_name(callback: CallbackQuery):
    if not await check_admin_access(callback): return
    category = "term"
    try:
        parts = callback.data.split(":")
        term_name = parts[1]
        current_page = 1
        if len(parts) > 3 and parts[2] == 'page':
             current_page = int(parts[3])

        success = delete_term(term_name) 

        if success:
            await callback.answer(f"Термин '{term_name}' успешно удален!", show_alert=True)

            total_items = await get_total_items_count(category)
            total_pages = math.ceil(total_items / ADMIN_DELETE_ITEMS_PER_PAGE) if total_items > 0 else 1
            target_page = current_page
            if total_items > 0 and target_page > total_pages:
                 target_page = total_pages
            if target_page < 1 and total_items > 0: target_page = 1
            if total_items == 0: target_page = 1


            current_page_items = await get_items_page(category, target_page, ADMIN_DELETE_ITEMS_PER_PAGE)

            if not current_page_items and total_items > 0:
                 from keyboards.admin_keyboard import manage_terms_keyboard
                 await callback.message.edit_text("ℹ️ Термины отсутствуют.", reply_markup=manage_terms_keyboard())
            elif not current_page_items and total_items == 0:
                  from keyboards.admin_keyboard import manage_terms_keyboard
                  await callback.message.edit_text("ℹ️ Термины отсутствуют.", reply_markup=manage_terms_keyboard())
            else:
                 keyboard = await create_paginated_keyboard(
                     items=current_page_items,
                     page=target_page,
                     items_per_page=ADMIN_DELETE_ITEMS_PER_PAGE,
                     total_items=total_items,
                     pagination_callback_prefix=f"navigate_delete_{category}",
                     item_callback_prefix=f"del_{category}_by_name",
                     item_id_index=0, item_name_index=0,
                 )
                 await callback.message.edit_reply_markup(reply_markup=keyboard)

        else:
            await callback.answer(f"Не удалось удалить термин '{term_name}'. Проверьте имя.", show_alert=True)
    except (ValueError, IndexError) as e:
        logger.error(f"Неверный формат данных в callback_data удаления термина: {callback.data} - {e}")
        await callback.answer("⚠️ Ошибка: Неверный формат данных для удаления термина.", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка удаления термина по имени: {e}")
        await callback.answer("⚠️ Произошла ошибка при удалении термина.", show_alert=True)


@router.callback_query(F.data.startswith("del_group_by_id:"))
async def handle_delete_group_by_id(callback: CallbackQuery):
    if not await check_admin_access(callback): return
    category = "group"
    try:
        parts = callback.data.split(":")
        group_id = int(parts[1])
        current_page = 1
        if len(parts) > 3 and parts[2] == 'page':
             current_page = int(parts[3])

        success = delete_group(group_id) 

        if success:
            await callback.answer(f"Группа (ID: {group_id}) успешно удалена!", show_alert=True)

            total_items = await get_total_items_count(category)
            total_pages = math.ceil(total_items / ADMIN_DELETE_ITEMS_PER_PAGE) if total_items > 0 else 1
            target_page = current_page
            if total_items > 0 and target_page > total_pages:
                 target_page = total_pages
            if target_page < 1 and total_items > 0: target_page = 1
            if total_items == 0: target_page = 1

            current_page_items = await get_items_page(category, target_page, ADMIN_DELETE_ITEMS_PER_PAGE)

            if not current_page_items and total_items > 0:
                 from keyboards.admin_keyboard import manage_groups_keyboard
                 await callback.message.edit_text("ℹ️ Группы отсутствуют.", reply_markup=manage_groups_keyboard())
            elif not current_page_items and total_items == 0:
                  from keyboards.admin_keyboard import manage_groups_keyboard
                  await callback.message.edit_text("ℹ️ Группы отсутствуют.", reply_markup=manage_groups_keyboard())
            else:
                 keyboard = await create_paginated_keyboard(
                     items=current_page_items,
                     page=target_page,
                     items_per_page=ADMIN_DELETE_ITEMS_PER_PAGE,
                     total_items=total_items,
                     pagination_callback_prefix=f"navigate_delete_{category}",
                     item_callback_prefix=f"del_{category}_by_id",
                     item_id_index=0, item_name_index=1,
                 )
                 await callback.message.edit_reply_markup(reply_markup=keyboard)

        else:
            await callback.answer(f"Не удалось удалить группу с ID {group_id}. Возможно, она уже удалена.", show_alert=True)
    except (ValueError, IndexError) as e:
        logger.error(f"Неверный формат данных в callback_data удаления группы: {callback.data} - {e}")
        await callback.answer("⚠️ Ошибка: Неверный формат данных для удаления группы.", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка удаления группы по ID: {e}")
        await callback.answer("⚠️ Произошла ошибка при удалении группы.", show_alert=True)


@router.callback_query(F.data.startswith("goto_delete_page:"))
async def ask_for_page_number(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if not await check_admin_access(callback): return

    try:
        category = callback.data.split(":")[1] 
        await state.set_state(AdminStates.waiting_for_goto_page_number)
        await state.update_data(goto_category=category, original_message_id=callback.message.message_id, chat_id=callback.message.chat.id)

        await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text="🔢 Введите номер страницы:")
        await callback.answer()

    except IndexError:
        logger.error(f"Неверный формат callback_data для goto_delete_page: {callback.data}")
        await callback.answer("⚠️ Ошибка: Неверный запрос страницы.", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка при обработке goto_delete_page: {e}")
        await callback.answer("⚠️ Произошла ошибка.", show_alert=True)

@router.message(StateFilter(AdminStates.waiting_for_goto_page_number))
async def process_goto_page_number(message: Message, state: FSMContext, bot: Bot):
    if not await check_admin_access(message):
        await state.clear() 
        return

    try:
        page_number_str = message.text.strip()
        page = int(page_number_str) 

        data = await state.get_data()
        category = data.get("goto_category")
        original_message_id = data.get("original_message_id")
        chat_id = data.get("chat_id")

        if not category or original_message_id is None or chat_id is None:
             logger.error("Состояние FSM для goto_page не содержит нужных данных.")
             await message.answer("⚠️ Ошибка состояния. Попробуйте снова.")
             await state.clear() 
             return
        
        total_items = await get_total_items_count(category)
        total_pages = math.ceil(total_items / ADMIN_DELETE_ITEMS_PER_PAGE) if total_items > 0 else 1 

        # Валидация номера страницы
        if page < 1 or page > total_pages:
            await message.answer(f"⚠️ Неверный номер страницы. Введите число от 1 до {total_pages}:")
            return 

        # Получаем элементы для запрошенной страницы
        items = await get_items_page(category, page, ADMIN_DELETE_ITEMS_PER_PAGE)

        # добавим проверку
        if not items and total_items > 0:
             logger.warning(f"Запрошена страница {page}, но список пуст при total_items > 0 для категории {category}")
             await message.answer("⚠️ На запрошенной странице нет элементов. Попробуйте другой номер.")
             return 
        elif not items and total_items == 0:
             
             empty_message = f"ℹ️ {category.capitalize()} отсутствуют."
             if category == "course": empty_message = "ℹ️ Курсы отсутствуют."
             elif category == "resource": empty_message = "ℹ️ Ресурсы отсутствуют."
             elif category == "term": empty_message = "ℹ️ Термины отсутствуют."
             elif category == "group": empty_message = "ℹ️ Группы отсутствуют."

             try:
                 await bot.edit_message_text(chat_id=chat_id, message_id=original_message_id, text=empty_message, reply_markup=None)
                 await message.answer("ℹ️ Элементы отсутствуют.") 
             except Exception as e:
                 logger.error(f"Ошибка при редактировании оригинального сообщения после удаления всех элементов: {e}")
                 await message.answer("ℹ️ Элементы отсутствуют.") 
             await state.clear() 
             return


        # Определяем индексы ID и имени для создания кнопок элементов
        item_id_index = 0 
        item_name_index = 1 
        item_callback_prefix_base = f"del_{category}_by_id" 

        if category == "term":
            item_id_index = 0 
            item_name_index = 0 
            item_callback_prefix_base = "del_term_by_name" 

        # Создаем клавиатуру для запрошенной страницы
        keyboard = await create_paginated_keyboard(
            items=items,
            page=page,
            items_per_page=ADMIN_DELETE_ITEMS_PER_PAGE,
            total_items=total_items,
            pagination_callback_prefix=f"navigate_delete_{category}",
            item_callback_prefix=item_callback_prefix_base,
            item_id_index=item_id_index,
            item_name_index=item_name_index
        )

        message_text = f"🗑️ Выберите {category.capitalize()} для удаления:"
        if category == "course": message_text = "🗑️ Выберите курс для удаления:"
        elif category == "resource": message_text = "🗑️ Выберите ресурс для удаления:"
        elif category == "term": message_text = "🗑️ Выберите термин для удаления:"
        elif category == "group": message_text = "🗑️ Выберите группу для удаления:"

        try:
            await bot.edit_message_text(chat_id=chat_id, message_id=original_message_id, text=message_text, reply_markup=keyboard)
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        except Exception as e:
             logger.error(f"Ошибка при редактировании оригинального сообщения для показа страницы {page}: {e}")
             await message.answer("⚠️ Произошла ошибка при обновлении страницы.")


        await state.clear() 

    except ValueError:
        data = await state.get_data()
        category = data.get("goto_category", "элементов") 
        try:
             total_items = await get_total_items_count(category)
             total_pages = math.ceil(total_items / ADMIN_DELETE_ITEMS_PER_PAGE) if total_items > 0 else 1
             await message.answer(f"⚠️ Неверный формат. Введите **целое число** от 1 до {total_pages}:")
        except Exception as e:
             logger.error(f"Ошибка при получении total_items для валидации в catch ValueError: {e}")
             await message.answer("⚠️ Неверный формат. Введите **целое число**.")
    except Exception as e:
        logger.error(f"Ошибка в обработчике process_goto_page_number: {e}")
        await message.answer("⚠️ Произошла ошибка при обработке номера страницы.")
        await state.clear() 

# Обработчик для кнопки "🔙 Назад" в инлайн клавиатурах
@router.callback_query(F.data == "back_to_admin")
async def back_from_deletion_inline(callback: CallbackQuery):
    if not await check_admin_access(callback): return
    await callback.message.edit_text("👨‍💻 Вы вернулись в админ-панель.", reply_markup=admin_main_menu())
    await callback.answer()

# Обработчик для кнопки "⬅️ Назад в админ панель" на Reply клавиатуре 
@router.message(F.text == "⬅️ Назад в админ панель")
async def back_to_admin_panel_message(message: Message):
    if not await check_admin_access(message): return
    await message.answer("👨‍💻 Вы вернулись в админ-панель.", reply_markup=admin_main_menu())