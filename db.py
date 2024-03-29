from config import db_params

import psycopg2
from psycopg2 import sql

sql_commands = """

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS promotions (
    id SERIAL PRIMARY KEY,
    text TEXT NOT NULL,
    image_path TEXT,
    action_url TEXT,
    button_text TEXT DEFAULT 'Подробнее', -- добавляем столбец для текста кнопки
    is_active BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS administrators (
    id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL,
    added_by INT,
    added_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (added_by) REFERENCES users (user_id) ON DELETE SET NULL
);

ALTER TABLE promotions ADD COLUMN media_paths TEXT[];
"""

def create_tables(db_params):

    conn = None

    try:

        # Подключение к базе данных

        conn = psycopg2.connect(**db_params)

        cursor = conn.cursor()

        # Создание таблиц

        cursor.execute(sql.SQL(sql_commands))

        conn.commit()

        print("Tables created successfully")

    except (Exception, psycopg2.DatabaseError) as error:

        print(error)

    finally:

        if conn is not None:

            conn.close()

create_tables(db_params)

# Функция подключения к базе данных
def get_db_connection():
    conn = psycopg2.connect(**db_params)
    return conn
