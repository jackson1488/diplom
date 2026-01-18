# routes/scanner.py
"""
Маршруты для сканирования документов.
Использует EasyOCR и PyMuPDF - без внешних зависимостей
"""

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    current_app,
)
from flask_login import current_user
from werkzeug.utils import secure_filename
import os
import base64
import logging
from io import BytesIO
from PIL import Image

from models import db
from models.folder import Folder
from models.document import Document
from utils.decorators import login_required
from services.document_service import DocumentService
from services.ocr_service import OCRService
from services.pdf_service import PDFService

logger = logging.getLogger(__name__)

scanner_bp = Blueprint("scanner", __name__, url_prefix="/scanner")


@scanner_bp.route("/")
@login_required
def index():
    """Главная страница сканера"""
    return render_template("scanner/scan.html")


@scanner_bp.route("/camera")
@login_required
def camera():
    """Страница сканирования через веб-камеру"""
    return render_template("scanner/camera.html")


@scanner_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    """Загрузка файла"""
    if request.method == "GET":
        folders = (
            Folder.query.filter_by(user_id=current_user.id).order_by(Folder.name).all()
        )
        return render_template("scanner/upload.html", folders=folders)

    try:
        # Проверяем файл
        if "file" not in request.files:
            return jsonify({"success": False, "error": "Файл не выбран"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"success": False, "error": "Файл не выбран"}), 400

        # Получаем параметры
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        folder_id = request.form.get("folder_id", type=int)
        perform_ocr = request.form.get("auto_ocr", "true") == "true"

        # Если название не указано
        if not title:
            title = os.path.splitext(secure_filename(file.filename))[0]

        # Проверяем расширение
        filename = secure_filename(file.filename)
        file_extension = os.path.splitext(filename)[1].lower()

        allowed_extensions = current_app.config["ALLOWED_EXTENSIONS"]
        if file_extension.lstrip(".") not in allowed_extensions:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"Формат {file_extension} не поддерживается",
                    }
                ),
                400,
            )

        # Создаем папки для пользователя
        upload_folder = current_app.config["UPLOAD_FOLDER"]
        user_folder = os.path.join(upload_folder, str(current_user.id))
        os.makedirs(user_folder, exist_ok=True)

        # Генерируем уникальное имя
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename_str = f"{timestamp}_{filename}"
        file_path = os.path.join(user_folder, safe_filename_str)

        # Сохраняем файл
        file.save(file_path)

        # Получаем размер файла
        file_size = os.path.getsize(file_path)

        # Создаем запись в БД
        document = Document(
            user_id=current_user.id,
            title=title,
            description=description,
            original_filename=filename,
            file_path=file_path,
            file_size=file_size,
            file_extension=file_extension,
            mime_type=file.content_type,
            folder_id=folder_id if folder_id else None,
        )

        db.session.add(document)
        db.session.flush()  # Получаем ID

        # Создаем миниатюру
        thumbnail_folder = os.path.join(
            current_app.config["THUMBNAIL_FOLDER"], str(current_user.id)
        )
        os.makedirs(thumbnail_folder, exist_ok=True)

        thumbnail_filename = f"thumb_{document.id}.jpg"
        thumbnail_path = os.path.join(thumbnail_folder, thumbnail_filename)

        try:
            if file_extension in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"]:
                # Для изображений
                img = Image.open(file_path)
                img.thumbnail(
                    current_app.config["THUMBNAIL_SIZE"], Image.Resampling.LANCZOS
                )
                img.save(thumbnail_path, "JPEG", quality=85)

                # ВАЖНО! Сохраняем относительный путь
                document.thumbnail_path = os.path.join(
                    str(current_user.id), thumbnail_filename
                )

            elif file_extension == ".pdf":
                # Для PDF
                thumb_path = PDFService.create_thumbnail(
                    file_path, thumbnail_path, size=current_app.config["THUMBNAIL_SIZE"]
                )
                if thumb_path:
                    document.thumbnail_path = os.path.join(
                        str(current_user.id), thumbnail_filename
                    )

        except Exception as e:
            logger.warning(f"Не удалось создать миниатюру: {e}")

        # Запускаем OCR
        if perform_ocr:
            document.ocr_status = "processing"
            db.session.commit()

            try:
                if file_extension == ".pdf":
                    # PDF OCR
                    text = PDFService.extract_text_from_pdf(file_path)
                else:
                    # Image OCR
                    text = OCRService.extract_text(file_path)

                if text and text.strip():
                    document.ocr_text = text
                    document.content = text
                    document.ocr_status = "completed"
                    logger.info(f"OCR завершен: {len(text)} символов")
                else:
                    document.ocr_status = "failed"
                    document.ocr_error = "Текст не найден"

            except Exception as e:
                logger.error(f"Ошибка OCR: {e}")
                document.ocr_status = "failed"
                document.ocr_error = str(e)

        db.session.commit()

        logger.info(f"Документ {document.id} загружен пользователем {current_user.id}")

        return jsonify(
            {
                "success": True,
                "document_id": document.id,
                "redirect": url_for("documents.view_document", document_id=document.id),
            }
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка загрузки: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@scanner_bp.route("/capture", methods=["POST"])
@login_required
def capture():
    """Обработка снимка с камеры"""
    try:
        # Получаем данные
        image_data = request.json.get("image")
        title = request.json.get("title", "Скан с камеры")

        # ИСПРАВЛЕНО: убираем type=int
        folder_id = request.json.get("folder_id")
        if folder_id:
            folder_id = int(folder_id)
        else:
            folder_id = None

        perform_ocr = request.json.get("auto_ocr", True)

        if not image_data:
            return (
                jsonify({"success": False, "error": "Изображение не предоставлено"}),
                400,
            )

        # ... остальной код без изменений ...

        # Декодируем base64
        if "base64," in image_data:
            image_data = image_data.split("base64,")[1]

        image_bytes = base64.b64decode(image_data)
        image = Image.open(BytesIO(image_bytes))

        # Создаем папки
        upload_folder = current_app.config["UPLOAD_FOLDER"]
        user_folder = os.path.join(upload_folder, str(current_user.id))
        os.makedirs(user_folder, exist_ok=True)

        # Генерируем имя файла
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"camera_{timestamp}.jpg"
        file_path = os.path.join(user_folder, filename)

        # Сохраняем
        image.save(file_path, "JPEG", quality=85)
        file_size = os.path.getsize(file_path)

        # Создаем документ
        document = Document(
            user_id=current_user.id,
            title=title,
            original_filename=filename,
            file_path=file_path,
            file_size=file_size,
            file_extension=".jpg",
            mime_type="image/jpeg",
            folder_id=folder_id if folder_id else None,
        )

        db.session.add(document)
        db.session.flush()

        # Миниатюра
        thumbnail_folder = os.path.join(
            current_app.config["THUMBNAIL_FOLDER"], str(current_user.id)
        )
        os.makedirs(thumbnail_folder, exist_ok=True)

        thumbnail_filename = f"thumb_{document.id}.jpg"
        thumbnail_path = os.path.join(thumbnail_folder, thumbnail_filename)

        thumb_img = image.copy()
        thumb_img.thumbnail(
            current_app.config["THUMBNAIL_SIZE"], Image.Resampling.LANCZOS
        )
        thumb_img.save(thumbnail_path, "JPEG", quality=85)

        # Сохраняем относительный путь
        document.thumbnail_path = os.path.join(
            "thumbnail", str(current_user.id), thumbnail_filename
        )

        # OCR
        if perform_ocr:
            document.ocr_status = "processing"
            db.session.commit()

            try:
                text = OCRService.extract_text(file_path)
                if text and text.strip():
                    document.ocr_text = text
                    document.content = text
                    document.ocr_status = "completed"
                else:
                    document.ocr_status = "failed"
                    document.ocr_error = "Текст не найден"
            except Exception as e:
                logger.error(f"Ошибка OCR: {e}")
                document.ocr_status = "failed"
                document.ocr_error = str(e)

        db.session.commit()

        logger.info(f"Снимок с камеры сохранен: doc_id={document.id}")

        return jsonify(
            {
                "success": True,
                "document_id": document.id,
                "redirect_url": url_for(
                    "documents.view_document", document_id=document.id
                ),
            }
        )

    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка обработки снимка: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
