# services/document_service.py
"""
Сервис для управления документами.
Содержит бизнес-логику создания, обновления, удаления документов.
"""

import os
import shutil
import uuid
from datetime import datetime
from typing import Optional, List, Tuple
from werkzeug.utils import secure_filename
import logging

from models import db
from models.document import Document
from models.folder import Folder

# Настраиваем логирование
logger = logging.getLogger(__name__)


class DocumentService:
    """
    Сервис для управления документами пользователей.
    """

    def __init__(self, upload_folder: str, allowed_extensions: set):
        """
        Инициализация сервиса документов.

        Args:
            upload_folder: базовая папка для загрузки файлов
            allowed_extensions: множество разрешенных расширений файлов
        """
        self.upload_folder = upload_folder
        self.allowed_extensions = allowed_extensions

        logger.info(f"DocumentService инициализирован: upload_folder={upload_folder}")

    def is_allowed_file(self, filename: str) -> bool:
        """
        Проверяет, разрешено ли расширение файла.

        Args:
            filename: имя файла

        Returns:
            True если расширение разрешено, False в противном случае
        """
        return (
            "." in filename
            and filename.rsplit(".", 1)[1].lower() in self.allowed_extensions
        )

    def save_uploaded_file(
        self, file, user_id: int
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Сохраняет загруженный файл на сервер.

        Args:
            file: файл из запроса (werkzeug FileStorage)
            user_id: ID пользователя, загружающего файл

        Returns:
            Кортеж (относительный_путь, расширение) или (None, None) при ошибке
        """
        try:
            # Проверяем, что файл предоставлен
            if not file or file.filename == "":
                logger.error("Файл не предоставлен")
                return None, None

            # Проверяем расширение файла
            if not self.is_allowed_file(file.filename):
                logger.error(f"Недопустимое расширение файла: {file.filename}")
                return None, None

            # Получаем безопасное имя файла
            original_filename = secure_filename(file.filename)
            file_extension = original_filename.rsplit(".", 1)[1].lower()

            # Генерируем уникальное имя файла
            unique_filename = f"{user_id}_{uuid.uuid4().hex}.{file_extension}"

            # Формируем путь для сохранения
            user_folder = os.path.join(self.upload_folder, "originals", str(user_id))
            os.makedirs(user_folder, exist_ok=True)

            file_path = os.path.join(user_folder, unique_filename)

            # Сохраняем файл
            file.save(file_path)

            # Формируем относительный путь (от базовой директории проекта)
            relative_path = os.path.join(
                "uploads", "originals", str(user_id), unique_filename
            )

            logger.info(f"Файл сохранен: {relative_path}")
            return relative_path, file_extension

        except Exception as e:
            logger.error(f"Ошибка при сохранении файла: {str(e)}", exc_info=True)
            return None, None

    def create_document(
        self,
        user_id: int,
        title: str,
        file_path: str,
        original_filename: str,
        file_extension: str,
        folder_id: Optional[int] = None,
        description: Optional[str] = None,
    ) -> Optional[Document]:
        """
        Создает новый документ в базе данных.

        Args:
            user_id: ID пользователя-владельца
            title: название документа
            file_path: путь к файлу
            original_filename: оригинальное имя файла
            file_extension: расширение файла
            folder_id: ID папки (опционально)
            description: описание документа (опционально)

        Returns:
            Объект Document или None при ошибке
        """
        try:
            logger.info(f"Создание документа: {title} для пользователя {user_id}")

            # Получаем размер файла
            absolute_path = os.path.join(os.getcwd(), file_path)
            file_size = (
                os.path.getsize(absolute_path)
                if os.path.exists(absolute_path)
                else None
            )

            # Создаем объект документа
            document = Document(
                title=title,
                description=description,
                original_filename=original_filename,
                file_path=file_path,
                file_size=file_size,
                file_extension=file_extension,
                user_id=user_id,
                folder_id=folder_id,
                ocr_status="pending",
            )

            # Сохраняем в базу данных
            db.session.add(document)
            db.session.commit()

            logger.info(f"Документ создан с ID: {document.id}")
            return document

        except Exception as e:
            logger.error(f"Ошибка при создании документа: {str(e)}", exc_info=True)
            db.session.rollback()
            return None

    def get_user_documents(
        self,
        user_id: int,
        folder_id: Optional[int] = None,
        is_archived: bool = False,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> List[Document]:
        """
        Получает список документов пользователя с фильтрацией и сортировкой.

        Args:
            user_id: ID пользователя
            folder_id: ID папки для фильтрации (None - все документы)
            is_archived: показывать архивные документы
            sort_by: поле для сортировки
            order: порядок сортировки ('asc' или 'desc')

        Returns:
            Список документов
        """
        try:
            # Базовый запрос
            query = Document.query.filter_by(user_id=user_id, is_archived=is_archived)

            # Фильтр по папке
            if folder_id is not None:
                query = query.filter_by(folder_id=folder_id)

            # Сортировка
            if hasattr(Document, sort_by):
                order_column = getattr(Document, sort_by)
                if order == "desc":
                    query = query.order_by(order_column.desc())
                else:
                    query = query.order_by(order_column.asc())

            documents = query.all()
            logger.info(
                f"Получено {len(documents)} документов для пользователя {user_id}"
            )

            return documents

        except Exception as e:
            logger.error(f"Ошибка при получении документов: {str(e)}", exc_info=True)
            return []

    def delete_document(self, document_id: int, user_id: int) -> bool:
        """
        Удаляет документ и связанные файлы.

        Args:
            document_id: ID документа
            user_id: ID пользователя (для проверки прав)

        Returns:
            True если документ удален успешно, False при ошибке
        """
        try:
            logger.info(f"Удаление документа ID: {document_id}")

            # Получаем документ
            document = Document.query.filter_by(id=document_id, user_id=user_id).first()

            if not document:
                logger.error(f"Документ не найден или нет прав: {document_id}")
                return False

            # Удаляем файлы с диска
            try:
                # Удаляем оригинал
                if document.file_path and os.path.exists(document.file_path):
                    os.remove(document.file_path)
                    logger.info(f"Удален файл: {document.file_path}")

                # Удаляем миниатюру
                if document.thumbnail_path and os.path.exists(document.thumbnail_path):
                    os.remove(document.thumbnail_path)
                    logger.info(f"Удалена миниатюра: {document.thumbnail_path}")

            except OSError as e:
                logger.warning(f"Ошибка при удалении файлов с диска: {str(e)}")

            # Удаляем запись из базы данных
            db.session.delete(document)
            db.session.commit()

            logger.info(f"Документ успешно удален: {document_id}")
            return True

        except Exception as e:
            logger.error(f"Ошибка при удалении документа: {str(e)}", exc_info=True)
            db.session.rollback()
            return False

    def move_document_to_folder(
        self, document_id: int, folder_id: Optional[int], user_id: int
    ) -> bool:
        """
        Перемещает документ в другую папку.

        Args:
            document_id: ID документа
            folder_id: ID целевой папки (None - переместить в корень)
            user_id: ID пользователя (для проверки прав)

        Returns:
            True если документ перемещен успешно, False при ошибке
        """
        try:
            logger.info(f"Перемещение документа {document_id} в папку {folder_id}")

            # Получаем документ
            document = Document.query.filter_by(id=document_id, user_id=user_id).first()

            if not document:
                logger.error(f"Документ не найден: {document_id}")
                return False

            # Если указана папка, проверяем ее существование и принадлежность пользователю
            if folder_id is not None:
                folder = Folder.query.filter_by(id=folder_id, user_id=user_id).first()
                if not folder:
                    logger.error(f"Папка не найдена: {folder_id}")
                    return False

            # Перемещаем документ
            document.folder_id = folder_id
            document.updated_at = datetime.utcnow()
            db.session.commit()

            logger.info(f"Документ успешно перемещен")
            return True

        except Exception as e:
            logger.error(f"Ошибка при перемещении документа: {str(e)}", exc_info=True)
            db.session.rollback()
            return False
