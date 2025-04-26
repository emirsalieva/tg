# handlers/admin_handler.py
from aiogram import Router, F, Bot # Импортируем Bot для аннотации типов
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from utils.pagination_admin import create_paginated_keyboard, ADMIN_DELETE_ITEMS_PER_PAGE
from keyboards.admin_keyboard import (
    admin_main_menu,
    manage_courses_keyboard,
    manage_resources_keyboard,
    manage_terms_keyboard,
    manage_groups_keyboard
)
from database.db_manager import (
    add_course, update_course, delete_course,
    add_resource, update_resource, delete_resource,
    add_term, update_term, delete_term,
    add_group, update_group, delete_group,
    # Важно: Убедитесь, что эти функции существуют в db_manager.py и работают как ожидается
    get_items_page, get_total_items_count
)
from dotenv import load_dotenv
import os
import logging
import math # Нужен для math.ceil

# ИСПРАВЛЕНО: ОПРЕДЕЛЯЕМ ЭКЗЕМПЛЯР ЛОГГЕРА РАНЬШЕ
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ИСПРАВЛЕНО: УДАЛЕН БЛОК try...except ImportError для импорта bot

load_dotenv()

# Создаем роутер
router = Router()

# Класс для управления состояниями FSM (остается без изменений)
class AdminStates(StatesGroup):
    # Состояния для добавления (общее для всех)
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_link = State()

    # --- СОСТОЯНИЕ ДЛЯ ПЕРЕХОДА ПО СТРАНИЦЕ ---
    waiting_for_goto_page_number = State()
    # --- КОНЕЦ ДОБАВЛЕННОГО СОСТОЯНИЯ ---

    # Состояния для редактирования (если реализовано, вам нужно будет их добавить)
    # ... (состояния для редактирования)


# Функция для проверки прав администратора (остается без изменений)
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


# --- Обработчики добавления элементов (остаются без изменений) ---

@router.message(F.text.in_(["➕ Добавить курс", "➕ Добавить ресурс", "➕ Добавить термин", "➕ Добавить группу"]))
async def add_entity_start(message: Message, state: FSMContext):
    if not await check_admin_access(message): return
    await state.set_data({"action": message.text})
    await state.set_state(AdminStates.waiting_for_name)
    await message.answer("📝 Введите название:", reply_markup=ReplyKeyboardRemove()) # Скрываем текущую Reply клавиатуру

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
            success = add_term(data["name"], data["description"]) # add_term(term, definition)
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

    if not link: # Или проверка на необязательность ссылки для группы, если нужно
         await message.answer("⚠️ Ссылка не может быть пустой для этого элемента. Попробуйте снова:")
         return

    name = data.get("name")
    description = data.get("description")

    try:
        success = False
        if action == "➕ Добавить курс":
            success = add_course(name, description, link) # add_course(name, desc, link)
        elif action == "➕ Добавить ресурс":
            success = add_resource(name, description, link) # add_resource(name, desc, link)
        elif action == "➕ Добавить группу":
             success = add_group(name, description, link) # add_group(name, desc, link)
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


# --- Обработчики начала удаления (теперь с пагинацией) ---

@router.message(F.text == "➖ Удалить курс")
async def delete_course_start(message: Message):
    if not await check_admin_access(message): return
    category = "course"
    # Получаем общее количество и элементы первой страницы из db_manager
    total_items = await get_total_items_count(category)
    current_page_items = await get_items_page(category, 1, ADMIN_DELETE_ITEMS_PER_PAGE)

    if not current_page_items and total_items > 0:
         # Если элементов нет на первой странице, но общее количество > 0, это странно.
         # Может быть, все элементы удалены только что? Возвращаемся в меню управления.
         await message.answer("ℹ️ Курсы отсутствуют или произошла ошибка загрузки.", reply_markup=manage_courses_keyboard())
         return
    elif not current_page_items and total_items == 0:
         await message.answer("ℹ️ Курсы отсутствуют.", reply_markup=manage_courses_keyboard()) # Или вернуться в меню управления курсами
         return

    # Используем функцию создания клавиатуры из pagination_utils
    keyboard = await create_paginated_keyboard(
        items=current_page_items,
        page=1,
        items_per_page=ADMIN_DELETE_ITEMS_PER_PAGE,
        total_items=total_items,
        pagination_callback_prefix=f"navigate_delete_{category}", # Префикс для навигации
        item_callback_prefix=f"del_{category}_by_id", # Префикс для удаления по ID
        item_id_index=0, # ID находится на позиции 0 в кортеже (id, name)
        item_name_index=1 # Имя находится на позиции 1 в кортеже (id, name)
        # add_button_callback и back_button_callback УДАЛЕНЫ
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
        item_id_index=0, # ID находится на позиции 0
        item_name_index=1, # Имя находится на позиции 1
        # add_button_callback и back_button_callback УДАЛЕНЫ
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

    # Для терминов, item_id_index и item_name_index оба 0, так как имя (термин) используется как ID
    keyboard = await create_paginated_keyboard(
        items=current_page_items,
        page=1,
        items_per_page=ADMIN_DELETE_ITEMS_PER_PAGE,
        total_items=total_items,
        pagination_callback_prefix=f"navigate_delete_{category}",
        item_callback_prefix=f"del_{category}_by_name", # Удаление по имени
        item_id_index=0, # Имя (термин) находится на позиции 0
        item_name_index=0, # Имя (термин) находится на позиции 0
        # add_button_callback и back_button_callback УДАЛЕНЫ
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
        item_id_index=0, # ID находится на позиции 0
        item_name_index=1, # Имя находится на позиции 1
        # add_button_callback и back_button_callback УДАЛЕНЫ
    )
    await message.answer("🗑️ Выберите группу для удаления:", reply_markup=keyboard)


# --- Обработчики удаления элементов (обновляют страницу после удаления) ---

# Важно: callback_data для удаления элемента включает номер текущей страницы:
# [item_callback_prefix]:[item_identifier]:page:[номер_страницы]
# Пример: del_course_by_id:123:page:5

@router.callback_query(F.data.startswith("del_course_by_id:"))
async def handle_delete_course_by_id(callback: CallbackQuery):
    if not await check_admin_access(callback): return
    category = "course"
    try:
        # Извлекаем ID и номер страницы из callback_data
        parts = callback.data.split(":")
        course_id = int(parts[1])
        # Проверяем, достаточно ли частей в callback_data перед попыткой извлечь номер страницы
        current_page = 1 # По умолчанию страница 1, если нет информации
        if len(parts) > 3 and parts[2] == 'page':
             current_page = int(parts[3])


        success = delete_course(course_id) # Удаление по ID

        if success:
            await callback.answer(f"Курс (ID: {course_id}) успешно удален!", show_alert=True)

            # После успешного удаления, обновляем текущую страницу
            # Получаем актуальное количество элементов и данные для текущей страницы
            total_items = await get_total_items_count(category)
            total_pages = math.ceil(total_items / ADMIN_DELETE_ITEMS_PER_PAGE) if total_items > 0 else 1 # Минимум 1 страница

            # Определяем целевую страницу после удаления (остаемся на текущей или переходим на предыдущую)
            target_page = current_page
            # Если текущая страница стала пустой после удаления последнего элемента на ней
            if total_items > 0 and target_page > total_pages:
                 target_page = total_pages # Переходим на последнюю страницу, если текущая стала несуществующей
            # Если после перехода на предыдущую страница все равно пуста (маловероятно при корректном расчете)
            if target_page < 1 and total_items > 0: target_page = 1
            if total_items == 0: target_page = 1 # Если все удалено, остаемся на "странице 1" (пустой список)


            current_page_items = await get_items_page(category, target_page, ADMIN_DELETE_ITEMS_PER_PAGE)

            # Проверяем, есть ли элементы на целевой странице
            if not current_page_items and total_items > 0:
                 # Если элементов нет, но общее количество > 0 (маловероятно после корректного расчета)
                 # Переходим в меню управления категорией, т.к. список пуст (или страница пуста)
                 from keyboards.admin_keyboard import manage_courses_keyboard # Импортируем клавиатуру меню
                 await callback.message.edit_text("ℹ️ Курсы отсутствуют.", reply_markup=manage_courses_keyboard())

            elif not current_page_items and total_items == 0:
                  # Если все элементы удалены
                  from keyboards.admin_keyboard import manage_courses_keyboard
                  await callback.message.edit_text("ℹ️ Курсы отсутствуют.", reply_markup=manage_courses_keyboard())
            else:
                 # Есть элементы на целевой странице, обновляем клавиатуру для нее
                 keyboard = await create_paginated_keyboard(
                     items=current_page_items,
                     page=target_page,
                     items_per_page=ADMIN_DELETE_ITEMS_PER_PAGE,
                     total_items=total_items,
                     pagination_callback_prefix=f"navigate_delete_{category}",
                     item_callback_prefix=f"del_{category}_by_id",
                     item_id_index=0, item_name_index=1,
                     # add_button_callback и back_button_callback УДАЛЕНЫ
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
        # Извлекаем ID и номер страницы
        parts = callback.data.split(":")
        resource_id = int(parts[1])
        current_page = 1
        if len(parts) > 3 and parts[2] == 'page':
             current_page = int(parts[3])

        success = delete_resource(resource_id) # Удаление по ID

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
                     # add_button_callback и back_button_callback УДАЛЕНЫ
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
        # Извлекаем имя и номер страницы
        parts = callback.data.split(":")
        term_name = parts[1]
        current_page = 1
        if len(parts) > 3 and parts[2] == 'page':
             current_page = int(parts[3])

        success = delete_term(term_name) # Удаление по имени

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
                     item_id_index=0, item_name_index=0, # Для терминов оба 0
                     # add_button_callback и back_button_callback УДАЛЕНЫ
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
        # Извлекаем ID и номер страницы
        parts = callback.data.split(":")
        group_id = int(parts[1])
        current_page = 1
        if len(parts) > 3 and parts[2] == 'page':
             current_page = int(parts[3])

        success = delete_group(group_id) # Удаление по ID

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
                     # add_button_callback и back_button_callback УДАЛЕНЫ
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


# --- ДОБАВЛЕН ОБРАБОТЧИК ДЛЯ КНОПКИ "ПЕРЕЙТИ НА СТРАНИЦУ" (callback) ---
# ДОБАВЛЕН ДЕКОРАТОР @router.callback_query
@router.callback_query(F.data.startswith("goto_delete_page:"))
# ИСПРАВЛЕНО: ДОБАВЛЕН bot: Bot В АРГУМЕНТЫ ФУНКЦИИ
async def ask_for_page_number(callback: CallbackQuery, state: FSMContext, bot: Bot):
    # Проверка прав администратора
    if not await check_admin_access(callback): return

    try:
        category = callback.data.split(":")[1] # Извлекаем категорию

        # Устанавливаем состояние FSM и сохраняем категорию и ID сообщения для последующего редактирования
        await state.set_state(AdminStates.waiting_for_goto_page_number)
        await state.update_data(goto_category=category, original_message_id=callback.message.message_id, chat_id=callback.message.chat.id)

        # Редактируем сообщение, чтобы запросить номер страницы, используя bot из аргументов
        await bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text="🔢 Введите номер страницы:")
        await callback.answer()

    except IndexError:
        logger.error(f"Неверный формат callback_data для goto_delete_page: {callback.data}")
        await callback.answer("⚠️ Ошибка: Неверный запрос страницы.", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка при обработке goto_delete_page: {e}")
        await callback.answer("⚠️ Произошла ошибка.", show_alert=True)
# --- КОНЕЦ ДОБАВЛЕННОГО ОБРАБОТЧИКА ---


# --- ДОБАВЛЕН ОБРАБОТЧИК ДЛЯ FSM состояния ввода номера страницы (message) ---
# ДОБАВЛЕН ДЕКОРАТОР @router.message
# ИСПОЛЬЗУЕМ ОБЪЕКТ СОСТОЯНИЯ В StateFilter
@router.message(StateFilter(AdminStates.waiting_for_goto_page_number))
# ИСПРАВЛЕНО: ДОБАВЛЕН bot: Bot В АРГУМЕНТЫ ФУНКЦИИ
async def process_goto_page_number(message: Message, state: FSMContext, bot: Bot):
    # Проверка прав администратора также нужна в обработчике сообщений в состоянии FSM
    if not await check_admin_access(message):
        await state.clear() # Очищаем состояние, если пользователь не админ
        return

    try:
        page_number_str = message.text.strip()
        page = int(page_number_str) # Пытаемся преобразовать ввод в целое число

        data = await state.get_data()
        category = data.get("goto_category")
        original_message_id = data.get("original_message_id")
        chat_id = data.get("chat_id")

        # Проверяем, что данные состояния корректны
        if not category or original_message_id is None or chat_id is None:
             logger.error("Состояние FSM для goto_page не содержит нужных данных.")
             await message.answer("⚠️ Ошибка состояния. Попробуйте снова.")
             await state.clear() # Очищаем состояние при ошибке данных
             return

        # Получаем общее количество элементов для валидации номера страницы
        total_items = await get_total_items_count(category)
        total_pages = math.ceil(total_items / ADMIN_DELETE_ITEMS_PER_PAGE) if total_items > 0 else 1 # Минимум 1 страница, если есть хоть 1 элемент

        # Валидация номера страницы
        if page < 1 or page > total_pages:
            await message.answer(f"⚠️ Неверный номер страницы. Введите число от 1 до {total_pages}:")
            return # Остаемся в текущем состоянии, ждем корректный ввод

        # Получаем элементы для запрошенной страницы
        items = await get_items_page(category, page, ADMIN_DELETE_ITEMS_PER_PAGE)

        # Хотя валидация выше должна исключить этот случай, добавим проверку
        if not items and total_items > 0:
             logger.warning(f"Запрошена страница {page}, но список пуст при total_items > 0 для категории {category}")
             await message.answer("⚠️ На запрошенной странице нет элементов. Попробуйте другой номер.")
             return # Остаемся в состоянии, ждем другой ввод
        elif not items and total_items == 0:
             # Все элементы удалены, пока пользователь был в состоянии FSM
             empty_message = f"ℹ️ {category.capitalize()} отсутствуют."
             if category == "course": empty_message = "ℹ️ Курсы отсутствуют."
             elif category == "resource": empty_message = "ℹ️ Ресурсы отсутствуют."
             elif category == "term": empty_message = "ℹ️ Термины отсутствуют."
             elif category == "group": empty_message = "ℹ️ Группы отсутствуют."

             # Редактируем оригинальное сообщение, чтобы показать состояние отсутствия элементов, используя bot из аргументов
             try:
                 await bot.edit_message_text(chat_id=chat_id, message_id=original_message_id, text=empty_message, reply_markup=None)
                 await message.answer("ℹ️ Элементы отсутствуют.") # Отвечаем на сообщение пользователя с номером страницы
             except Exception as e:
                 logger.error(f"Ошибка при редактировании оригинального сообщения после удаления всех элементов: {e}")
                 await message.answer("ℹ️ Элементы отсутствуют.") # Просто отвечаем пользователю

             await state.clear() # Очищаем состояние
             return


        # Определяем индексы ID и имени для создания кнопок элементов
        item_id_index = 0 # По умолчанию ID первый
        item_name_index = 1 # По умолчанию имя второй
        item_callback_prefix_base = f"del_{category}_by_id" # По умолчанию удаление по ID

        if category == "term":
            item_id_index = 0 # Для терминов имя (термин) первый и используется как ID
            item_name_index = 0 # Отображаем тоже имя
            item_callback_prefix_base = "del_term_by_name" # Удаление по имени

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
            # add_button_callback и back_button_callback УДАЛЕНЫ
        )

        # Редактируем оригинальное сообщение, чтобы показать запрошенную страницу с клавиатурой, используя bot из аргументов
        message_text = f"🗑️ Выберите {category.capitalize()} для удаления:"
        if category == "course": message_text = "🗑️ Выберите курс для удаления:"
        elif category == "resource": message_text = "🗑️ Выберите ресурс для удаления:"
        elif category == "term": message_text = "🗑️ Выберите термин для удаления:"
        elif category == "group": message_text = "🗑️ Выберите группу для удаления:"

        try:
            await bot.edit_message_text(chat_id=chat_id, message_id=original_message_id, text=message_text, reply_markup=keyboard)
            # Также удаляем сообщение пользователя с номером страницы, используя bot из аргументов
            await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
        except Exception as e:
             logger.error(f"Ошибка при редактировании оригинального сообщения для показа страницы {page}: {e}")
             await message.answer("⚠️ Произошла ошибка при обновлении страницы.")
             # Если редактирование не удалось, можно отправить новое сообщение
             # await message.answer(message_text, reply_markup=keyboard)


        await state.clear() # Очищаем состояние после успешного перехода

    except ValueError:
        # Ввод пользователя не является целым числом
        data = await state.get_data()
        category = data.get("goto_category", "элементов") # Получаем категорию для корректного подсчета страниц
        # В этом месте также нужен get_total_items_count, чтобы сообщить пользователю правильный диапазон страниц
        try:
             total_items = await get_total_items_count(category)
             total_pages = math.ceil(total_items / ADMIN_DELETE_ITEMS_PER_PAGE) if total_items > 0 else 1
             await message.answer(f"⚠️ Неверный формат. Введите **целое число** от 1 до {total_pages}:")
        except Exception as e:
             logger.error(f"Ошибка при получении total_items для валидации в catch ValueError: {e}")
             await message.answer("⚠️ Неверный формат. Введите **целое число**.")

        # Остаемся в состоянии, ждем корректный ввод
    except Exception as e:
        logger.error(f"Ошибка в обработчике process_goto_page_number: {e}")
        await message.answer("⚠️ Произошла ошибка при обработке номера страницы.")
        await state.clear() # Очищаем состояние при неожиданной ошибке

# --- Конец обработчика для FSM состояния ввода номера страницы ---


# --- Обработчики "Назад" (остаются без изменений) ---

# Обработчик для кнопки "🔙 Назад" в инлайн клавиатурах
@router.callback_query(F.data == "back_to_admin")
async def back_from_deletion_inline(callback: CallbackQuery):
    if not await check_admin_access(callback): return
    # Редактируем сообщение с клавиатурой, чтобы показать основное меню админки
    await callback.message.edit_text("👨‍💻 Вы вернулись в админ-панель.", reply_markup=admin_main_menu())
    await callback.answer() # Не забываем ответить на callback

# Обработчик для кнопки "⬅️ Назад в админ панель" на Reply клавиатуре (если используется)
@router.message(F.text == "⬅️ Назад в админ панель")
async def back_to_admin_panel_message(message: Message):
    if not await check_admin_access(message): return
    await message.answer("👨‍💻 Вы вернулись в админ-панель.", reply_markup=admin_main_menu())