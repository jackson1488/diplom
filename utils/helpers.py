# utils/helpers.py
"""
Вспомогательные функции общего назначения.
"""

import os
import uuid
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def format_file_size(size_bytes: int) -> str:
    """
    Форматирует размер файла в человекочитаемый вид.

    Args:
        size_bytes: размер в байтах

    Returns:
        Отформатированная строка (например, "1.5 MB")
    """
    if size_bytes is None:
        return "Неизвестно"

    # Определяем единицы измерения
    units = ["Б", "КБ", "МБ", "ГБ", "ТБ"]
    unit_index = 0
    size = float(size_bytes)

    # Переводим в подходящую единицу измерения
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    # Форматируем с нужным количеством знаков после запятой
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.2f} {units[unit_index]}"


def format_date(date: Optional[datetime], format_string: str = "%d.%m.%Y %H:%M") -> str:
    """
    Форматирует дату в строку.

    Args:
        date: объект datetime
        format_string: формат вывода даты

    Returns:
        Отформатированная строка даты
    """
    if date is None:
        return "Не указано"

    try:
        return date.strftime(format_string)
    except Exception as e:
        logger.error(f"Ошибка при форматировании даты: {str(e)}")
        return "Ошибка формата"


def format_relative_date(date: Optional[datetime]) -> str:
    """
    Форматирует дату в относительный вид (например, "2 часа назад").

    Args:
        date: объект datetime

    Returns:
        Относительная дата в виде строки
    """
    if date is None:
        return "Никогда"

    try:
        now = datetime.utcnow()
        diff = now - date

        seconds = diff.total_seconds()

        if seconds < 60:
            return "Только что"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes} мин. назад"
        elif seconds < 86400:
            hours = int(seconds / 3600)
            return f"{hours} ч. назад"
        elif seconds < 604800:
            days = int(seconds / 86400)
            return f"{days} дн. назад"
        elif seconds < 2592000:
            weeks = int(seconds / 604800)
            return f"{weeks} нед. назад"
        elif seconds < 31536000:
            months = int(seconds / 2592000)
            return f"{months} мес. назад"
        else:
            years = int(seconds / 31536000)
            return f"{years} лет назад"

    except Exception as e:
        logger.error(f"Ошибка при форматировании относительной даты: {str(e)}")
        return "Неизвестно"


def generate_unique_filename(
    original_filename: str, user_id: Optional[int] = None
) -> str:
    """
    Генерирует уникальное имя файла на основе оригинального.

    Args:
        original_filename: оригинальное имя файла
        user_id: ID пользователя (опционально, добавляется в префикс)

    Returns:
        Уникальное имя файла
    """
    # Получаем расширение файла
    if "." in original_filename:
        name, extension = original_filename.rsplit(".", 1)
    else:
        name = original_filename
        extension = ""

    # Генерируем уникальный идентификатор
    unique_id = uuid.uuid4().hex[:12]

    # Формируем новое имя
    if user_id:
        new_filename = f"{user_id}_{unique_id}"
    else:
        new_filename = unique_id

    # Добавляем расширение, если оно было
    if extension:
        new_filename = f"{new_filename}.{extension.lower()}"

    return new_filename


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Обрезает строку до указанной длины, добавляя суффикс.

    Args:
        text: исходная строка
        max_length: максимальная длина
        suffix: суффикс для обрезанной строки

    Returns:
        Обрезанная строка
    """
    if not text:
        return ""

    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def sanitize_filename(filename: str) -> str:
    """
    Очищает имя файла от опасных символов.

    Args:
        filename: исходное имя файла

    Returns:
        Безопасное имя файла
    """
    # Заменяем опасные символы на подчеркивание
    dangerous_chars = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]

    safe_filename = filename
    for char in dangerous_chars:
        safe_filename = safe_filename.replace(char, "_")

    # Убираем множественные подчеркивания
    while "__" in safe_filename:
        safe_filename = safe_filename.replace("__", "_")

    # Убираем подчеркивания в начале и конце
    safe_filename = safe_filename.strip("_")

    return safe_filename


def create_directory_if_not_exists(directory_path: str) -> bool:
    """
    Создает директорию, если она не существует.

    Args:
        directory_path: путь к директории

    Returns:
        True если директория создана или уже существует, False при ошибке
    """
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path, exist_ok=True)
            logger.info(f"Создана директория: {directory_path}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при создании директории {directory_path}: {str(e)}")
        return False


def get_file_extension(filename: str) -> Optional[str]:
    """
    Извлекает расширение файла.

    Args:
        filename: имя файла

    Returns:
        Расширение файла в нижнем регистре или None
    """
    if "." not in filename:
        return None

    return filename.rsplit(".", 1)[1].lower()


def is_image_file(filename: str) -> bool:
    """
    Проверяет, является ли файл изображением по расширению.

    Args:
        filename: имя файла

    Returns:
        True если файл - изображение, False в противном случае
    """
    image_extensions = {"jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp"}
    extension = get_file_extension(filename)
    return extension in image_extensions if extension else False


def is_pdf_file(filename: str) -> bool:
    """
    Проверяет, является ли файл PDF документом.

    Args:
        filename: имя файла

    Returns:
        True если файл - PDF, False в противном случае
    """
    extension = get_file_extension(filename)
    return extension == "pdf" if extension else False
