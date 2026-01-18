# routes/admin.py
"""
Маршруты для административной панели.
Доступны только пользователям с правами администратора.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user
from datetime import datetime, timedelta
import logging

from models import db
from models.user import User
from models.document import Document
from models.folder import Folder
from utils.decorators import login_required, admin_required

# Настраиваем логирование
logger = logging.getLogger(__name__)

# Создаем blueprint для админ-панели
admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/dashboard")
@login_required
@admin_required
def dashboard():
    """
    Главная страница административной панели.
    Отображает статистику и общую информацию о системе.
    """
    # Получаем общую статистику
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    admin_users = User.query.filter_by(is_admin=True).count()

    total_documents = Document.query.count()
    total_folders = Folder.query.count()

    # Вычисляем общий размер хранилища
    total_storage = db.session.query(db.func.sum(Document.file_size)).scalar() or 0

    # Статистика за последние 30 дней
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    new_users_30d = User.query.filter(User.created_at >= thirty_days_ago).count()
    new_documents_30d = Document.query.filter(
        Document.created_at >= thirty_days_ago
    ).count()

    # Статистика OCR
    ocr_completed = Document.query.filter_by(ocr_status="completed").count()
    ocr_processing = Document.query.filter_by(ocr_status="processing").count()
    ocr_failed = Document.query.filter_by(ocr_status="failed").count()

    # Последние пользователи
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()

    # Последние документы
    recent_documents = (
        Document.query.order_by(Document.created_at.desc()).limit(5).all()
    )

    # Топ пользователей по количеству документов
    top_users = (
        db.session.query(User, db.func.count(Document.id).label("doc_count"))
        .join(Document)
        .group_by(User.id)
        .order_by(db.desc("doc_count"))
        .limit(5)
        .all()
    )

    stats = {
        "total_users": total_users,
        "active_users": active_users,
        "admin_users": admin_users,
        "total_documents": total_documents,
        "total_folders": total_folders,
        "total_storage": total_storage,
        "new_users_30d": new_users_30d,
        "new_documents_30d": new_documents_30d,
        "ocr_completed": ocr_completed,
        "ocr_processing": ocr_processing,
        "ocr_failed": ocr_failed,
    }

    logger.info(f"Админ-панель открыта: admin_id={current_user.id}")

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        recent_users=recent_users,
        recent_documents=recent_documents,
        top_users=top_users,
    )


@admin_bp.route("/users")
@login_required
@admin_required
def users():
    """
    Страница управления пользователями.
    """
    # Получаем параметры фильтрации
    search_query = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "all")

    # Базовый запрос
    query = User.query

    # Поиск по имени или email
    if search_query:
        query = query.filter(
            db.or_(
                User.username.ilike(f"%{search_query}%"),
                User.email.ilike(f"%{search_query}%"),
                User.full_name.ilike(f"%{search_query}%"),
            )
        )

    # Фильтр по статусу
    if status_filter == "active":
        query = query.filter_by(is_active=True)
    elif status_filter == "inactive":
        query = query.filter_by(is_active=False)
    elif status_filter == "admin":
        query = query.filter_by(is_admin=True)

    # Сортировка
    query = query.order_by(User.created_at.desc())

    # Выполняем запрос
    users_list = query.all()

    return render_template(
        "admin/users.html",
        users=users_list,
        search_query=search_query,
        status_filter=status_filter,
    )


@admin_bp.route("/user/<int:user_id>")
@login_required
@admin_required
def view_user(user_id):
    """
    Просмотр детальной информации о пользователе.
    """
    user = User.query.get_or_404(user_id)

    # Получаем статистику пользователя
    user_stats = {
        "documents": Document.query.filter_by(user_id=user_id).count(),
        "folders": Folder.query.filter_by(user_id=user_id).count(),
        "storage": db.session.query(db.func.sum(Document.file_size))
        .filter_by(user_id=user_id)
        .scalar()
        or 0,
    }

    # Последние документы пользователя
    recent_documents = (
        Document.query.filter_by(user_id=user_id)
        .order_by(Document.created_at.desc())
        .limit(10)
        .all()
    )

    return render_template(
        "admin/user.html",
        user=user,
        stats=user_stats,
        recent_documents=recent_documents,
    )


@admin_bp.route("/user/toggle_active/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def toggle_user_active(user_id):
    """
    Активация/деактивация пользователя.
    """
    user = User.query.get_or_404(user_id)

    # Нельзя деактивировать самого себя
    if user.id == current_user.id:
        flash("Вы не можете деактивировать собственный аккаунт", "warning")
        return redirect(url_for("admin.users"))

    try:
        user.is_active = not user.is_active
        db.session.commit()

        status = "активирован" if user.is_active else "деактивирован"
        logger.info(
            f"Пользователь {status}: user_id={user_id}, by_admin={current_user.id}"
        )
        flash(f"Пользователь {user.username} {status}", "success")

    except Exception as e:
        db.session.rollback()
        logger.error(
            f"Ошибка при изменении статуса пользователя: {str(e)}", exc_info=True
        )
        flash("Ошибка при изменении статуса пользователя", "danger")

    return redirect(url_for("admin.users"))


@admin_bp.route("/user/toggle_admin/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def toggle_user_admin(user_id):
    """
    Назначение/снятие прав администратора.
    """
    user = User.query.get_or_404(user_id)

    # Нельзя снять права у самого себя
    if user.id == current_user.id:
        flash("Вы не можете изменить собственные права администратора", "warning")
        return redirect(url_for("admin.users"))

    try:
        user.is_admin = not user.is_admin
        db.session.commit()

        status = "назначены" if user.is_admin else "сняты"
        logger.info(
            f"Права администратора {status}: user_id={user_id}, by_admin={current_user.id}"
        )
        flash(f"Права администратора для {user.username} {status}", "success")

    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при изменении прав: {str(e)}", exc_info=True)
        flash("Ошибка при изменении прав администратора", "danger")

    return redirect(url_for("admin.users"))


@admin_bp.route("/user/delete/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    """
    Удаление пользователя и всех его данных.
    """
    user = User.query.get_or_404(user_id)

    # Нельзя удалить самого себя
    if user.id == current_user.id:
        flash("Вы не можете удалить собственный аккаунт", "warning")
        return redirect(url_for("admin.users"))

    try:
        username = user.username

        # Удаляем пользователя (связанные документы и папки удалятся автоматически)
        db.session.delete(user)
        db.session.commit()

        logger.info(
            f"Пользователь удален: user_id={user_id}, username={username}, by_admin={current_user.id}"
        )
        flash(f"Пользователь {username} и все его данные удалены", "success")

    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при удалении пользователя: {str(e)}", exc_info=True)
        flash("Ошибка при удалении пользователя", "danger")

    return redirect(url_for("admin.users"))


@admin_bp.route("/documents")
@login_required
@admin_required
def documents():
    """
    Просмотр всех документов в системе.
    """
    # Получаем параметры
    search_query = request.args.get("q", "").strip()
    user_filter = request.args.get("user_id", type=int)

    # Базовый запрос
    query = Document.query

    # Фильтр по пользователю
    if user_filter:
        query = query.filter_by(user_id=user_filter)

    # Поиск
    if search_query:
        query = query.filter(
            db.or_(
                Document.title.ilike(f"%{search_query}%"),
                Document.description.ilike(f"%{search_query}%"),
            )
        )

    # Сортировка
    query = query.order_by(Document.created_at.desc())

    # Выполняем запрос
    documents_list = query.all()

    # Список пользователей для фильтра
    users_list = User.query.order_by(User.username).all()

    return render_template(
        "admin/documents.html",
        documents=documents_list,
        users=users_list,
        search_query=search_query,
        user_filter=user_filter,
    )


@admin_bp.route("/statistics")
@login_required
@admin_required
def statistics():
    """
    Детальная статистика системы.
    """
    # Общая статистика
    total_stats = {
        "users": User.query.count(),
        "documents": Document.query.count(),
        "folders": Folder.query.count(),
        "storage_bytes": db.session.query(db.func.sum(Document.file_size)).scalar()
        or 0,
    }

    # Статистика за последние 30 дней
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)

    recent_stats = {
        "new_users": User.query.filter(User.created_at >= thirty_days_ago).count(),
        "new_documents": Document.query.filter(
            Document.created_at >= thirty_days_ago
        ).count(),
    }

    # Топ пользователей по количеству документов
    top_users = (
        db.session.query(User, db.func.count(Document.id).label("doc_count"))
        .join(Document)
        .group_by(User.id)
        .order_by(db.desc("doc_count"))
        .limit(10)
        .all()
    )

    return render_template(
        "admin/statistics.html",
        total_stats=total_stats,
        recent_stats=recent_stats,
        top_users=top_users,
    )
