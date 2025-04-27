import sqlite3
import os
from typing import List, Tuple, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_NAME = "bot.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    return conn

def init_db():
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

# Функции для Курсов 

def add_course(name: str, description: str, link: str) -> bool:
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
        return False 
    except sqlite3.Error as e:
        logger.error(f"Ошибка добавления курса '{name}': {e}")
        return False


# Удаление курса по ID
def delete_course(course_id: int) -> bool:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM courses WHERE id = ?", (course_id,))
            conn.commit()
            success = cursor.rowcount > 0
            if success:
                logger.info(f"Курс с ID {course_id} удален.")
            else:
                logger.warning(f"Курс с ID {course_id} не найден для удаления.")
            return success
    except sqlite3.Error as e:
        logger.error(f"Ошибка при удалении курса с ID {course_id}: {e}")
        return False

# Получение всех курсов 
def get_all_courses() -> List[Tuple[int, str, Any, Any]]: 
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, description, link FROM courses")
            courses = cursor.fetchall()
            return courses 
    except sqlite3.Error as e:
        logger.error(f"Ошибка при получении всех курсов: {e}")
        return []

# Функции для Ресурсов 

def add_resource(name: str, description: str, link: str) -> bool:
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
        return False
    except sqlite3.Error as e:
        logger.error(f"Ошибка при добавлении ресурса '{name}': {e}")
        return False

# Удаление ресурса по ID
def delete_resource(resource_id: int) -> bool:
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

# Получение всех ресурсов
def get_all_resources() -> List[Tuple[int, str, Any, Any]]: 
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, description, link FROM resources")
            resources = cursor.fetchall()
            return resources 
    except sqlite3.Error as e:
        logger.error(f"Ошибка при получении всех ресурсов: {e}")
        return []

# --- Функции для Терминов ---

def add_term(term: str, definition: str) -> bool:
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
        return False 
    except sqlite3.Error as e:
        logger.error(f"Ошибка добавления термина '{term}': {e}")
        return False

# Функция удаления термина 
def delete_term(term: str) -> bool:
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

# Функция получения всех терминов 
def get_all_terms() -> List[Tuple[str, str]]: 
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT term, definition FROM terms")
            terms = cursor.fetchall()
            return terms 
    except sqlite3.Error as e:
        logger.error(f"Ошибка получения терминов: {e}")
        return []

# Функции для Групп 

def add_group(name: str, description: str, link: str) -> bool:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO groups (name, description, link) VALUES (?, ?, ?)",
                (name, description, link)
            )
            conn.commit()
            logger.info(f"Группа '{name}' добавлена.")
            return True
    except sqlite3.IntegrityError:
        logger.warning(f"Попытка добавить существующую группу: '{name}'")
        return False 
    except sqlite3.Error as e:
        logger.error(f"Ошибка добавления группы '{name}': {e}")
        return False

# Удаление группы по ID
def delete_group(group_id: int) -> bool:
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

# Получение всех групп 
def get_all_groups() -> List[Tuple[int, str, Any, Any]]: 
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, description, link FROM groups")
            groups = cursor.fetchall()
            return groups 
    except sqlite3.Error as e:
        logger.error(f"Ошибка при получении всех групп: {e}")
        return []

async def get_items_page(category: str, page: int, items_per_page: int) -> List[Tuple]:
    """Получает элементы для конкретной страницы из базы данных по категории."""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        offset = (page - 1) * items_per_page
        query = ""
        if category == "course":
            query = "SELECT id, name, description, link FROM courses LIMIT ? OFFSET ?"  
        elif category == "resource":
            query = "SELECT id, name, description, link FROM resources LIMIT ? OFFSET ?"
        elif category == "term":
            query = "SELECT term, definition FROM terms LIMIT ? OFFSET ?"
        elif category == "group":
            query = "SELECT id, name, description, link FROM groups LIMIT ? OFFSET ?"
        else:
            logger.error(f"Неизвестная категория для пагинации: {category}")
            return []

        cursor.execute(query, (items_per_page, offset))
        items = cursor.fetchall()
        adapted_items = []
        for item in items:
            if category == "term":
                adapted_items.append((item[0], item[0]))
            else:
                adapted_items.append((item[0], item[1]))
        return adapted_items 


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

init_db()