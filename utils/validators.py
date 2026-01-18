# utils/validators.py
"""
Функции для валидации данных.
"""

import re
import os
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    Проверяет корректность email адреса.

    Args:
        email: email адрес для проверки

    Returns:
        Кортеж (валиден, сообщение_об_ошибке)
    """
    if not email:
        return False, "Email не может быть пустым"

    # Простая регулярка для проверки email
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(email_pattern, email):
        return False, "Некорректный формат email адреса"

    if len(email) > 120:
        return False, "Email слишком длинный (максимум 120 символов)"

    return True, None


def validate_password(password: str, min_length: int = 6) -> Tuple[bool, Optional[str]]:
    """
    Проверяет корректность пароля.

    Args:
        password: пароль для проверки
        min_length: минимальная длина пароля

    Returns:
        Кортеж (валиден, сообщение_об_ошибке)
    """
    if not password:
        return False, "Пароль не может быть пустым"

    if len(password) < min_length:
        return False, f"Пароль должен содержать минимум {min_length} символов"

    if len(password) > 128:
        return False, "Пароль слишком длинный (максимум 128 символов)"

    # Дополнительные проверки (опционально)
    # if not re.search(r'[A-Z]', password):
    #     return False, "Пароль должен содержать хотя бы одну заглавную букву"
    # if not re.search(r'[a-z]', password):
    #     return False, "Пароль должен содержать хотя бы одну строчную букву"
    # if not re.search(r'[0-9]', password):
    #     return False, "Пароль должен содержать хотя бы одну цифру"

    return True, None


def validate_username(username: str) -> Tuple[bool, Optional[str]]:
    """
    Проверяет корректность имени пользователя.

    Args:
        username: имя пользователя для проверки

    Returns:
        Кортеж (валиден, сообщение_об_ошибке)
    """
    if not username:
        return False, "Имя пользователя не может быть пустым"

    if len(username) < 3:
        return False, "Имя пользователя должно содержать минимум 3 символа"

    if len(username) > 64:
        return False, "Имя пользователя слишком длинное (максимум 64 символа)"

    # Разрешаем только буквы, цифры, подчеркивание и дефис
    username_pattern = r"^[a-zA-Z0-9_-]+$"
    if not re.match(username_pattern, username):
        return (
            False,
            "Имя пользователя может содержать только буквы, цифры, подчеркивание и дефис",
        )

    return True, None


def validate_filename(
    filename: str, allowed_extensions: set
) -> Tuple[bool, Optional[str]]:
    """
    Проверяет корректность имени файла и его расширения.

    Args:
        filename: имя файла для проверки
        allowed_extensions: множество разрешенных расширений

    Returns:
        Кортеж (валиден, сообщение_об_ошибке)
    """
    if not filename:
        return False, "Имя файла не может быть пустым"

    # Проверяем наличие расширения
    if "." not in filename:
        return False, "Файл должен иметь расширение"

    # Получаем расширение
    extension = filename.rsplit(".", 1)[1].lower()

    # Проверяем, разрешено ли расширение
    if extension not in allowed_extensions:
        return (
            False,
            f"Недопустимое расширение файла. Разрешены: {', '.join(allowed_extensions)}",
        )

    # Проверяем длину имени файла
    if len(filename) > 256:
        return False, "Имя файла слишком длинное (максимум 256 символов)"

    return True, None


def validate_document_title(title: str) -> Tuple[bool, Optional[str]]:
    """
    Проверяет корректность названия документа.

    Args:
        title: название документа

    Returns:
        Кортеж (валиден, сообщение_об_ошибке)
    """
    if not title:
        return False, "Название документа не может быть пустым"

    if len(title) < 2:
        return False, "Название документа должно содержать минимум 2 символа"

    if len(title) > 256:
        return False, "Название документа слишком длинное (максимум 256 символов)"

    return True, None


def validate_folder_name(name: str) -> Tuple[bool, Optional[str]]:
    """
    Проверяет корректность названия папки.

    Args:
        name: название папки

    Returns:
        Кортеж (валиден, сообщение_об_ошибке)
    """
    if not name:
        return False, "Название папки не может быть пустым"

    if len(name) < 2:
        return False, "Название папки должно содержать минимум 2 символа"

    if len(name) > 128:
        return False, "Название папки слишком длинное (максимум 128 символов)"

    return True, None


def validate_hex_color(color: str) -> Tuple[bool, Optional[str]]:
    """
    Проверяет корректность hex кода цвета.

    Args:
        color: hex код цвета (например, #FF5733)

    Returns:
        Кортеж (валиден, сообщение_об_ошибке)
    """
    if not color:
        return False, "Цвет не может быть пустым"

    # Проверяем формат hex цвета
    hex_pattern = r"^#[0-9A-Fa-f]{6}$"
    if not re.match(hex_pattern, color):
        return False, "Некорректный формат цвета. Используйте формат #RRGGBB"

    return True, None
