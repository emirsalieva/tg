import math
import logging
from ssl import SSLContext
from typing import List, Tuple, Any
from aiogram import Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

logger = logging.getLogger(__name__)

ADMIN_DELETE_ITEMS_PER_PAGE = 10

async def create_paginated_keyboard(
    items: List[Tuple], 
    page: int, 
    items_per_page: int, 
    total_items: int, 
    pagination_callback_prefix: str, 
    item_callback_prefix: str, 
    item_id_index: int, 
    item_name_index: int, 
    row_width: int = 2
) -> InlineKeyboardMarkup:

    all_rows = []
    item_buttons = []

    total_pages = math.ceil(total_items / items_per_page)

    for item in items:
        item_identifier = item[item_id_index]
        button_text = item[item_name_index]
        callback_data = f"{item_callback_prefix}:{item_identifier}:page:{page}"

        if len(callback_data.encode('utf-8')) > 64:
            logger.warning(f"Длинная callback_data для '{button_text}' ({item_callback_prefix}): {callback_data} ({len(callback_data.encode('utf-8'))} bytes). Возможны проблемы.")

        item_buttons.append(InlineKeyboardButton(text=f"❌ {button_text}", callback_data=callback_data)) 
    for i in range(0, len(item_buttons), row_width):
        all_rows.append(item_buttons[i : i + row_width])

    # Добавляем кнопки пагинации
    navigation_buttons = []
    if page > 1:
        navigation_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"{pagination_callback_prefix}:{page - 1}"))

    if total_pages > 0:
        navigation_buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="ignore_page_info")) # Изменено на ignore_page_info

    if page < total_pages:
        navigation_buttons.append(InlineKeyboardButton(text="➡️ Далее", callback_data=f"{pagination_callback_prefix}:{page + 1}"))

    if navigation_buttons:
        all_rows.append(navigation_buttons) 

    category = pagination_callback_prefix.replace("navigate_delete_", "")
    all_rows.append([InlineKeyboardButton(text="🔢 Перейти на страницу", callback_data=f"goto_delete_page:{category}")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=all_rows)

    return keyboard

# --- Функции для регистрации обработчиков пагинации (добавляется обработчик для goto_delete_page) ---

def register_pagination_handlers(router: Router, check_admin_access_func, get_items_page_func, get_total_items_count_func):

    @router.callback_query(F.data.startswith("navigate_delete_"))
    async def navigate_delete_page(callback: CallbackQuery):
        if not await check_admin_access_func(callback): return

        try:
            parts = callback.data.split(":")
            pagination_prefix = parts[0] 
            category = pagination_prefix.replace("navigate_delete_", "")
            page_data = parts[1] 

            if page_data == "current_page_info":
                 await callback.answer("Вы на текущей странице.", show_alert=False)
                 return


            page = int(page_data) 

            total_items = await get_total_items_count_func(category)
            total_pages = math.ceil(total_items / ADMIN_DELETE_ITEMS_PER_PAGE)

            if page < 1 or (total_pages > 0 and page > total_pages) or (total_pages == 0 and page != 1):
                 await callback.answer("Неверный номер страницы.")
                 return

            items = await get_items_page_func(category, page, ADMIN_DELETE_ITEMS_PER_PAGE)

            if not items and total_items > 0:
                 if total_pages > 0:
                      last_valid_page = total_pages
                      if last_valid_page < 1: last_valid_page = 1 
                      last_page_callback_data = f"navigate_delete_{category}:{last_valid_page}"
                      new_callback = CallbackQuery(id=callback.id, from_user=callback.from_user, chat_instance=callback.chat_instance, data=last_page_callback_data, inline_message_id=callback.inline_message_id, message=callback.message) # Создаем новый CallbackQuery
                      await router.process_update(new_callback.update)
                      return
                 
                 empty_message = f"ℹ️ {category.capitalize()} отсутствуют."
                 if category == "course": empty_message = "ℹ️ Курсы отсутствуют."
                 elif category == "resource": empty_message = "ℹ️ Ресурсы отсутствуют."
                 elif category == "term": empty_message = "ℹ️ Термины отсутствуют."
                 elif category == "group": empty_message = "ℹ️ Группы отсутствуют."

                 from keyboards.admin_keyboard import manage_courses_keyboard, manage_resources_keyboard, manage_terms_keyboard, manage_groups_keyboard, admin_main_menu # Импортируем клавиатуры меню

                 reply_kb = None
                 message_text = f"ℹ️ {category.capitalize()} отсутствуют."
                 if category == "course":
                     reply_kb = manage_courses_keyboard()
                     message_text = "ℹ️ Курсы отсутствуют."
                 elif category == "resource":
                      reply_kb = manage_resources_keyboard()
                      message_text = "ℹ️ Ресурсы отсутствуют."
                 elif category == "term":
                      reply_kb = manage_terms_keyboard()
                      message_text = "ℹ️ Термины отсутствуют."
                 elif category == "group":
                      reply_kb = manage_groups_keyboard()
                      message_text = "ℹ️ Группы отсутствуют."

                 if reply_kb:
                    await callback.message.edit_text(message_text, reply_markup=reply_kb)
                 else:
                    await callback.message.edit_text("ℹ️ Элементы отсутствуют.", reply_markup=admin_main_menu())

                 await callback.answer("Все элементы удалены.")
                 return


            # Определяем индексы ID и имени для создания кнопок элементов
            item_id_index = 0 
            item_name_index = 1 
            item_callback_prefix_base = f"del_{category}_by_id" 

            if category == "term":
                item_id_index = 0 
                item_name_index = 0 
                item_callback_prefix_base = "del_term_by_name" 

            # Создаем новую клавиатуру для текущей страницы
            keyboard = await create_paginated_keyboard(
                items=items,
                page=page,
                items_per_page=ADMIN_DELETE_ITEMS_PER_PAGE,
                total_items=total_items,
                pagination_callback_prefix=pagination_prefix,
                item_callback_prefix=item_callback_prefix_base, 
                item_id_index=item_id_index,
                item_name_index=item_name_index,
            )
            message_text = f"🗑️ Выберите {category.capitalize()} для удаления:"
            if category == "course": message_text = "🗑️ Выберите курс для удаления:"
            elif category == "resource": message_text = "🗑️ Выберите ресурс для удаления:"
            elif category == "term": message_text = "🗑️ Выберите термин для удаления:"
            elif category == "group": message_text = "🗑️ Выберите группу для удаления:"

            await callback.message.edit_text(message_text, reply_markup=keyboard)
            await callback.answer()

        except ValueError:
            logger.error(f"Неверный формат номера страницы в callback_data навигации: {callback.data}")
            await callback.answer("⚠️ Ошибка: Неверный формат номера страницы.", show_alert=True)
        except Exception as e:
            logger.error(f"Ошибка в обработчике навигации ({category}, page {page_data}): {e}")
            await callback.answer("⚠️ Произошла ошибка при загрузке страницы.", show_alert=True)

    # --- ОБРАБОТЧИК ДЛЯ КНОПКИ "ПЕРЕЙТИ НА СТРАНИЦУ" ---
    @router.callback_query(F.data.startswith("goto_delete_page:"))
    async def ask_for_page_number(callback: CallbackQuery, state: SSLContext):
        if not await check_admin_access_func(callback): 
            return

        try:
            category = callback.data.split(":")[1] 

            # Устанавливаем состояние FSM и сохраняем категорию и ID сообщения для последующего редактирования
            await state.set_state("handlers.admin_handler:AdminStates.waiting_for_goto_page_number") 
            await state.update_data(goto_category=category, original_message_id=callback.message.message_id, chat_id=callback.message.chat.id)

            await callback.message.edit_text("🔢 Введите номер страницы:")
            await callback.answer()

        except IndexError:
            logger.error(f"Неверный формат callback_data для goto_delete_page: {callback.data}")
            await callback.answer("⚠️ Ошибка: Неверный запрос страницы.", show_alert=True)
        except Exception as e:
            logger.error(f"Ошибка при обработке goto_delete_page: {e}")
            await callback.answer("⚠️ Произошла ошибка.", show_alert=True)
