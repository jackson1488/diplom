// static/js/editor.js
/**
 * Дополнительные функции редактора
 * Горячие клавиши, автосохранение, статистика
 */

(function () {
    'use strict';

    /**
     * Подсчет слов в тексте
     */
    window.countWords = function (text) {
        return text.trim().split(/\s+/).filter(word => word.length > 0).length;
    };

    /**
     * Подсчет строк в тексте
     */
    window.countLines = function (text) {
        return text.split('\n').length;
    };

    /**
     * Экспорт текста в файл
     */
    window.exportToFile = function (content, filename, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    /**
     * Поиск и замена текста
     */
    window.findAndReplace = function (quillInstance, searchText, replaceText) {
        const text = quillInstance.getText();
        const newText = text.replaceAll(searchText, replaceText);
        quillInstance.setText(newText);
    };

    /**
     * Вставка текущей даты
     */
    window.insertDate = function (quillInstance) {
        const range = quillInstance.getSelection(true);
        const date = new Date().toLocaleDateString('ru-RU');
        quillInstance.insertText(range.index, date);
    };

    /**
     * Вставка времени
     */
    window.insertTime = function (quillInstance) {
        const range = quillInstance.getSelection(true);
        const time = new Date().toLocaleTimeString('ru-RU');
        quillInstance.insertText(range.index, time);
    };

    /**
     * Полноэкранный режим редактора
     */
    window.toggleFullscreen = function () {
        const editorContainer = document.querySelector('.editor-container');
        if (!document.fullscreenElement) {
            editorContainer.requestFullscreen();
        } else {
            document.exitFullscreen();
        }
    };

    /**
     * Печать документа
     */
    window.printDocument = function () {
        window.print();
    };

})();
