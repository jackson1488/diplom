"""
PDF обработка БЕЗ Poppler и Tesseract
Использует только Python библиотеки
"""

import io
import fitz  # PyMuPDF
import easyocr
from PIL import Image
import logging

logger = logging.getLogger(__name__)

# Инициализируем EasyOCR один раз (поддержка русского и английского)
reader = easyocr.Reader(["ru", "en"], gpu=False)


def pdf_to_images(pdf_path):
    """
    Конвертирует PDF в изображения БЕЗ Poppler

    Args:
        pdf_path: путь к PDF файлу

    Returns:
        list: список PIL Image объектов
    """
    images = []

    try:
        # Открываем PDF
        pdf_document = fitz.open(pdf_path)

        # Конвертируем каждую страницу
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]

            # Рендерим в изображение (dpi=300 для качества)
            pix = page.get_pixmap(matrix=fitz.Matrix(300 / 72, 300 / 72))

            # Конвертируем в PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            images.append(img)

        pdf_document.close()
        logger.info(f"PDF конвертирован: {len(images)} страниц")

    except Exception as e:
        logger.error(f"Ошибка конвертации PDF: {str(e)}")

    return images


def extract_text_ocr(image):
    """
    Извлекает текст из изображения БЕЗ Tesseract

    Args:
        image: PIL Image или путь к файлу

    Returns:
        str: извлеченный текст
    """
    try:
        # EasyOCR работает с путями или numpy массивами
        if isinstance(image, str):
            result = reader.readtext(image, detail=0, paragraph=True)
        else:
            # Конвертируем PIL Image в numpy
            import numpy as np

            img_array = np.array(image)
            result = reader.readtext(img_array, detail=0, paragraph=True)

        # Объединяем результаты
        text = "\n".join(result)
        return text

    except Exception as e:
        logger.error(f"Ошибка OCR: {str(e)}")
        return ""


def process_pdf(pdf_path):
    """
    Полная обработка PDF: конвертация + OCR

    Args:
        pdf_path: путь к PDF

    Returns:
        dict: {
            'text': извлеченный текст,
            'page_count': количество страниц,
            'images': список изображений
        }
    """
    # Конвертируем PDF в изображения
    images = pdf_to_images(pdf_path)

    if not images:
        return {"text": "", "page_count": 0, "images": []}

    # Извлекаем текст из каждой страницы
    all_text = []
    for i, image in enumerate(images):
        logger.info(f"OCR страницы {i+1}/{len(images)}...")
        text = extract_text_ocr(image)
        all_text.append(text)

    result = {
        "text": "\n\n".join(all_text),
        "page_count": len(images),
        "images": images,
    }

    return result


def extract_text_from_pdf(pdf_path):
    """
    Пробует извлечь текст напрямую из PDF (без OCR)
    Если не получается - использует OCR
    """
    try:
        # Сначала пробуем извлечь текст напрямую
        pdf_document = fitz.open(pdf_path)
        text = ""

        for page in pdf_document:
            text += page.get_text()

        pdf_document.close()

        # Если текст есть - возвращаем
        if text.strip():
            logger.info("Текст извлечен напрямую из PDF")
            return text

        # Если текста нет (отсканированный PDF) - используем OCR
        logger.info("Текст не найден, использую OCR...")
        result = process_pdf(pdf_path)
        return result["text"]

    except Exception as e:
        logger.error(f"Ошибка обработки PDF: {str(e)}")
        return ""
