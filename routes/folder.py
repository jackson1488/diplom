"""
Маршруты для работы с папками
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user
from datetime import datetime
import logging

from models import db
from models.folder import Folder
from models.document import Document
from utils.decorators import login_required

folder_bp = Blueprint("folder", __name__, url_prefix="/folders")
logger = logging.getLogger(__name__)


@folder_bp.route("/")
@folder_bp.route("/list")
@login_required
def list():
    """Список всех папок пользователя"""
    folders = (
        Folder.query.filter_by(user_id=current_user.id).order_by(Folder.name).all()
    )
    folders_with_count = []

    for folder in folders:
        doc_count = Document.query.filter_by(
            folder_id=folder.id, is_archived=False
        ).count()
        folders_with_count.append({"folder": folder, "doc_count": doc_count})

    return render_template("folders/list.html", folders=folders_with_count)


@folder_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    """Создание новой папки"""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        color = request.form.get("color", "#6c757d")

        if not name:
            flash("Название папки обязательно", "error")
            return redirect(url_for("folder.create"))

        # Создаем папку
        folder = Folder(
            user_id=current_user.id, name=name, description=description, color=color
        )

        db.session.add(folder)
        db.session.commit()

        flash("Папка успешно создана", "success")
        logger.info(f"User {current_user.id} created folder '{name}'")

        return redirect(url_for("folder.list"))

    return render_template("folders/create.html")


@folder_bp.route("/edit/<int:folder_id>", methods=["GET", "POST"])
@login_required
def edit(folder_id):
    """Редактирование папки"""
    folder = Folder.query.filter_by(
        id=folder_id, user_id=current_user.id
    ).first_or_404()

    if request.method == "POST":
        folder.name = request.form.get("name", "").strip()
        folder.description = request.form.get("description", "").strip()
        folder.color = request.form.get("color", "#6c757d")

        if not folder.name:
            flash("Название папки обязательно", "error")
            return redirect(url_for("folder.edit", folder_id=folder_id))

        db.session.commit()
        flash("Папка обновлена", "success")

        return redirect(url_for("folder.list"))

    return render_template("folders/edit.html", folder=folder)


@folder_bp.route("/delete/<int:folder_id>", methods=["POST"])
@login_required
def delete(folder_id):
    """Удаление папки"""
    folder = Folder.query.filter_by(
        id=folder_id, user_id=current_user.id
    ).first_or_404()

    try:
        # Открепляем документы от папки
        documents = Document.query.filter_by(folder_id=folder_id).all()
        for doc in documents:
            doc.folder_id = None

        # Удаляем папку
        db.session.delete(folder)
        db.session.commit()

        logger.info(f"User {current_user.id} deleted folder {folder_id}")
        return jsonify({"success": True, "message": "Папка удалена"})

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting folder {folder_id}: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@folder_bp.route("/view/<int:folder_id>")
@login_required
def view(folder_id):
    """Просмотр документов в папке"""
    folder = Folder.query.filter_by(
        id=folder_id, user_id=current_user.id
    ).first_or_404()

    documents = (
        Document.query.filter_by(folder_id=folder_id, is_archived=False)
        .order_by(Document.upload_date.desc())
        .all()
    )

    return render_template("folders/view.html", folder=folder, documents=documents)
