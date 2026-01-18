# routes/__init__.py
"""
Инициализация модуля маршрутов.
Регистрирует все blueprints приложения.
"""

from flask import Flask


def register_blueprints(app: Flask):
    """
    Регистрирует все blueprints в приложении.

    Args:
        app: экземпляр Flask приложения
    """
    from routes.auth import auth_bp
    from routes.documents import documents_bp
    from routes.scanner import scanner_bp
    from routes.editor import editor_bp
    from routes.admin import admin_bp

    # Регистрируем blueprints с префиксами URL
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(documents_bp, url_prefix="/documents")
    app.register_blueprint(scanner_bp, url_prefix="/scanner")
    app.register_blueprint(editor_bp, url_prefix="/editor")
    app.register_blueprint(admin_bp, url_prefix="/admin")

    print("✓ Все blueprints зарегистрированы")
