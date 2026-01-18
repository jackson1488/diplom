"""
Сервис для OCR (оптическое распознавание текста)
Использует EasyOCR вместо Tesseract
"""

import os
import logging
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)

# Глобальный reader
_ocr_reader = None


def get_ocr_reader():
    """Ленивая инициализация EasyOCR"""
    global _ocr_reader
    if _ocr_reader is None:
        try:
            import easyocr

            logger.info("Инициализация EasyOCR...")
            _ocr_reader = easyocr.Reader(["ru", "en"], gpu=False)
            logger.info("✓ EasyOCR готов")
        except Exception as e:
            logger.error(f"Ошибка инициализации EasyOCR: {e}")
            raise
    return _ocr_reader


class OCRService:
    """Сервис для распознавания текста (совместимость со старым кодом)"""

    @staticmethod
    def extract_text(image_path, languages=["ru", "en"]):
        """
        Извлекает текст из изображения

        Args:
            image_path: путь к изображению или PIL Image
            languages: языки (не используется, EasyOCR использует ['ru', 'en'])

        Returns:
            str: распознанный текст
        """
        try:
            reader = get_ocr_reader()

            # Если PIL Image
            if isinstance(image_path, Image.Image):
                img_array = np.array(image_path)
                result = reader.readtext(img_array, detail=0, paragraph=True)
            else:
                # Если путь
                result = reader.readtext(image_path, detail=0, paragraph=True)

            text = "\n".join(result)
            logger.info(f"OCR: извлечено {len(text)} символов")
            return text

        except Exception as e:
            logger.error(f"Ошибка OCR: {e}")
            return ""

    @staticmethod
    def process_image(image_path, preprocess=True):
        """
        Обрабатывает изображение с предобработкой

        Args:
            image_path: путь к изображению
            preprocess: применять ли улучшения

        Returns:
            dict: результаты OCR
        """
        try:
            reader = get_ocr_reader()

            if preprocess:
                image = Image.open(image_path)
                image = OCRService.enhance_image(image)
                img_array = np.array(image)
            else:
                img_array = image_path

            # OCR с уверенностью
            result = reader.readtext(img_array, detail=1)

            texts = []
            confidences = []

            for bbox, text, conf in result:
                texts.append(text)
                confidences.append(conf)

            avg_confidence = (
                sum(confidences) / len(confidences) * 100 if confidences else 0
            )

            return {
                "text": "\n".join(texts),
                "confidence": round(avg_confidence, 2),
                "language": "mixed",
            }

        except Exception as e:
            logger.error(f"Ошибка обработки: {e}")
            return {"text": "", "confidence": 0, "language": "unknown"}

    @staticmethod
    def enhance_image(image):
        """Улучшает изображение для OCR"""
        try:
            from PIL import ImageEnhance

            image = image.convert("L")

            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)

            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(1.5)

            return image

        except Exception as e:
            logger.warning(f"Не удалось улучшить: {e}")
            return image

    @staticmethod
    def batch_ocr(image_paths):
        """Массовое распознавание"""
        results = []
        for i, path in enumerate(image_paths):
            logger.info(f"OCR {i+1}/{len(image_paths)}")
            result = OCRService.process_image(path)
            results.append(result)
        return results


# Функции для обратной совместимости
def extract_text_from_image(image_path, languages=["ru", "en"]):
    """Обертка для OCRService.extract_text"""
    return OCRService.extract_text(image_path, languages)


def process_image(image_path, preprocess=True):
    """Обертка для OCRService.process_image"""
    return OCRService.process_image(image_path, preprocess)


def enhance_image(image):
    """Обертка для OCRService.enhance_image"""
    return OCRService.enhance_image(image)


def batch_ocr(image_paths):
    """Обертка для OCRService.batch_ocr"""
    return OCRService.batch_ocr(image_paths)
