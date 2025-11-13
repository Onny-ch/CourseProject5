#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Скрипт для проверки подключения к базе данных PostgreSQL."""
import os
import sys
from pathlib import Path

# Устанавливаем кодировку вывода для Windows
if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Добавляем путь к проекту (на уровень выше, так как мы в services/)
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Загружаем переменные окружения
from dotenv import load_dotenv

load_dotenv(BASE_DIR / ".env")

DB_ENGINE = os.getenv("DB_ENGINE", "").strip()

if not DB_ENGINE or "postgresql" not in DB_ENGINE.lower():
    print("PostgreSQL не настроен. Используется SQLite.")
    sys.exit(0)

try:
    import psycopg2

    conn_params = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", "postgres"),
        "database": "postgres",  # Подключаемся к системной БД для проверки
    }

    print("Попытка подключения к PostgreSQL...")
    conn = psycopg2.connect(**conn_params)
    conn.set_client_encoding("UTF8")
    cursor = conn.cursor()

    # Проверяем существование базы данных
    db_name = os.getenv("DB_NAME", "habits")
    cursor.execute(
        "SELECT 1 FROM pg_database WHERE datname = %s", (db_name,)
    )
    exists = cursor.fetchone()

    if exists:
        print(f"[OK] База данных '{db_name}' существует")
    else:
        print(f"[ERROR] База данных '{db_name}' НЕ существует")
        print(f"\nСоздайте базу данных командой:")
        print(f"  CREATE DATABASE {db_name} WITH ENCODING 'UTF8';")
        print("\nИли через psql:")
        print(f"  psql -U {conn_params['user']} -c \"CREATE DATABASE {db_name} WITH ENCODING 'UTF8';\"")

    cursor.close()
    conn.close()
    print("[OK] Подключение к PostgreSQL успешно!")

except psycopg2.OperationalError as e:
    print(f"[ERROR] Ошибка подключения к PostgreSQL: {e}")
    print("\nПроверьте:")
    print("  1. PostgreSQL запущен")
    print("  2. Параметры подключения в .env файле корректны")
    print("  3. База данных создана")
except ImportError:
    print("[ERROR] psycopg2 не установлен. Установите: pip install psycopg2-binary")
except Exception as e:
    print(f"[ERROR] Неожиданная ошибка: {e}")

