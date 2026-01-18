/**
 * Модуль работы с камерой для сканирования документов
 */

// DOM элементы
const video = document.getElementById('camera-video');
const canvas = document.getElementById('camera-canvas');
const preview = document.getElementById('preview-image');
const startBtn = document.getElementById('start-camera-btn');
const captureBtn = document.getElementById('capture-btn');
const switchBtn = document.getElementById('switch-camera-btn');
const retakeBtn = document.getElementById('retake-btn');
const saveBtn = document.getElementById('save-btn');
const titleInput = document.getElementById('document-title');
const folderSelect = document.getElementById('folder-select');

// Контейнеры
const cameraView = document.getElementById('camera-view');
const previewView = document.getElementById('preview-view');
const captureControls = document.getElementById('capture-controls');
const previewControls = document.getElementById('preview-controls');

// Состояние
let stream = null;
let cameraActive = false;
let cameraFacing = 'environment'; // 'user' или 'environment'
let capturedImage = null;

/**
 * Инициализация модуля камеры
 */
function initCamera() {
    console.log('Инициализация камеры...');

    // Обработчики событий
    if (startBtn) {
        startBtn.addEventListener('click', startCamera);
        console.log('Кнопка запуска камеры подключена');
    }
    if (captureBtn) captureBtn.addEventListener('click', capturePhoto);
    if (switchBtn) switchBtn.addEventListener('click', switchCamera);
    if (retakeBtn) retakeBtn.addEventListener('click', retakePhoto);
    if (saveBtn) saveBtn.addEventListener('click', saveDocument);

    // Проверяем доступность камеры
    checkCameraAvailability();
}

/**
 * Проверка доступности камеры
 */
async function checkCameraAvailability() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        showError('Ваш браузер не поддерживает работу с камерой');
        if (startBtn) startBtn.disabled = true;
        return;
    }

    try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        const videoDevices = devices.filter(device => device.kind === 'videoinput');

        if (videoDevices.length === 0) {
            showError('Камера не найдена на устройстве');
            if (startBtn) startBtn.disabled = true;
        } else {
            console.log(`Найдено камер: ${videoDevices.length}`);
            // Показываем кнопку переключения только если камер больше одной
            if (videoDevices.length > 1 && switchBtn) {
                switchBtn.style.display = 'inline-block';
            }
        }
    } catch (error) {
        console.error('Ошибка проверки камеры:', error);
    }
}

/**
 * Запуск камеры с УЛУЧШЕННЫМИ настройками
 */
async function startCamera() {
    console.log('Запуск камеры...');

    try {
        // Показываем индикатор загрузки
        if (startBtn) {
            startBtn.disabled = true;
            startBtn.innerHTML = '<i class="bi bi-hourglass-split"></i> Запуск...';
        }

        // Останавливаем предыдущий поток если есть
        if (stream) {
            stopCamera();
        }

        // Запрашиваем камеру с ВЫСОКИМ разрешением
        const constraints = {
            video: {
                facingMode: cameraFacing,
                width: { ideal: 1920, min: 1280 },
                height: { ideal: 1080, min: 720 },
                aspectRatio: { ideal: 16 / 9 }
            }
        };

        console.log('Запрос доступа к камере с настройками:', constraints);

        stream = await navigator.mediaDevices.getUserMedia(constraints);
        video.srcObject = stream;

        // Ждем загрузки метаданных
        await new Promise((resolve) => {
            video.onloadedmetadata = () => {
                video.play();
                resolve();
            };
        });

        // Применяем дополнительные настройки для лучшего качества
        const videoTrack = stream.getVideoTracks()[0];
        const capabilities = videoTrack.getCapabilities();
        const settings = {};

        // Включаем автофокус если поддерживается
        if (capabilities.focusMode) {
            if (capabilities.focusMode.includes('continuous')) {
                settings.focusMode = 'continuous';
            } else if (capabilities.focusMode.includes('single-shot')) {
                settings.focusMode = 'single-shot';
            }
        }

        // Максимальное разрешение
        if (capabilities.width && capabilities.width.max) {
            settings.width = Math.min(capabilities.width.max, 1920);
        }
        if (capabilities.height && capabilities.height.max) {
            settings.height = Math.min(capabilities.height.max, 1080);
        }

        // Применяем настройки
        try {
            await videoTrack.applyConstraints(settings);
        } catch (e) {
            console.warn('Не удалось применить дополнительные настройки:', e);
        }

        const finalSettings = videoTrack.getSettings();
        console.log('Камера запущена успешно!');
        console.log('Разрешение:', finalSettings.width + 'x' + finalSettings.height);

        cameraActive = true;
        updateUI();

    } catch (error) {
        console.error('Ошибка доступа к камере:', error);

        let errorMessage = 'Не удалось получить доступ к камере. ';
        if (error.name === 'NotAllowedError') {
            errorMessage += 'Разрешите доступ к камере в настройках браузера.';
        } else if (error.name === 'NotFoundError') {
            errorMessage += 'Камера не найдена.';
        } else if (error.name === 'NotReadableError') {
            errorMessage += 'Камера уже используется другим приложением.';
        } else {
            errorMessage += error.message;
        }

        showError(errorMessage);
        if (startBtn) {
            startBtn.disabled = false;
            startBtn.innerHTML = '<i class="bi bi-camera-video"></i> Запустить камеру';
        }
    }
}

/**
 * Остановка камеры
 */
function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }
    if (video) {
        video.srcObject = null;
    }
    cameraActive = false;
    console.log('Камера остановлена');
}

/**
 * Переключение между фронтальной и основной камерой
 */
async function switchCamera() {
    cameraFacing = cameraFacing === 'environment' ? 'user' : 'environment';
    console.log('Переключение камеры на:', cameraFacing);

    if (cameraActive) {
        await startCamera();
    }
}

/**
 * Захват фото с УЛУЧШЕНИЕМ качества
 */
function capturePhoto() {
    if (!cameraActive) {
        showError('Камера не активна');
        return;
    }

    console.log('Захват фото...');

    try {
        // Устанавливаем размеры canvas равными РЕАЛЬНОМУ разрешению видео
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        console.log(`Захват изображения: ${canvas.width}x${canvas.height}`);

        const ctx = canvas.getContext('2d');

        // Улучшаем качество рендеринга
        ctx.imageSmoothingEnabled = true;
        ctx.imageSmoothingQuality = 'high';

        // Рисуем изображение
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        // Применяем улучшения для OCR
        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
        const enhancedData = enhanceImageForOCR(imageData);
        ctx.putImageData(enhancedData, 0, 0);

        // Получаем base64 с МАКСИМАЛЬНЫМ качеством JPEG (0.95 = 95% качества)
        const dataUrl = canvas.toDataURL('image/jpeg', 0.95);

        console.log(`Размер изображения: ${(dataUrl.length / 1024).toFixed(2)} КБ`);

        // Показываем предпросмотр
        preview.src = dataUrl;
        capturedImage = dataUrl;

        // Переключаем UI
        cameraView.style.display = 'none';
        captureControls.style.display = 'none';
        previewView.style.display = 'flex';
        previewControls.style.display = 'flex';

        // Останавливаем камеру для экономии ресурсов
        stopCamera();

        // Фокус на поле названия
        if (titleInput) titleInput.focus();

        console.log('Фото захвачено успешно');

    } catch (error) {
        console.error('Ошибка при захвате фото:', error);
        showError('Не удалось захватить изображение');
    }
}

/**
 * УЛУЧШЕНИЕ изображения для OCR
 * Увеличивает контраст и резкость
 */
function enhanceImageForOCR(imageData) {
    const data = imageData.data;

    // Параметры улучшения
    const contrastFactor = 1.4;
    const brightnessFactor = 1.1;

    for (let i = 0; i < data.length; i += 4) {
        let r = data[i];
        let g = data[i + 1];
        let b = data[i + 2];

        // Применяем контраст
        r = ((r - 128) * contrastFactor) + 128;
        g = ((g - 128) * contrastFactor) + 128;
        b = ((b - 128) * contrastFactor) + 128;

        // Применяем яркость
        r = r * brightnessFactor;
        g = g * brightnessFactor;
        b = b * brightnessFactor;

        // Ограничиваем значения
        data[i] = Math.min(255, Math.max(0, r));
        data[i + 1] = Math.min(255, Math.max(0, g));
        data[i + 2] = Math.min(255, Math.max(0, b));
    }

    return imageData;
}

/**
 * Повторный снимок
 */
function retakePhoto() {
    capturedImage = null;

    // Переключаем UI
    previewView.style.display = 'none';
    previewControls.style.display = 'none';
    cameraView.style.display = 'block';
    captureControls.style.display = 'flex';

    // Запускаем камеру снова
    startCamera();
}

/**
 * Сохранение документа
 */
async function saveDocument() {
    if (!capturedImage) {
        showError('Нет изображения для сохранения');
        return;
    }

    const title = (titleInput ? titleInput.value.trim() : '') || `Скан ${new Date().toLocaleString('ru-RU')}`;
    const folderId = (folderSelect ? folderSelect.value : '') || null;

    console.log('Сохранение документа:', title);

    // Показываем индикатор загрузки
    saveBtn.disabled = true;
    saveBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Обработка...';

    try {
        const response = await fetch('/scanner/capture', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                image: capturedImage,
                title: title,
                folder_id: folderId
            })
        });

        const result = await response.json();

        if (result.success) {
            console.log('Документ сохранен успешно');
            showSuccess('Документ успешно сохранен');
            setTimeout(() => {
                window.location.href = result.redirect_url;
            }, 1000);
        } else {
            console.error('Ошибка сохранения:', result.error);
            showError(result.error || 'Ошибка при сохранении документа');
            saveBtn.disabled = false;
            saveBtn.innerHTML = '<i class="bi bi-check-lg"></i> Сохранить';
        }
    } catch (error) {
        console.error('Ошибка при сохранении:', error);
        showError('Ошибка связи с сервером');
        saveBtn.disabled = false;
        saveBtn.innerHTML = '<i class="bi bi-check-lg"></i> Сохранить';
    }
}

/**
 * Обновление UI в зависимости от состояния камеры
 */
function updateUI() {
    if (cameraActive) {
        startBtn.style.display = 'none';
        cameraView.style.display = 'block';
        captureControls.style.display = 'flex';
    } else {
        startBtn.style.display = 'inline-block';
        startBtn.disabled = false;
        startBtn.innerHTML = '<i class="bi bi-camera-video"></i> Запустить камеру';
        cameraView.style.display = 'none';
        captureControls.style.display = 'none';
    }
}

/**
 * Показать сообщение об ошибке
 */
function showError(message) {
    console.error('Ошибка:', message);

    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3';
    alertDiv.style.zIndex = '9999';
    alertDiv.style.minWidth = '300px';
    alertDiv.innerHTML = `
        <i class="bi bi-exclamation-triangle-fill me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);

    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

/**
 * Показать сообщение об успехе
 */
function showSuccess(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-success alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3';
    alertDiv.style.zIndex = '9999';
    alertDiv.style.minWidth = '300px';
    alertDiv.innerHTML = `
        <i class="bi bi-check-circle-fill me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);

    setTimeout(() => {
        alertDiv.remove();
    }, 3000);
}

/**
 * Очистка при закрытии страницы
 */
window.addEventListener('beforeunload', () => {
    stopCamera();
});

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', initCamera);
