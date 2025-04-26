import sqlite3
import os
from typing import List, Tuple, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_NAME = "bot.db"

def get_db_connection():
    """Создает и возвращает соединение с базой данных"""
    conn = sqlite3.connect(DB_NAME)
    return conn

def init_db():
    """Инициализирует базу данных и создает таблицы"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Создание таблицы курсов
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL,
            link TEXT NOT NULL
        )
        """)

        # Создание таблицы ресурсов
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL,
            link TEXT NOT NULL
        )
        """)

        # Создание таблицы терминов
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS terms (
            term TEXT PRIMARY KEY, -- Термин как первичный ключ (строка)
            definition TEXT NOT NULL
        )
        """)

        # Создание таблицы групп
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE, -- Используем 'name' как уникальное имя группы
            description TEXT NOT NULL,
            link TEXT NOT NULL -- Предполагаем, что группа тоже может иметь ссылку
        )
        """)

        conn.commit()
        logger.info("Таблицы проверены/созданы.")
    except sqlite3.Error as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
    finally:
        if conn:
            conn.close()

# --- Функции для Курсов ---

def add_course(name: str, description: str, link: str) -> bool:
    """Добавляет курс в базу данных"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO courses (name, description, link) VALUES (?, ?, ?)",
                (name, description, link)
            )
            conn.commit()
            logger.info(f"Курс '{name}' добавлен.")
            return True
    except sqlite3.IntegrityError:
        logger.warning(f"Попытка добавить существующий курс: '{name}'")
        return False # Курс с таким именем уже существует
    except sqlite3.Error as e:
        logger.error(f"Ошибка добавления курса '{name}': {e}")
        return False

def update_course(course_id: int, new_description: str, new_link: str) -> bool:
    """Обновляет описание и ссылку курса по его ID."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE courses SET description = ?, link = ? WHERE id = ?",
                           (new_description, new_link, course_id))
            conn.commit()
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Курс с ID {course_id} обновлен.")
            else:
                logger.warning(f"Курс с ID {course_id} не найден для обновления.")
            return success
    except sqlite3.Error as e:
        logger.error(f"Ошибка при обновлении курса с ID {course_id}: {e}")
        return False

# ИЗМЕНЕНО: Удаление курса по ID
def delete_course(course_id: int) -> bool:
    """Удаляет курс из базы данных по его ID."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM courses WHERE id = ?", (course_id,))
            conn.commit()
            success = cursor.rowcount > 0 # Проверяем, была ли удалена хотя бы одна строка
            if success:
                logger.info(f"Курс с ID {course_id} удален.")
            else:
                logger.warning(f"Курс с ID {course_id} не найден для удаления.")
            return success
    except sqlite3.Error as e:
        logger.error(f"Ошибка при удалении курса с ID {course_id}: {e}")
        return False

# ИЗМЕНЕНО: Получение всех курсов (ID первым, затем имя, описание, ссылка)
def get_all_courses() -> List[Tuple[int, str, Any, Any]]: # ID (int) первым, затем имя (str)
    """Возвращает список всех курсов (id, имя, описание, ссылка)."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Выбираем ID первым, затем имя!
            cursor.execute("SELECT id, name, description, link FROM courses")
            courses = cursor.fetchall()
            return courses # Возвращаем список кортежей (id, name, description, link)
    except sqlite3.Error as e:
        logger.error(f"Ошибка при получении всех курсов: {e}")
        return []

# --- Функции для Ресурсов ---

def add_resource(name: str, description: str, link: str) -> bool:
    """Добавляет новый ресурс в базу данных."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO resources (name, description, link) VALUES (?, ?, ?)",
                (name, description, link)
            )
            conn.commit()
            logger.info(f"Ресурс '{name}' добавлен.")
            return True
    except sqlite3.IntegrityError:
        logger.warning(f"Попытка добавить существующий ресурс: '{name}'")
        return False # Ресурс с таким именем уже существует
    except sqlite3.Error as e:
        logger.error(f"Ошибка при добавлении ресурса '{name}': {e}")
        return False

def update_resource(resource_id: int, new_description: str, new_link: str) -> bool:
    """Обновляет описание и ссылку ресурса по его ID."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE resources SET description = ?, link = ? WHERE id = ?",
                           (new_description, new_link, resource_id))
            conn.commit()
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Ресурс с ID {resource_id} обновлен.")
            else:
                logger.warning(f"Ресурс с ID {resource_id} не найден для обновления.")
            return success
    except sqlite3.Error as e:
        logger.error(f"Ошибка при обновлении ресурса с ID {resource_id}: {e}")
        return False

# ИЗМЕНЕНО: Удаление ресурса по ID
def delete_resource(resource_id: int) -> bool:
    """Удаляет ресурс из базы данных по его ID."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM resources WHERE id = ?", (resource_id,))
            conn.commit()
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Ресурс с ID {resource_id} удален.")
            else:
                logger.warning(f"Ресурс с ID {resource_id} не найден для удаления.")
            return success
    except sqlite3.Error as e:
        logger.error(f"Ошибка при удалении ресурса с ID {resource_id}: {e}")
        return False

# ИЗМЕНЕНО: Получение всех ресурсов (ID первым, затем имя, описание, ссылка)
def get_all_resources() -> List[Tuple[int, str, Any, Any]]: # ID (int) первым, затем имя (str)
    """Возвращает список всех ресурсов (id, имя, описание, ссылка)."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Выбираем ID первым, затем имя!
            cursor.execute("SELECT id, name, description, link FROM resources")
            resources = cursor.fetchall()
            return resources # Возвращаем список кортежей (id, name, description, link)
    except sqlite3.Error as e:
        logger.error(f"Ошибка при получении всех ресурсов: {e}")
        return []

# --- Функции для Терминов ---

def add_term(term: str, definition: str) -> bool:
    """Добавляет термин в базу данных."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO terms (term, definition) VALUES (?, ?)",
                (term, definition)
            )
            conn.commit()
            logger.info(f"Термин '{term}' добавлен.")
            return True
    except sqlite3.IntegrityError:
        logger.warning(f"Попытка добавить существующий термин: '{term}'")
        return False # Термин с таким именем уже существует
    except sqlite3.Error as e:
        logger.error(f"Ошибка добавления термина '{term}': {e}")
        return False

def update_term(term: str, new_definition: str) -> bool:
    """Обновляет определение термина по его названию."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE terms SET definition = ? WHERE term = ?",
                           (new_definition, term))
            conn.commit()
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Термин '{term}' обновлен.")
            else:
                logger.warning(f"Термин '{term}' не найден для обновления.")
            return success
    except sqlite3.Error as e:
        logger.error(f"Ошибка при обновлении термина '{term}': {e}")
        return False

# Функция удаления термина (по имени, т.к. оно первичный ключ)
def delete_term(term: str) -> bool:
    """Удаляет термин из базы данных по его названию."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM terms WHERE term = ?", (term,))
            conn.commit()
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Термин '{term}' удален.")
            else:
                logger.warning(f"Термин '{term}' не найден для удаления.")
            return success
    except sqlite3.Error as e:
        logger.error(f"Ошибка удаления термина '{term}': {e}")
        return False

# Функция получения всех терминов (термин первым, затем определение)
def get_all_terms() -> List[Tuple[str, str]]: # Термин (str) первым
    """Возвращает список всех терминов (термин, определение)."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Здесь термин уже идет первым по определению таблицы
            cursor.execute("SELECT term, definition FROM terms")
            terms = cursor.fetchall()
            return terms # Возвращаем список кортежей (term, definition)
    except sqlite3.Error as e:
        logger.error(f"Ошибка получения терминов: {e}")
        return []

# --- Функции для Групп ---

def add_group(name: str, description: str, link: str) -> bool:
    """Добавляет новую группу в базу данных."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Убедитесь, что в таблице groups есть колонка 'link', если добавляете ее здесь
            cursor.execute(
                "INSERT INTO groups (name, description, link) VALUES (?, ?, ?)",
                (name, description, link)
            )
            conn.commit()
            logger.info(f"Группа '{name}' добавлена.")
            return True
    except sqlite3.IntegrityError:
        logger.warning(f"Попытка добавить существующую группу: '{name}'")
        return False # Группа с таким именем уже существует
    except sqlite3.Error as e:
        logger.error(f"Ошибка добавления группы '{name}': {e}")
        return False

def update_group(group_id: int, new_description: str, new_link: str) -> bool:
    """Обновляет описание и ссылку группы по ее ID."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE groups SET description = ?, link = ? WHERE id = ?",
                           (new_description, new_link, group_id))
            conn.commit()
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Группа с ID {group_id} обновлена.")
            else:
                logger.warning(f"Группа с ID {group_id} не найдена для обновления.")
            return success
    except sqlite3.Error as e:
        logger.error(f"Ошибка при обновлении группы с ID {group_id}: {e}")
        return False

# ИЗМЕНЕНО: Удаление группы по ID
def delete_group(group_id: int) -> bool:
    """Удаляет группу из базы данных по ее ID."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM groups WHERE id = ?", (group_id,))
            conn.commit()
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Группа с ID {group_id} удалена.")
            else:
                logger.warning(f"Группа с ID {group_id} не найдена для удаления.")
            return success
    except sqlite3.Error as e:
        logger.error(f"Ошибка при удалении группы с ID {group_id}: {e}")
        return False

# ИЗМЕНЕНО: Получение всех групп (ID первым, затем имя, описание, ссылка)
def get_all_groups() -> List[Tuple[int, str, Any, Any]]: # ID (int) первым, затем имя (str)
    """Возвращает список всех групп (id, имя, описание, ссылка)."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Выбираем ID первым, затем имя!
            cursor.execute("SELECT id, name, description, link FROM groups")
            groups = cursor.fetchall()
            return groups # Возвращаем список кортежей (id, name, description, link)
    except sqlite3.Error as e:
        logger.error(f"Ошибка при получении всех групп: {e}")
        return []
# ... (импорты и get_db_connection, init_db - остаются без изменений)

# Добавьте эти две функции:

async def get_items_page(category: str, page: int, items_per_page: int) -> List[Tuple]:
    """Получает элементы для конкретной страницы из базы данных по категории."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        offset = (page - 1) * items_per_page
        query = ""
        if category == "course":
            # get_all_courses в db_manager теперь должен возвращать (id, name, ...)
            query = "SELECT id, name, description, link FROM courses LIMIT ? OFFSET ?" # Выбираем больше полей для общности, хотя для кнопок нужно только ID и name
        elif category == "resource":
            # get_all_resources в db_manager теперь должен возвращать (id, name, ...)
            query = "SELECT id, name, description, link FROM resources LIMIT ? OFFSET ?"
        elif category == "term":
            # get_all_terms в db_manager возвращает (term, definition)
            query = "SELECT term, definition FROM terms LIMIT ? OFFSET ?"
        elif category == "group":
            # get_all_groups в db_manager теперь должен возвращать (id, name, ...)
            query = "SELECT id, name, description, link FROM groups LIMIT ? OFFSET ?"
        else:
            logger.error(f"Неизвестная категория для пагинации: {category}")
            return []

        cursor.execute(query, (items_per_page, offset))
        items = cursor.fetchall()
        # Для пагинации в админке нам нужно только ID и Name (или Term)
        # Адаптируем возвращаемый формат для соответствия ожиданиям create_paginated_keyboard
        adapted_items = []
        for item in items:
            if category == "term":
                # Для терминов: (term, definition) -> (term, term) для item_id_index=0, item_name_index=0
                adapted_items.append((item[0], item[0]))
            else:
                # Для остальных: (id, name, ...) -> (id, name) для item_id_index=0, item_name_index=1
                adapted_items.append((item[0], item[1]))
        return adapted_items # Возвращаем список кортежей (ID/Имя, Имя)


    except sqlite3.Error as e:
        logger.error(f"Ошибка при получении страницы {page} для категории {category}: {e}")
        return []
    finally:
        if conn:
            conn.close()


async def get_total_items_count(category: str) -> int:
    """Получает общее количество элементов для конкретной категории."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        query = ""
        if category == "course":
            query = "SELECT COUNT(*) FROM courses"
        elif category == "resource":
            query = "SELECT COUNT(*) FROM resources"
        elif category == "term":
            query = "SELECT COUNT(*) FROM terms"
        elif category == "group":
            query = "SELECT COUNT(*) FROM groups"
        else:
            logger.error(f"Неизвестная категория для подсчета количества: {category}")
            return 0

        cursor.execute(query)
        count = cursor.fetchone()[0]
        return count
    except sqlite3.Error as e:
        logger.error(f"Ошибка при подсчете количества для категории {category}: {e}")
        return 0
    finally:
        if conn:
            conn.close()

# ... (остальные функции add, update, delete в db_manager - должны соответствовать логике в handlers)

# Инициализация базы данных при первом импорте
init_db()