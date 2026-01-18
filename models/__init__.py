# models/__init__.py
"""
Инициализация модуля моделей базы данных.
Импортирует все модели для удобного доступа.
"""

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# Инициализация расширений
# SQLAlchemy - ORM для работы с базой данных
db = SQLAlchemy()

# LoginManager - управление сессиями пользователей
login_manager = LoginManager()
login_manager.login_view = (
    "auth.login"  # Перенаправление неавторизованных пользователей
)
login_manager.login_message = "Пожалуйста, войдите для доступа к этой странице."
login_manager.login_message_category = "info"

# Импортируем модели (после инициализации db, чтобы избежать циклических импортов)
from models.user import User
from models.folder import Folder
from models.document import Document

# Экспортируем все для удобного импорта в других модулях
__all__ = ["db", "login_manager", "User", "Folder", "Document"]
