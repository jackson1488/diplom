"""
Конфигурация приложения
"""

import os
import sys
from datetime import timedelta


def get_app_path():
    """Получает путь к приложению (работает и в dev, и в compiled)"""
    if getattr(sys, "frozen", False):
        # Если скомпилировано PyInstaller
        # На macOS .app: ~/Applications/DocScanner.app/Contents/MacOS/
        # Данные сохраняем в ~/Library/Application Support/DocScanner/
        if sys.platform == "darwin":  # macOS
            home = os.path.expanduser("~")
            app_support = os.path.join(
                home, "Library", "Application Support", "DocScanner"
            )
            os.makedirs(app_support, exist_ok=True)
            return app_support
        else:
            # Для Windows/Linux - рядом с exe
            return os.path.dirname(sys.executable)
    else:
        # Режим разработки
        return os.path.abspath(os.path.dirname(__file__))


class Config:
    """Базовая конфигурация"""

    # Базовая директория
    BASE_DIR = get_app_path()

    # Flask
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-change-in-production"
    DEBUG = False
    TESTING = False

    # База данных
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL")
        or f'sqlite:///{os.path.join(BASE_DIR, "data", "app.db")}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # Загрузка файлов
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "gif", "tiff", "bmp"}

    # Миниатюры
    THUMBNAIL_SIZE = (300, 300)
    THUMBNAIL_FOLDER = os.path.join(UPLOAD_FOLDER, "thumbnails")
    JPEG_QUALITY = 85
    IMAGE_MAX_SIZE = (2000, 2000)

    # Экспорт документов (ДОБАВЬ ЭТО!)
    EXPORT_TEMP_FOLDER = os.path.join(BASE_DIR, "temp", "exports")  # ← НОВОЕ

    # Flask-Login
    REMEMBER_COOKIE_DURATION = timedelta(days=30)

    # Логирование
    LOG_FOLDER = os.path.join(BASE_DIR, "logs")
    LOG_FILE = os.path.join(LOG_FOLDER, "app.log")
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # OCR настройки
    OCR_LANGUAGES = ["ru", "en"]
    OCR_GPU = False

    # PDF настройки
    PDF_DPI = 300  # Качество при генерации PDF
    PDF_TO_IMAGE_DPI = 300  # Качество при конвертации PDF → изображение

    # Администратор
    ADMIN_USERNAME = "admin"
    ADMIN_EMAIL = "admin@example.com"
    ADMIN_PASSWORD = "admin"

    @staticmethod
    def init_app(app):
        """Инициализация приложения"""
        # Создаем необходимые директории
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(Config.THUMBNAIL_FOLDER, exist_ok=True)
        os.makedirs(Config.EXPORT_TEMP_FOLDER, exist_ok=True)  # ← НОВОЕ
        os.makedirs(Config.LOG_FOLDER, exist_ok=True)
        os.makedirs(os.path.join(Config.BASE_DIR, "data"), exist_ok=True)


class DevelopmentConfig(Config):
    """Конфигурация для разработки"""

    DEBUG = True
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    """Конфигурация для продакшена"""

    DEBUG = False
    SQLALCHEMY_ECHO = False
    LOG_LEVEL = "WARNING"


class TestingConfig(Config):
    """Конфигурация для тестирования"""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


# Словарь конфигураций
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}


def get_config(config_name="default"):
    """Получить конфигурацию по имени"""
    return config.get(config_name, config["default"])
