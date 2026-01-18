# services/image_processor.py
"""
Сервис для обработки изображений.
Включает создание миниатюр, улучшение качества для OCR, определение границ документа.
"""

from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
import os
import logging
from typing import Tuple, Optional

# Настраиваем логирование
logger = logging.getLogger(__name__)


class ImageProcessor:
    """
    Сервис для обработки и улучшения изображений.
    """

    def __init__(
        self, thumbnail_size: Tuple[int, int] = (300, 400), jpeg_quality: int = 85
    ):
        """
        Инициализация процессора изображений.

        Args:
            thumbnail_size: размер миниатюры (ширина, высота)
            jpeg_quality: качество JPEG сжатия (1-100)
        """
        self.thumbnail_size = thumbnail_size
        self.jpeg_quality = jpeg_quality

        logger.info(
            f"ImageProcessor инициализирован: размер миниатюр={thumbnail_size}, качество={jpeg_quality}"
        )

    def create_thumbnail(self, image_path: str, output_path: str) -> bool:
        """
        Создает миниатюру изображения для предпросмотра.

        Args:
            image_path: путь к исходному изображению
            output_path: путь для сохранения миниатюры

        Returns:
            True если миниатюра создана успешно, False при ошибке
        """
        try:
            logger.info(f"Создание миниатюры: {image_path} -> {output_path}")

            # Открываем изображение
            image = Image.open(image_path)

            # Конвертируем в RGB (если изображение в другом режиме)
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Создаем миниатюру с сохранением пропорций
            image.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)

            # Создаем директорию, если не существует
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Сохраняем миниатюру
            image.save(output_path, "JPEG", quality=self.jpeg_quality, optimize=True)

            logger.info(f"Миниатюра успешно создана: {output_path}")
            return True

        except Exception as e:
            logger.error(f"Ошибка при создании миниатюры: {str(e)}", exc_info=True)
            return False

    def enhance_for_ocr(
        self, image_path: str, output_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Улучшает изображение для повышения качества OCR распознавания.
        Применяет следующие операции:
        - Увеличение контраста
        - Увеличение резкости
        - Бинаризация (преобразование в черно-белое)
        - Удаление шумов

        Args:
            image_path: путь к исходному изображению
            output_path: путь для сохранения улучшенного изображения (опционально)

        Returns:
            Путь к улучшенному изображению или None при ошибке
        """
        try:
            logger.info(f"Улучшение изображения для OCR: {image_path}")

            # Открываем изображение
            image = Image.open(image_path)

            # Конвертируем в RGB
            if image.mode != "RGB":
                image = image.convert("RGB")

            # Увеличиваем контраст
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)

            # Увеличиваем резкость
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)

            # Конвертируем в градации серого
            image = image.convert("L")

            # Применяем адаптивную бинаризацию с помощью OpenCV
            img_array = np.array(image)
            binary = cv2.adaptiveThreshold(
                img_array, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )

            # Удаляем шумы
            kernel = np.ones((1, 1), np.uint8)
            binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

            # Конвертируем обратно в PIL Image
            enhanced_image = Image.fromarray(binary)

            # Определяем путь сохранения
            if not output_path:
                base, ext = os.path.splitext(image_path)
                output_path = f"{base}_enhanced{ext}"

            # Создаем директорию, если не существует
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Сохраняем улучшенное изображение
            enhanced_image.save(output_path)

            logger.info(f"Изображение улучшено и сохранено: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Ошибка при улучшении изображения: {str(e)}", exc_info=True)
            return None

    def detect_document_edges(self, image_path: str) -> Optional[np.ndarray]:
        """
        Определяет границы документа на изображении.
        Используется для автоматической обрезки и коррекции перспективы.

        Args:
            image_path: путь к изображению

        Returns:
            Массив numpy с координатами углов документа или None при ошибке
        """
        try:
            logger.info(f"Определение границ документа: {image_path}")

            # Читаем изображение с помощью OpenCV
            image = cv2.imread(image_path)

            # Конвертируем в градации серого
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Применяем размытие для уменьшения шумов
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)

            # Определяем края с помощью алгоритма Canny
            edges = cv2.Canny(blurred, 50, 150)

            # Находим контуры
            contours, _ = cv2.findContours(
                edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            # Сортируем контуры по площади (от большего к меньшему)
            contours = sorted(contours, key=cv2.contourArea, reverse=True)

            # Ищем контур документа (обычно это самый большой прямоугольник)
            for contour in contours[:5]:  # Проверяем 5 самых больших контуров
                # Упрощаем контур
                perimeter = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)

                # Если контур имеет 4 угла, это вероятно документ
                if len(approx) == 4:
                    logger.info("Границы документа определены")
                    return approx

            logger.warning("Не удалось определить границы документа")
            return None

        except Exception as e:
            logger.error(f"Ошибка при определении границ: {str(e)}", exc_info=True)
            return None

    def crop_and_perspective_transform(
        self, image_path: str, corners: np.ndarray, output_path: Optional[str] = None
    ) -> Optional[str]:
        """
        Обрезает изображение и корректирует перспективу документа.

        Args:
            image_path: путь к исходному изображению
            corners: координаты углов документа
            output_path: путь для сохранения (опционально)

        Returns:
            Путь к обработанному изображению или None при ошибке
        """
        try:
            logger.info(f"Коррекция перспективы документа: {image_path}")

            # Читаем изображение
            image = cv2.imread(image_path)

            # Переупорядочиваем углы (верхний левый, верхний правый, нижний правый, нижний левый)
            corners = self._order_points(corners.reshape(4, 2))

            # Вычисляем размеры выходного изображения
            (tl, tr, br, bl) = corners

            widthA = np.linalg.norm(br - bl)
            widthB = np.linalg.norm(tr - tl)
            maxWidth = max(int(widthA), int(widthB))

            heightA = np.linalg.norm(tr - br)
            heightB = np.linalg.norm(tl - bl)
            maxHeight = max(int(heightA), int(heightB))

            # Определяем точки назначения для трансформации
            dst = np.array(
                [
                    [0, 0],
                    [maxWidth - 1, 0],
                    [maxWidth - 1, maxHeight - 1],
                    [0, maxHeight - 1],
                ],
                dtype="float32",
            )

            # Вычисляем матрицу перспективного преобразования
            matrix = cv2.getPerspectiveTransform(corners, dst)

            # Применяем трансформацию
            warped = cv2.warpPerspective(image, matrix, (maxWidth, maxHeight))

            # Определяем путь сохранения
            if not output_path:
                base, ext = os.path.splitext(image_path)
                output_path = f"{base}_cropped{ext}"

            # Создаем директорию, если не существует
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Сохраняем результат
            cv2.imwrite(output_path, warped)

            logger.info(f"Перспектива скорректирована: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Ошибка при коррекции перспективы: {str(e)}", exc_info=True)
            return None

    @staticmethod
    def _order_points(pts: np.ndarray) -> np.ndarray:
        """
        Упорядочивает точки углов в стандартном порядке:
        верхний левый, верхний правый, нижний правый, нижний левый.

        Args:
            pts: массив точек

        Returns:
            Упорядоченный массив точек
        """
        # Инициализируем массив упорядоченных координат
        rect = np.zeros((4, 2), dtype="float32")

        # Верхний левый угол имеет наименьшую сумму, нижний правый - наибольшую
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]

        # Верхний правый угол имеет наименьшую разницу, нижний левый - наибольшую
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]

        return rect

    def resize_image(
        self,
        image_path: str,
        max_size: Tuple[int, int],
        output_path: Optional[str] = None,
    ) -> Optional[str]:
        """
        Изменяет размер изображения с сохранением пропорций.

        Args:
            image_path: путь к исходному изображению
            max_size: максимальные размеры (ширина, высота)
            output_path: путь для сохранения (опционально)

        Returns:
            Путь к измененному изображению или None при ошибке
        """
        try:
            logger.info(f"Изменение размера изображения: {image_path}")

            # Открываем изображение
            image = Image.open(image_path)

            # Вычисляем новые размеры с сохранением пропорций
            image.thumbnail(max_size, Image.Resampling.LANCZOS)

            # Определяем путь сохранения
            if not output_path:
                base, ext = os.path.splitext(image_path)
                output_path = f"{base}_resized{ext}"

            # Создаем директорию, если не существует
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Сохраняем результат
            image.save(output_path, quality=self.jpeg_quality, optimize=True)

            logger.info(f"Размер изменен: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Ошибка при изменении размера: {str(e)}", exc_info=True)
            return None
