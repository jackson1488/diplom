# utils/decorators.py
"""
Декораторы для проверки прав доступа и других условий.
"""

from functools import wraps
from flask import redirect, url_for, flash, abort
from flask_login import current_user
import logging

logger = logging.getLogger(__name__)


def login_required(f):
    """
    Декоратор, требующий авторизации пользователя.
    Перенаправляет неавторизованных пользователей на страницу входа.

    Usage:
        @app.route('/protected')
        @login_required
        def protected_page():
            return "This page requires login"
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            logger.warning(f"Неавторизованный доступ к {f.__name__}")
            flash("Пожалуйста, войдите для доступа к этой странице.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """
    Декоратор, требующий прав администратора.
    Возвращает 403 ошибку, если пользователь не является администратором.

    Usage:
        @app.route('/admin')
        @login_required
        @admin_required
        def admin_panel():
            return "Admin only"
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            logger.warning(f"Неавторизованный доступ к админ-панели: {f.__name__}")
            flash("Пожалуйста, войдите для доступа к этой странице.", "warning")
            return redirect(url_for("auth.login"))

        if not current_user.is_admin:
            logger.warning(
                f"Попытка доступа к админ-панели пользователем {current_user.id}: {f.__name__}"
            )
            flash("У вас нет прав для доступа к этой странице.", "danger")
            abort(403)

        return f(*args, **kwargs)

    return decorated_function


def document_owner_required(f):
    """
    Декоратор, проверяющий, что пользователь является владельцем документа.
    Требует параметр document_id в URL.

    Usage:
        @app.route('/document/<int:document_id>')
        @login_required
        @document_owner_required
        def view_document(document_id):
            return "Your document"
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        from models.document import Document

        document_id = kwargs.get("document_id")
        if not document_id:
            logger.error(
                "document_id не предоставлен в декораторе document_owner_required"
            )
            abort(400)

        document = Document.query.get_or_404(document_id)

        # Проверяем права: владелец или администратор
        if document.user_id != current_user.id and not current_user.is_admin:
            logger.warning(
                f"Попытка доступа к чужому документу {document_id} пользователем {current_user.id}"
            )
            flash("У вас нет прав для доступа к этому документу.", "danger")
            abort(403)

        return f(*args, **kwargs)

    return decorated_function


def active_user_required(f):
    """
    Декоратор, проверяющий, что пользователь активен (не заблокирован).

    Usage:
        @app.route('/action')
        @login_required
        @active_user_required
        def some_action():
            return "Action performed"
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_active:
            logger.warning(
                f"Попытка доступа заблокированным пользователем {current_user.id}"
            )
            flash("Ваш аккаунт заблокирован. Обратитесь к администратору.", "danger")
            return redirect(url_for("auth.logout"))
        return f(*args, **kwargs)

    return decorated_function
