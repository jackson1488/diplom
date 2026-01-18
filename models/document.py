# models/document.py
"""
Модель документа.
Содержит информацию о документе, его содержимом и метаданных.
"""

from datetime import datetime
from models import db
import os


class Document(db.Model):
    """
    Модель документа в системе.
    Каждый документ принадлежит одному пользователю и может находиться в папке.
    """

    # Название таблицы в базе данных
    __tablename__ = "documents"

    # === ОСНОВНЫЕ ПОЛЯ ===

    # Уникальный идентификатор документа (первичный ключ)
    id = db.Column(db.Integer, primary_key=True)

    # Название документа (обязательное)
    title = db.Column(db.String(256), nullable=False)

    # Описание документа (необязательное)
    description = db.Column(db.Text, nullable=True)

    # === ФАЙЛОВЫЕ ПОЛЯ ===

    # Имя оригинального файла при загрузке
    original_filename = db.Column(db.String(256), nullable=False)

    # Путь к файлу оригинала на сервере (относительный)
    file_path = db.Column(db.String(512), nullable=False)

    # Путь к миниатюре документа
    thumbnail_path = db.Column(db.String(512), nullable=True)

    # Размер файла в байтах
    file_size = db.Column(db.Integer, nullable=True)

    # MIME тип файла (image/jpeg, application/pdf и т.д.)
    mime_type = db.Column(db.String(128), nullable=True)

    # Расширение файла (pdf, jpg, png и т.д.)
    file_extension = db.Column(db.String(10), nullable=False)

    # === СОДЕРЖИМОЕ ДОКУМЕНТА ===

    # Распознанный текст из документа (OCR)
    ocr_text = db.Column(db.Text, nullable=True)

    # Редактируемый текст документа (может отличаться от OCR после правок)
    content = db.Column(db.Text, nullable=True)

    # Статус обработки OCR (pending, processing, completed, failed)
    ocr_status = db.Column(db.String(20), default="pending", nullable=False)

    # Сообщение об ошибке, если OCR не удался
    ocr_error = db.Column(db.Text, nullable=True)

    # Язык документа (автоматически определяется при OCR)
    language = db.Column(db.String(10), nullable=True)

    # Количество страниц (для многостраничных документов)
    page_count = db.Column(db.Integer, default=1, nullable=False)

    # === СВЯЗИ С ДРУГИМИ ТАБЛИЦАМИ ===

    # ID владельца документа (внешний ключ на таблицу users)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )

    # ID папки, в которой находится документ (необязательное, внешний ключ на таблицу folders)
    folder_id = db.Column(
        db.Integer, db.ForeignKey("folders.id"), nullable=True, index=True
    )

    # === МЕТАДАННЫЕ ===

    # Теги документа (через запятую, например: "договор, работа, 2026")
    tags = db.Column(db.String(512), nullable=True)

    # Флаг избранного
    is_favorite = db.Column(db.Boolean, default=False, nullable=False)

    # Флаг архивного документа (скрыт из основного списка)
    is_archived = db.Column(db.Boolean, default=False, nullable=False)

    # === ВРЕМЕННЫЕ МЕТКИ ===

    # Дата и время создания документа
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, nullable=False, index=True
    )

    # Дата и время последнего обновления
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Дата и время последнего просмотра (для статистики)
    last_viewed = db.Column(db.DateTime, nullable=True)

    # === МЕТОДЫ ===

    def get_file_size_mb(self):
        """
        Возвращает размер файла в мегабайтах.

        Returns:
            Число с плавающей точкой - размер в МБ
        """
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0

    def get_tags_list(self):
        """
        Возвращает список тегов документа.

        Returns:
            Список строк - теги
        """
        if self.tags:
            return [tag.strip() for tag in self.tags.split(",") if tag.strip()]
        return []

    def add_tag(self, tag):
        """
        Добавляет тег к документу.

        Args:
            tag: строка - новый тег
        """
        tags_list = self.get_tags_list()
        if tag not in tags_list:
            tags_list.append(tag)
            self.tags = ", ".join(tags_list)

    def remove_tag(self, tag):
        """
        Удаляет тег из документа.

        Args:
            tag: строка - тег для удаления
        """
        tags_list = self.get_tags_list()
        if tag in tags_list:
            tags_list.remove(tag)
            self.tags = ", ".join(tags_list)

    def update_last_viewed(self):
        """
        Обновляет время последнего просмотра документа.
        """
        self.last_viewed = datetime.utcnow()
        db.session.commit()

    def get_absolute_file_path(self, base_dir):
        """
        Возвращает абсолютный путь к файлу документа.

        Args:
            base_dir: базовая директория проекта

        Returns:
            Строка - абсолютный путь к файлу
        """
        return os.path.join(base_dir, self.file_path)

    def get_absolute_thumbnail_path(self, base_dir):
        """
        Возвращает абсолютный путь к миниатюре документа.

        Args:
            base_dir: базовая директория проекта

        Returns:
            Строка - абсолютный путь к миниатюре или None
        """
        if self.thumbnail_path:
            return os.path.join(base_dir, self.thumbnail_path)
        return None

    def is_image(self):
        """
        Проверяет, является ли документ изображением.

        Returns:
            True если документ - изображение, False в противном случае
        """
        return self.file_extension.lower() in ["jpg", "jpeg", "png", "gif", "bmp"]

    def is_pdf(self):
        """
        Проверяет, является ли документ PDF файлом.

        Returns:
            True если документ - PDF, False в противном случае
        """
        return self.file_extension.lower() == "pdf"

    def can_ocr(self):
        """
        Проверяет, можно ли применить OCR к документу.

        Returns:
            True если документ поддерживает OCR, False в противном случае
        """
        return self.is_image() or self.is_pdf()

    def to_dict(self):
        """
        Преобразует объект документа в словарь.
        Полезно для API и сериализации.

        Returns:
            Словарь с данными документа
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "original_filename": self.original_filename,
            "file_path": self.file_path,
            "thumbnail_path": self.thumbnail_path,
            "file_size": self.file_size,
            "file_size_mb": self.get_file_size_mb(),
            "mime_type": self.mime_type,
            "file_extension": self.file_extension,
            "ocr_status": self.ocr_status,
            "language": self.language,
            "page_count": self.page_count,
            "user_id": self.user_id,
            "folder_id": self.folder_id,
            "tags": self.get_tags_list(),
            "is_favorite": self.is_favorite,
            "is_archived": self.is_archived,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_viewed": self.last_viewed.isoformat() if self.last_viewed else None,
        }

    def __repr__(self):
        """
        Строковое представление объекта для отладки.
        """
        return f"<Document {self.title} (User: {self.user_id})>"
