/**
 * Скрипт для страницы библиотеки документов
 */

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function () {
    console.log('Библиотека документов загружена');

    // Инициализация поиска
    initSearch();

    // Инициализация фильтров
    initFilters();
});

/**
 * Инициализация поиска
 */
function initSearch() {
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        // Поиск при вводе с задержкой
        let searchTimeout;
        searchInput.addEventListener('input', function (e) {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                performSearch(e.target.value);
            }, 500);
        });
    }
}

/**
 * Выполнить поиск
 */
function performSearch(query) {
    if (query.length < 2 && query.length > 0) {
        return; // Минимум 2 символа
    }

    const url = new URL(window.location.href);
    if (query) {
        url.searchParams.set('q', query);
    } else {
        url.searchParams.delete('q');
    }

    window.location.href = url.toString();
}

/**
 * Инициализация фильтров
 */
function initFilters() {
    const sortSelect = document.getElementById('sort-select');
    if (sortSelect) {
        sortSelect.addEventListener('change', function (e) {
            const url = new URL(window.location.href);
            url.searchParams.set('sort', e.target.value);
            window.location.href = url.toString();
        });
    }

    const viewButtons = document.querySelectorAll('[data-view]');
    viewButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            const view = this.dataset.view;
            const url = new URL(window.location.href);
            url.searchParams.set('view', view);
            window.location.href = url.toString();
        });
    });
}

/**
 * Удаление документа
 */
function deleteDocument(documentId) {
    if (!confirm('Вы уверены, что хотите удалить этот документ?')) {
        return;
    }

    fetch(`/documents/delete/${documentId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({})
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Документ успешно удален', 'success');
                setTimeout(() => location.reload(), 1000);
            } else {
                showNotification(data.error || 'Ошибка при удалении', 'error');
            }
        })
        .catch(error => {
            console.error('Ошибка:', error);
            showNotification('Ошибка при удалении документа', 'error');
        });
}

/**
 * Переключение избранного
 */
function toggleFavorite(documentId) {
    fetch(`/documents/toggle-favorite/${documentId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({})
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification(
                    data.is_favorite ? 'Добавлено в избранное' : 'Удалено из избранного',
                    'success'
                );

                // Обновляем иконку
                const btns = document.querySelectorAll(`[onclick*="toggleFavorite(${documentId})"]`);
                btns.forEach(btn => {
                    const icon = btn.querySelector('i');
                    if (icon) {
                        if (data.is_favorite) {
                            icon.classList.remove('bi-star');
                            icon.classList.add('bi-star-fill');
                            btn.classList.remove('btn-outline-warning');
                            btn.classList.add('btn-warning');
                        } else {
                            icon.classList.remove('bi-star-fill');
                            icon.classList.add('bi-star');
                            btn.classList.remove('btn-warning');
                            btn.classList.add('btn-outline-warning');
                        }
                    }
                });
            } else {
                showNotification(data.error || 'Ошибка', 'error');
            }
        })
        .catch(error => {
            console.error('Ошибка:', error);
            showNotification('Ошибка при изменении избранного', 'error');
        });
}

/**
 * Архивирование документа
 */
function archiveDocument(documentId) {
    if (!confirm('Переместить документ в архив?')) {
        return;
    }

    fetch(`/documents/archive/${documentId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({})
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Документ перемещен в архив', 'success');
                setTimeout(() => location.reload(), 1000);
            } else {
                showNotification(data.error || 'Ошибка', 'error');
            }
        })
        .catch(error => {
            console.error('Ошибка:', error);
            showNotification('Ошибка при архивировании', 'error');
        });
}

/**
 * Восстановление из архива
 */
function restoreDocument(documentId) {
    fetch(`/documents/restore/${documentId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({})
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Документ восстановлен', 'success');
                setTimeout(() => location.reload(), 1000);
            } else {
                showNotification(data.error || 'Ошибка', 'error');
            }
        })
        .catch(error => {
            console.error('Ошибка:', error);
            showNotification('Ошибка при восстановлении', 'error');
        });
}

/**
 * Перемещение в папку
 */
function moveToFolder(documentId, folderId) {
    fetch(`/documents/move/${documentId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ folder_id: folderId })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showNotification('Документ перемещен', 'success');
                setTimeout(() => location.reload(), 500);
            } else {
                showNotification(data.error || 'Ошибка', 'error');
            }
        })
        .catch(error => {
            console.error('Ошибка:', error);
            showNotification('Ошибка при перемещении', 'error');
        });
}

/**
 * Фильтр по папке
 */
function filterByFolder(folderId) {
    const url = new URL(window.location.href);
    if (folderId) {
        url.searchParams.set('folder_id', folderId);
    } else {
        url.searchParams.delete('folder_id');
    }
    window.location.href = url.toString();
}

/**
 * Показать уведомление
 */
function showNotification(message, type = 'info') {
    const alertClass = type === 'success' ? 'alert-success' :
        type === 'error' ? 'alert-danger' : 'alert-info';

    const icon = type === 'success' ? 'bi-check-circle-fill' :
        type === 'error' ? 'bi-exclamation-triangle-fill' : 'bi-info-circle-fill';

    const alertDiv = document.createElement('div');
    alertDiv.className = `alert ${alertClass} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
    alertDiv.style.zIndex = '9999';
    alertDiv.style.minWidth = '300px';
    alertDiv.innerHTML = `
        <i class="bi ${icon} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    document.body.appendChild(alertDiv);

    setTimeout(() => {
        alertDiv.remove();
    }, 3000);
}

/**
 * Предпросмотр изображения перед загрузкой
 */
function previewImage(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function (e) {
            const preview = document.getElementById('image-preview');
            if (preview) {
                preview.src = e.target.result;
                preview.style.display = 'block';
            }
        };
        reader.readAsDataURL(input.files[0]);
    }
}
