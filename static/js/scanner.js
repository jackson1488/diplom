// static/js/scanner.js
/**
 * Основные функции сканера
 * Обработка загрузки, валидация, UI взаимодействия
 */

(function () {
    'use strict';

    /**
     * Форматирование размера файла
     */
    window.formatFileSize = function (bytes) {
        if (bytes === 0) return '0 Байт';
        const k = 1024;
        const sizes = ['Байт', 'КБ', 'МБ', 'ГБ'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
    };

    /**
     * Проверка поддержки камеры
     */
    window.checkCameraSupport = function () {
        return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
    };

    /**
     * Валидация типа файла
     */
    window.validateFileType = function (file) {
        const allowedExtensions = ['pdf', 'jpg', 'jpeg', 'png', 'txt', 'docx'];
        const extension = file.name.split('.').pop().toLowerCase();
        return allowedExtensions.includes(extension);
    };

    /**
     * Валидация размера файла (макс 50 МБ)
     */
    window.validateFileSize = function (file) {
        const maxSize = 50 * 1024 * 1024; // 50 МБ
        return file.size <= maxSize;
    };

    /**
     * Показать уведомление
     */
    window.showNotification = function (message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
        alertDiv.style.zIndex = '9999';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(alertDiv);

        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    };

    /**
     * Проверка доступа к камере при загрузке страницы камеры
     */
    if (window.location.pathname.includes('/scanner/camera')) {
        if (!checkCameraSupport()) {
            showNotification('Ваш браузер не поддерживает доступ к камере', 'danger');
        }
    }

})();
