# routes/editor.py
"""
Маршруты для редактирования документов.
Включает текстовый редактор с поддержкой форматирования.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import current_user
import logging
import os

from models import db
from models.document import Document
from utils.decorators import login_required

# Настраиваем логирование
logger = logging.getLogger(__name__)

# Создаем blueprint для маршрутов редактора
editor_bp = Blueprint("editor", __name__)


@editor_bp.route("/<int:document_id>")
@login_required
def edit_document(document_id):
    """
    Страница редактора документа.
    Отображает интерфейс редактирования с панелью инструментов.
    """
    # Получаем документ
    document = Document.query.filter_by(id=document_id, user_id=current_user.id).first()

    if not document:
        flash("Документ не найден", "danger")
        return redirect(url_for("documents.library"))

    logger.info(f"Открытие редактора: doc_id={document_id}, user_id={current_user.id}")

    return render_template("editor/edit.html", document=document)


@editor_bp.route("/save/<int:document_id>", methods=["POST"])
@login_required
def save_document(document_id):
    """
    Сохранение изменений документа.
    Принимает содержимое в формате HTML или plain text.
    """
    # Получаем документ
    document = Document.query.filter_by(id=document_id, user_id=current_user.id).first()

    if not document:
        return jsonify({"success": False, "error": "Документ не найден"}), 404

    # Получаем содержимое из запроса
    content = (
        request.json.get("content", "")
        if request.is_json
        else request.form.get("content", "")
    )

    if content is None:
        return jsonify({"success": False, "error": "Содержимое не предоставлено"}), 400

    try:
        # Сохраняем содержимое
        document.content = content
        db.session.commit()

        logger.info(f"Документ сохранен: doc_id={document_id}, length={len(content)}")

        if request.is_json:
            return jsonify(
                {
                    "success": True,
                    "message": "Документ сохранен",
                    "updated_at": document.updated_at.isoformat(),
                }
            )
        else:
            flash("Документ успешно сохранен", "success")
            return redirect(url_for("editor.edit_document", document_id=document_id))

    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при сохранении документа: {str(e)}", exc_info=True)

        if request.is_json:
            return jsonify({"success": False, "error": "Ошибка при сохранении"}), 500
        else:
            flash("Ошибка при сохранении документа", "danger")
            return redirect(url_for("editor.edit_document", document_id=document_id))


@editor_bp.route("/autosave/<int:document_id>", methods=["POST"])
@login_required
def autosave(document_id):
    """
    Автоматическое сохранение документа.
    Вызывается JavaScript каждые N секунд.
    """
    document = Document.query.filter_by(id=document_id, user_id=current_user.id).first()

    if not document:
        return jsonify({"success": False, "error": "Документ не найден"}), 404

    content = request.json.get("content", "")

    try:
        document.content = content
        db.session.commit()

        logger.debug(f"Автосохранение: doc_id={document_id}")

        return jsonify({"success": True, "saved_at": document.updated_at.isoformat()})

    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка автосохранения: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@editor_bp.route("/rerun_ocr/<int:doc_id>", methods=["POST"])
@login_required
def rerun_ocr(doc_id):
    """Повторный запуск OCR для документа"""
    try:
        document = Document.query.filter_by(
            id=doc_id, user_id=current_user.id
        ).first_or_404()

        # Проверяем файл
        if not os.path.exists(document.file_path):
            return jsonify({"success": False, "error": "Файл не найден"}), 404

        # Обновляем статус
        document.ocr_status = "processing"
        db.session.commit()

        # Запускаем OCR (БЕЗ Tesseract!)
        from services.ocr_service import OCRService
        from services.pdf_service import PDFService

        try:
            # Если PDF
            if document.file_extension == ".pdf":
                text = PDFService.extract_text_from_pdf(document.file_path)
            else:
                # Если изображение
                text = OCRService.extract_text(document.file_path)

            if text and text.strip():
                document.ocr_text = text
                document.content = text
                document.ocr_status = "completed"
                document.ocr_error = None

                db.session.commit()

                logger.info(f"OCR повторно выполнен для документа {doc_id}")

                return jsonify(
                    {"success": True, "text": text, "message": "OCR успешно выполнен"}
                )
            else:
                document.ocr_status = "failed"
                document.ocr_error = "Текст не найден"
                db.session.commit()

                return jsonify({"success": False, "error": "Текст не распознан"}), 400

        except Exception as e:
            document.ocr_status = "failed"
            document.ocr_error = str(e)
            db.session.commit()
            raise

    except Exception as e:
        logger.error(f"Ошибка при повторном OCR: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

    except Exception as e:
        document.ocr_status = "failed"
        document.ocr_error = str(e)
        db.session.commit()

        logger.error(f"Ошибка при повторном OCR: {str(e)}", exc_info=True)
        return jsonify({"success": False, "error": str(e)}), 500
