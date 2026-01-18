"""
Сервис для работы с PDF
Использует PyMuPDF (fitz) вместо pdf2image - не требует Poppler
"""

import os
import io
import logging
import fitz  # PyMuPDF
from PIL import Image
from services.ocr_service import OCRService

logger = logging.getLogger(__name__)


class PDFService:
    """Сервис для обработки PDF документов"""

    @staticmethod
    def pdf_to_images(pdf_path, dpi=300):
        """
        Конвертирует PDF в изображения (БЕЗ Poppler)

        Args:
            pdf_path: путь к PDF файлу
            dpi: качество изображений (default 300)

        Returns:
            list: список PIL Image объектов
        """
        images = []

        try:
            pdf = fitz.open(pdf_path)
            zoom = dpi / 72  # 72 DPI - стандарт PDF
            matrix = fitz.Matrix(zoom, zoom)

            logger.info(f"Конвертирую PDF: {len(pdf)} страниц...")

            for page_num in range(len(pdf)):
                page = pdf[page_num]
                pix = page.get_pixmap(matrix=matrix)

                # Конвертируем в PIL Image
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                images.append(img)

                logger.info(f"Страница {page_num + 1}/{len(pdf)} конвертирована")

            pdf.close()
            logger.info(f"✓ PDF конвертирован: {len(images)} страниц")

        except Exception as e:
            logger.error(f"Ошибка конвертации PDF: {e}")

        return images

    @staticmethod
    def extract_text_from_pdf(pdf_path):
        """
        Извлекает текст из PDF
        Сначала пробует текстовый слой, потом OCR

        Args:
            pdf_path: путь к PDF файлу

        Returns:
            str: извлеченный текст
        """
        try:
            # Пробуем извлечь текст напрямую
            pdf = fitz.open(pdf_path)
            text = ""

            for page in pdf:
                text += page.get_text()

            pdf.close()

            # Если есть текст - возвращаем
            if text.strip():
                logger.info(f"Текст извлечен напрямую: {len(text)} символов")
                return text

            # Иначе используем OCR
            logger.info("Текстовый слой не найден, запускаю OCR...")
            images = PDFService.pdf_to_images(pdf_path)

            all_text = []
            for i, img in enumerate(images):
                logger.info(f"OCR страницы {i + 1}/{len(images)}...")
                page_text = OCRService.extract_text(img)
                all_text.append(page_text)

            final_text = "\n\n".join(all_text)
            logger.info(f"✓ OCR завершен: {len(final_text)} символов")

            return final_text

        except Exception as e:
            logger.error(f"Ошибка обработки PDF: {e}")
            return ""

    @staticmethod
    def get_pdf_info(pdf_path):
        """
        Получает информацию о PDF документе

        Args:
            pdf_path: путь к PDF

        Returns:
            dict: метаданные документа
        """
        try:
            pdf = fitz.open(pdf_path)

            info = {
                "page_count": len(pdf),
                "title": pdf.metadata.get("title", "") or "",
                "author": pdf.metadata.get("author", "") or "",
                "subject": pdf.metadata.get("subject", "") or "",
                "keywords": pdf.metadata.get("keywords", "") or "",
                "creator": pdf.metadata.get("creator", "") or "",
                "producer": pdf.metadata.get("producer", "") or "",
            }

            pdf.close()
            logger.info(f"PDF info: {info['page_count']} страниц")
            return info

        except Exception as e:
            logger.error(f"Ошибка получения info: {e}")
            return {"page_count": 0}

    @staticmethod
    def extract_images_from_pdf(pdf_path, output_folder):
        """
        Извлекает все изображения из PDF

        Args:
            pdf_path: путь к PDF
            output_folder: папка для сохранения

        Returns:
            list: список путей к извлеченным изображениям
        """
        extracted_images = []

        try:
            os.makedirs(output_folder, exist_ok=True)
            pdf = fitz.open(pdf_path)

            for page_num in range(len(pdf)):
                page = pdf[page_num]
                image_list = page.get_images()

                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = pdf.extract_image(xref)
                    image_bytes = base_image["image"]

                    # Сохраняем изображение
                    image_filename = f"page_{page_num + 1}_img_{img_index + 1}.png"
                    image_path = os.path.join(output_folder, image_filename)

                    with open(image_path, "wb") as img_file:
                        img_file.write(image_bytes)

                    extracted_images.append(image_path)

            pdf.close()
            logger.info(f"✓ Извлечено {len(extracted_images)} изображений")

        except Exception as e:
            logger.error(f"Ошибка извлечения изображений: {e}")

        return extracted_images

    @staticmethod
    def create_thumbnail(pdf_path, output_path, size=(200, 200)):
        """
        Создает миниатюру первой страницы PDF

        Args:
            pdf_path: путь к PDF
            output_path: путь для сохранения миниатюры
            size: размер миниатюры (width, height)

        Returns:
            str: путь к созданной миниатюре или None
        """
        try:
            pdf = fitz.open(pdf_path)

            if len(pdf) == 0:
                logger.warning("PDF пустой")
                return None

            # Берем первую страницу
            page = pdf[0]

            # Рендерим в небольшое изображение
            zoom = 0.5  # Меньше чем обычно для миниатюры
            matrix = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=matrix)

            # Конвертируем в PIL
            img_data = pix.tobytes("png")
            img = Image.open(io.BytesIO(img_data))

            # Создаем миниатюру
            img.thumbnail(size, Image.Resampling.LANCZOS)

            # Сохраняем
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            img.save(output_path, "PNG")

            pdf.close()
            logger.info(f"✓ Миниатюра создана: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Ошибка создания миниатюры: {e}")
            return None

    @staticmethod
    def merge_pdfs(pdf_paths, output_path):
        """
        Объединяет несколько PDF в один

        Args:
            pdf_paths: список путей к PDF
            output_path: путь для результата

        Returns:
            bool: успех операции
        """
        try:
            result = fitz.open()

            for pdf_path in pdf_paths:
                pdf = fitz.open(pdf_path)
                result.insert_pdf(pdf)
                pdf.close()

            result.save(output_path)
            result.close()

            logger.info(f"✓ PDF объединены: {len(pdf_paths)} файлов -> {output_path}")
            return True

        except Exception as e:
            logger.error(f"Ошибка объединения PDF: {e}")
            return False

    @staticmethod
    def split_pdf(pdf_path, output_folder):
        """
        Разделяет PDF на отдельные страницы

        Args:
            pdf_path: путь к PDF
            output_folder: папка для сохранения

        Returns:
            list: список путей к созданным PDF
        """
        split_files = []

        try:
            os.makedirs(output_folder, exist_ok=True)
            pdf = fitz.open(pdf_path)

            for page_num in range(len(pdf)):
                # Создаем новый PDF с одной страницей
                new_pdf = fitz.open()
                new_pdf.insert_pdf(pdf, from_page=page_num, to_page=page_num)

                # Сохраняем
                output_path = os.path.join(output_folder, f"page_{page_num + 1}.pdf")
                new_pdf.save(output_path)
                new_pdf.close()

                split_files.append(output_path)

            pdf.close()
            logger.info(f"✓ PDF разделен на {len(split_files)} файлов")

        except Exception as e:
            logger.error(f"Ошибка разделения PDF: {e}")

        return split_files
