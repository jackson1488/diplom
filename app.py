# app.py
"""
Главный файл приложения Flask.
Инициализирует приложение, регистрирует расширения и маршруты.
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, redirect, url_for, send_from_directory
from flask_login import current_user

from config import get_config
from models import db, login_manager
from routes import register_blueprints


def create_app(config_name="default"):
    """
    Фабрика приложений Flask.
    Создает и настраивает экземпляр приложения.

    Args:
        config_name: название конфигурации ('development', 'production', 'testing')

    Returns:
        Сконфигурированное Flask приложение
    """
    # Создаем экземпляр Flask
    app = Flask(__name__)

    # Загружаем конфигурацию
    config_class = get_config(config_name)
    app.config.from_object(config_class)

    # Инициализируем конфигурацию (создание директорий и т.д.)
    config_class.init_app(app)

    # Настраиваем логирование
    setup_logging(app)

    # Инициализируем расширения
    db.init_app(app)
    login_manager.init_app(app)

    # Создаем таблицы базы данных
    with app.app_context():
        db.create_all()

        # Создаем администратора по умолчанию, если его нет
        from models.user import User

        admin = User.query.filter_by(username=app.config["ADMIN_USERNAME"]).first()
        if not admin:
            User.create_admin(
                username=app.config["ADMIN_USERNAME"],
                email=app.config["ADMIN_EMAIL"],
                password=app.config["ADMIN_PASSWORD"],
            )
            app.logger.info("Создан администратор по умолчанию")

    # Регистрируем blueprints (маршруты)
    register_blueprints(app)

    # Регистрируем маршруты для раздачи файлов (ВАЖНО!)
    register_file_routes(app)

    # Регистрируем обработчики ошибок
    register_error_handlers(app)

    # Регистрируем контекстные процессоры для шаблонов
    register_template_context(app)

    # Главная страница
    @app.route("/")
    def index():
        """Главная страница приложения."""
        if current_user.is_authenticated:
            return redirect(url_for("documents.library"))
        return redirect(url_for("auth.login"))

    app.logger.info(f"Приложение запущено в режиме: {config_name}")

    return app


def register_file_routes(app):
    """
    Регистрирует маршруты для раздачи загруженных файлов и миниатюр.
    ВАЖНО: Без этого миниатюры не будут отображаться!

    Args:
        app: экземпляр Flask приложения
    """

    @app.route("/thumbnails/<path:filename>")
    def serve_thumbnail(filename):
        """
        Раздача миниатюр изображений.
        Путь: /thumbnails/user_id/thumb_filename.jpg
        """
        thumbnails_dir = app.config["THUMBNAIL_FOLDER"]
        return send_from_directory(thumbnails_dir, filename)

    @app.route("/uploads/<path:filename>")
    def serve_upload(filename):
        """
        Раздача загруженных файлов.
        Путь: /uploads/user_id/filename.ext
        """
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    app.logger.info("Маршруты для раздачи файлов зарегистрированы")


def setup_logging(app):
    """
    Настраивает систему логирования.

    Args:
        app: экземпляр Flask приложения
    """
    if not app.debug and not app.testing:
        # Создаем директорию для логов, если не существует
        if not os.path.exists(app.config["LOG_FOLDER"]):
            os.makedirs(app.config["LOG_FOLDER"])

        # Настраиваем файловый обработчик с ротацией
        file_handler = RotatingFileHandler(
            app.config["LOG_FILE"], maxBytes=10240000, backupCount=10  # 10 МБ
        )

        # Устанавливаем формат логов
        file_handler.setFormatter(logging.Formatter(app.config["LOG_FORMAT"]))

        # Устанавливаем уровень логирования
        log_level = getattr(logging, app.config["LOG_LEVEL"].upper(), logging.INFO)
        file_handler.setLevel(log_level)

        # Добавляем обработчик к логгеру приложения
        app.logger.addHandler(file_handler)
        app.logger.setLevel(log_level)

        app.logger.info("Система логирования инициализирована")


def register_error_handlers(app):
    """
    Регистрирует обработчики HTTP ошибок.

    Args:
        app: экземпляр Flask приложения
    """

    @app.errorhandler(404)
    def not_found_error(error):
        """Обработчик ошибки 404 (страница не найдена)."""
        app.logger.warning(f"404 ошибка: {error}")
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden_error(error):
        """Обработчик ошибки 403 (доступ запрещен)."""
        app.logger.warning(f"403 ошибка: {error}")
        return render_template("errors/403.html"), 403

    @app.errorhandler(500)
    def internal_error(error):
        """Обработчик ошибки 500 (внутренняя ошибка сервера)."""
        db.session.rollback()
        app.logger.error(f"500 ошибка: {error}", exc_info=True)
        return render_template("errors/500.html"), 500

    app.logger.info("Обработчики ошибок зарегистрированы")


def register_template_context(app):
    """
    Регистрирует контекстные процессоры для шаблонов.
    Добавляет глобальные переменные и функции, доступные во всех шаблонах.

    Args:
        app: экземпляр Flask приложения
    """
    from utils.helpers import format_file_size, format_date, format_relative_date

    @app.context_processor
    def utility_processor():
        """Добавляет утилиты в контекст шаблонов."""
        return {
            "format_file_size": format_file_size,
            "format_date": format_date,
            "format_relative_date": format_relative_date,
        }

    @app.context_processor
    def inject_config():
        """Добавляет конфигурацию в контекст шаблонов."""
        return {"app_name": "DocScanner", "app_version": "1.0.0"}


@login_manager.user_loader
def load_user(user_id):
    """Функция загрузки пользователя для Flask-Login."""
    from models.user import User

    return db.session.get(User, int(user_id))


# Создаем экземпляр приложения
# Режим берется из переменной окружения FLASK_ENV или используется 'development'
config_name = os.environ.get("FLASK_ENV", "development")
app = create_app(config_name)


if __name__ == "__main__":
    """
    Точка входа для запуска приложения.
    Использовать только для разработки!
    Для продакшена используйте WSGI сервер (gunicorn, uwsgi).
    """
    # Получаем порт из переменной окружения или используем 5000
    port = int(os.environ.get("PORT", 5000))

    # Запускаем сервер разработки
    app.run(
        host="0.0.0.0",  # Доступ с любого IP адреса
        port=port,
        debug=app.config["DEBUG"],
    )
