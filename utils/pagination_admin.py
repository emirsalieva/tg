# pagination_utils.py
import math
import logging
from ssl import SSLContext
from typing import List, Tuple, Any
from aiogram import Router, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

logger = logging.getLogger(__name__)

# КОНСТАНТА: Количество элементов на странице удаления в админ-панели
ADMIN_DELETE_ITEMS_PER_PAGE = 10

async def create_paginated_keyboard(
    items: List[Tuple], # Список элементов для текущей страницы
    page: int, # Номер текущей страницы (начиная с 1)
    items_per_page: int, # Количество элементов на странице
    total_items: int, # Общее количество элементов
    pagination_callback_prefix: str, # Префикс для callback_data кнопок пагинации (например, "navigate_delete_course")
    item_callback_prefix: str, # Префикс для callback_data кнопок самих элементов (например, "del_course_by_id")
    item_id_index: int, # Индекс элемента в кортеже items, который является ID (для большинства)
    item_name_index: int, # Индекс элемента в кортеже items, который является именем для отображения
    row_width: int = 2 # Количество кнопок элементов в ряду
) -> InlineKeyboardMarkup:
    """
    Создает инлайн клавиатуру с кнопками элементов текущей страницы и кнопками пагинации,
    включая кнопку "Перейти на страницу".
    callback_data для кнопок элементов: [item_callback_prefix]:[item_identifier]:page:[current_page]
    callback_data для кнопки "Перейти на страницу": goto_delete_page:[category]
    """
    all_rows = []
    item_buttons = []

    total_pages = math.ceil(total_items / items_per_page)

    for item in items:
        item_identifier = item[item_id_index]
        button_text = item[item_name_index]

        # Формируем callback_data для кнопки элемента, включая номер текущей страницы
        callback_data = f"{item_callback_prefix}:{item_identifier}:page:{page}"

        # Проверка длины callback_data (важно!)
        if len(callback_data.encode('utf-8')) > 64:
            logger.warning(f"Длинная callback_data для '{button_text}' ({item_callback_prefix}): {callback_data} ({len(callback_data.encode('utf-8'))} bytes). Возможны проблемы.")

        item_buttons.append(InlineKeyboardButton(text=f"❌ {button_text}", callback_data=callback_data)) # Добавляем эмодзи "❌" для удаления

    # Группируем кнопки элементов по row_width и добавляем их как ряды в all_rows
    for i in range(0, len(item_buttons), row_width):
        all_rows.append(item_buttons[i : i + row_width])

    # Добавляем кнопки пагинации
    navigation_buttons = []
    if page > 1:
        navigation_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"{pagination_callback_prefix}:{page - 1}"))

    if total_pages > 0:
        # Кнопка с номером текущей страницы (ignore или уникальный для инфо)
        # Используем ignore, чтобы кнопка не вызывала callback query
        navigation_buttons.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="ignore_page_info")) # Изменено на ignore_page_info

    if page < total_pages:
        navigation_buttons.append(InlineKeyboardButton(text="➡️ Далее", callback_data=f"{pagination_callback_prefix}:{page + 1}"))

    if navigation_buttons:
        all_rows.append(navigation_buttons) # Добавляем ряд с кнопками пагинации в all_rows

    # --- ДОБАВЛЕНА КНОПКА "ПЕРЕЙТИ НА СТРАНИЦУ" ---
    # Определяем категорию из префикса пагинации для callback_data кнопки "Перейти на страницу"
    category = pagination_callback_prefix.replace("navigate_delete_", "")
    all_rows.append([InlineKeyboardButton(text="🔢 Перейти на страницу", callback_data=f"goto_delete_page:{category}")])
    # --- КОНЕЦ ДОБАВЛЕННОЙ КНОПКИ ---

    # КНОПКИ "ДОБАВИТЬ" И "НАЗАД В АДМИН ПАНЕЛЬ" УДАЛЕНЫ ИЗ ЭТОЙ КЛАВИАТУРЫ

    # Правильно создаем InlineKeyboardMarkup, передавая ей собранный список рядов
    keyboard = InlineKeyboardMarkup(inline_keyboard=all_rows)

    return keyboard

# --- Функции для регистрации обработчиков пагинации (добавляется обработчик для goto_delete_page) ---

def register_pagination_handlers(router: Router, check_admin_access_func, get_items_page_func, get_total_items_count_func):
    """
    Регистрирует обработчики для кнопок навигации по страницам и кнопки "Перейти на страницу".
    Принимает функции проверки прав, получения данных страницы и общего количества извне.
    """

    @router.callback_query(F.data.startswith("navigate_delete_"))
    async def navigate_delete_page(callback: CallbackQuery):
        if not await check_admin_access_func(callback): return

        try:
            parts = callback.data.split(":")
            pagination_prefix = parts[0] # например, "navigate_delete_course"
            category = pagination_prefix.replace("navigate_delete_", "") # Извлекаем "course", "resource" и т.д.
            page_data = parts[1] # номер страницы или "current_page_info"

            if page_data == "current_page_info":
                 # Обработка нажатия на кнопку с номером текущей страницы (callback_data="ignore_page_info")
                 # Эта кнопка теперь не интерактивна, но обработчик все равно может сработать если старый callback_data
                 # был navigate_delete_*:current_page_info. Отвечаем на всякий случай.
                 await callback.answer("Вы на текущей странице.", show_alert=False)
                 return


            page = int(page_data) # Преобразуем номер страницы в число

            total_items = await get_total_items_count_func(category)
            total_pages = math.ceil(total_items / ADMIN_DELETE_ITEMS_PER_PAGE)

            # Проверка на корректный номер страницы
            if page < 1 or (total_pages > 0 and page > total_pages) or (total_pages == 0 and page != 1):
                 await callback.answer("Неверный номер страницы.")
                 return

            items = await get_items_page_func(category, page, ADMIN_DELETE_ITEMS_PER_PAGE)

            # Если на запрошенной странице нет элементов, но общее количество > 0
            if not items and total_items > 0:
                 if total_pages > 0:
                      # Перенаправить на последнюю действительную страницу
                      last_valid_page = total_pages
                      if last_valid_page < 1: last_valid_page = 1 # Минимальная страница 1
                      last_page_callback_data = f"navigate_delete_{category}:{last_valid_page}"
                      # Создаем искусственный callback_data и передаем его обработчику
                      new_callback = CallbackQuery(id=callback.id, from_user=callback.from_user, chat_instance=callback.chat_instance, data=last_page_callback_data, inline_message_id=callback.inline_message_id, message=callback.message) # Создаем новый CallbackQuery
                      await router.process_update(new_callback.update) # Обрабатываем обновленный callback
                      return
                 # Если total_pages стало 0 после удаления или ошибка логики
                 empty_message = f"ℹ️ {category.capitalize()} отсутствуют."
                 if category == "course": empty_message = "ℹ️ Курсы отсутствуют."
                 elif category == "resource": empty_message = "ℹ️ Ресурсы отсутствуют."
                 elif category == "term": empty_message = "ℹ️ Термины отсутствуют."
                 elif category == "group": empty_message = "ℹ️ Группы отсутствуют."

                 # Внимание: Если элементы удалены, нужно вернуться в предыдущее меню
                 # Эта клавиатура не содержит кнопки "Назад в админ панель".
                 # Возвращаемся в меню управления конкретной категорией или в главное меню админки
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

                 # Если все элементы удалены, редактируем сообщение на текст "Отсутствуют" и показываем меню управления категорией
                 if reply_kb:
                    await callback.message.edit_text(message_text, reply_markup=reply_kb)
                 else:
                    # Если не смогли определить меню управления, возвращаемся в главное админ меню
                    await callback.message.edit_text("ℹ️ Элементы отсутствуют.", reply_markup=admin_main_menu())

                 await callback.answer("Все элементы удалены.")
                 return


            # Определяем индексы ID и имени для создания кнопок элементов
            item_id_index = 0 # По умолчанию ID первый
            item_name_index = 1 # По умолчанию имя второй
            item_callback_prefix_base = f"del_{category}_by_id" # По умолчанию удаление по ID

            if category == "term":
                item_id_index = 0 # Для терминов имя (термин) первый и используется как ID
                item_name_index = 0 # Отображаем тоже имя
                item_callback_prefix_base = "del_term_by_name" # Удаление по имени

            # Создаем новую клавиатуру для текущей страницы
            keyboard = await create_paginated_keyboard(
                items=items,
                page=page,
                items_per_page=ADMIN_DELETE_ITEMS_PER_PAGE,
                total_items=total_items,
                pagination_callback_prefix=pagination_prefix,
                item_callback_prefix=item_callback_prefix_base, # Используем префикс действия над элементом
                item_id_index=item_id_index,
                item_name_index=item_name_index,
                # Аргументы для кнопок "Добавить" и "Назад" УДАЛЕНЫ
            )
            # Редактируем сообщение, заменяя старую клавиатуру на новую
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

    # --- ДОБАВЛЕН ОБРАБОТЧИК ДЛЯ КНОПКИ "ПЕРЕЙТИ НА СТРАНИЦУ" ---
    @router.callback_query(F.data.startswith("goto_delete_page:"))
    async def ask_for_page_number(callback: CallbackQuery, state: SSLContext):
        # Проверка прав администратора
        if not await check_admin_access_func(callback): return

        try:
            category = callback.data.split(":")[1] # Извлекаем категорию

            # Устанавливаем состояние FSM и сохраняем категорию и ID сообщения для последующего редактирования
            await state.set_state("handlers.admin_handler:AdminStates.waiting_for_goto_page_number") # Указываем полное имя состояния, т.к. FSMState определен в другом файле
            await state.update_data(goto_category=category, original_message_id=callback.message.message_id, chat_id=callback.message.chat.id)

            # Редактируем сообщение, чтобы запросить номер страницы
            await callback.message.edit_text("🔢 Введите номер страницы:")
            await callback.answer()

        except IndexError:
            logger.error(f"Неверный формат callback_data для goto_delete_page: {callback.data}")
            await callback.answer("⚠️ Ошибка: Неверный запрос страницы.", show_alert=True)
        except Exception as e:
            logger.error(f"Ошибка при обработке goto_delete_page: {e}")
            await callback.answer("⚠️ Произошла ошибка.", show_alert=True)
    # --- КОНЕЦ ДОБАВЛЕННОГО ОБРАБОТЧИКА ---