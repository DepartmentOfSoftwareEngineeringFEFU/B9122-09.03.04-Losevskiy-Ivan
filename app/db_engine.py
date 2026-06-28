import bcrypt
import sqlite3
from pathlib import Path


DB_PATH = "video_presets.db"


# Описание структуры таблиц
TABLE_SCHEMAS = {
    "Users": """
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        )
    """,

    "H264": """
        CREATE TABLE IF NOT EXISTS H264 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            preset_name TEXT NOT NULL,
            preset_description TEXT,
            crf INTEGER NOT NULL,
            preset TEXT NOT NULL,
            aq_mode INTEGER NOT NULL,
            bf INTEGER NOT NULL,
        
            FOREIGN KEY(user_id) REFERENCES Users(id),
        
            UNIQUE(user_id, preset_name)
        )
    """
}

def init_db(db_path: str = DB_PATH) -> None:
    """
    Создание БД и всех таблиц.
    """
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        for schema in TABLE_SCHEMAS.values():
            cursor.execute(schema)

        conn.commit()


def save_preset(
    codec: str,
    username: str,
    values: tuple,
    db_path: str = DB_PATH
) -> int:
    """
    values для H264:

    (
        preset_name,
        preset_description,
        crf,
        preset,
        aq_mode,
        bf
    )
    """

    codec = codec.upper()

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id FROM Users WHERE username = ?",
            (username,)
        )

        row = cursor.fetchone()

        if row is None:
            raise ValueError(f"Пользователь '{username}' не найден")

        user_id = row[0]

        if codec == "H264":
            cursor.execute(
                """
                INSERT INTO H264(
                    user_id,
                    preset_name,
                    preset_description,
                    crf,
                    preset,
                    aq_mode,
                    bf
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, *values)
            )
        else:
            raise ValueError(f"Неизвестный кодек: {codec}")

        conn.commit()
        return cursor.lastrowid


def create_user(
    username: str,
    password: str,
    db_path: str = DB_PATH
) -> bool:
    """
    Создает нового пользователя.

    Возвращает:
        True  - пользователь создан.
        False - пользователь уже существует.
    """

    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO Users(username, password_hash)
                VALUES (?, ?)
                """,
                (username, password_hash)
            )

            conn.commit()
            return True

    except sqlite3.IntegrityError:
        return False

def authenticate_user(
    username: str,
    password: str,
    db_path: str = DB_PATH
) -> bool:
    """
    Проверяет существование пользователя и правильность пароля.

    Возвращает:
        True  - логин и пароль верны.
        False - пользователь отсутствует или пароль неверен.
    """

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT password_hash
            FROM Users
            WHERE username = ?
            """,
            (username,)
        )

        row = cursor.fetchone()

        if row is None:
            return False

        stored_hash = row[0].encode("utf-8")

        return bcrypt.checkpw(
            password.encode("utf-8"),
            stored_hash
        )

def user_exists(
    username: str,
    db_path: str = DB_PATH
) -> bool:

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT 1
            FROM Users
            WHERE username = ?
            """,
            (username,)
        )

        return cursor.fetchone() is not None

def get_preset_by_id(
    codec: str,
    preset_id: int,
    db_path: str = DB_PATH
):
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        cursor.execute(
            f"SELECT * FROM {codec.upper()} WHERE id = ?",
            (preset_id,)
        )

        return cursor.fetchone()

def get_user_presets(
    codec: str,
    username: str,
    db_path: str = DB_PATH
):
    """
    Возвращает кортеж всех пресетов пользователя.

    (
        (id, user_id, preset_name, preset_description,
         crf, preset, aq_mode, bf),

        ...
    )
    """

    codec = codec.upper()

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        cursor.execute(
            f"""
            SELECT p.*
            FROM {codec} p
            JOIN Users u
                ON p.user_id = u.id
            WHERE u.username = ?
            ORDER BY p.id
            """,
            (username,)
        )

        return tuple(cursor.fetchall())


if __name__ == "__main__":
    init_db()

    preset_id = save_preset(
        "H264",
        (
            "Balanced",
            "Универсальный пресет",
            22,
            "slow",
            2,
            4
        )
    )

    print(f"Добавлен пресет ID={preset_id}")

    print("\nПо ID:")
    print(get_preset_by_id("H264", preset_id))