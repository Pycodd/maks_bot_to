import sqlite3
import os
from pathlib import Path


def get_db_path():
    """Определяет путь к базе данных с учётом окружения"""

    # 1. DATA_DIR от BotHost (с значением по умолчанию)
    data_dir = os.getenv('DATA_DIR', '/app/data')  # ← добавили значение по умолчанию
    if data_dir:
        Path(data_dir).mkdir(parents=True, exist_ok=True)
        return Path(data_dir) / "to_bot.db"

    # 2. DATABASE_PATH (пользовательский путь)
    db_path = os.getenv("DATABASE_PATH")
    if db_path:
        return Path(db_path)

    # 3. Локальный путь по умолчанию
    return Path(__file__).parent / "data" / "to_bot.db"


DB_PATH = get_db_path()


def get_db():
    """Возвращает соединение с базой данных с оптимальными настройками"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    conn.execute("PRAGMA cache_size=-20000")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Создаёт базу данных и таблицы, если их нет"""

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        print(f"📁 База данных уже существует: {DB_PATH}")
    else:
        print(f"🆕 Создаём новую базу данных: {DB_PATH}")

    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute('''
                    CREATE TABLE IF NOT EXISTS admins (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        admin_id INTEGER NOT NULL UNIQUE,
                        admin_name TEXT NOT NULL,
                        phone TEXT NOT NULL
                    )
                ''')

        cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL UNIQUE,
                        user_name TEXT NOT NULL
                    )
                ''')

        cursor.execute('''
                    CREATE TABLE IF NOT EXISTS registrations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        district TEXT,
                        address TEXT NOT NULL,
                        entrance INTEGER,
                        floor INTEGER,
                        apartment TEXT,
                        phone TEXT NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                    )
                ''')

        cursor.execute('''
                    CREATE TABLE IF NOT EXISTS dispatchers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        dispatcher_id INTEGER NOT NULL UNIQUE,
                        dispatcher_name TEXT NOT NULL,
                        phone TEXT NOT NULL
                    )
                ''')

        conn.commit()

    print("✅ Таблицы готовы (admins, users, registrations, dispatchers)")

def check_db():
    """Проверяет состояние базы данных"""
    if DB_PATH.exists():
        size = DB_PATH.stat().st_size
        print(f"📊 База данных: {DB_PATH}")
        print(f"📏 Размер: {size} байт")

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"📋 Таблицы: {[t[0] for t in tables]}")
    else:
        print(f"❌ База данных не найдена: {DB_PATH}")

def populate_initial_data():
    """
    Заполняет базу данных начальными данными
    """
    with get_db() as conn:
        cursor = conn.cursor()

        admin_ids = [(13264219, 'Андрей Владимирович', '+79050646666')]
        for admin_id, name, phone in admin_ids:
            cursor.execute(
                "INSERT OR IGNORE INTO admins (admin_id, admin_name, phone) VALUES (?, ?, ?)",
                (admin_id, name, phone)
            )

        conn.commit()

    print("✅ Начальные данные добавлены (админы и техники)")
