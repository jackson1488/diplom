# models/folder.py
"""
Модель папки для организации документов.
Папки позволяют пользователям группировать документы по категориям.
"""

from datetime import datetime
from models import db


class Folder(db.Model):
    """
    Модель папки для организации документов пользователя.
    Каждая папка принадлежит одному пользователю.
    """
    
    # Название таблицы в базе данных
    __tablename__ = 'folders'
    
    # === ОСНОВНЫЕ ПОЛЯ ===
    
    # Уникальный идентификатор папки (первичный ключ)
    id = db.Column(db.Integer, primary_key=True)
    
    # Название папки (обязательное)
    name = db.Column(db.String(128), nullable=False)
    
    # Описание папки (необязательное)
    description = db.Column(db.Text, nullable=True)
    
    # Цвет папки для визуального различия (hex код, например #FF5733)
    color = db.Column(db.String(7), default='#3498db')
    
    # === СВЯЗЬ С ПОЛЬЗОВАТЕЛЕМ ===
    
    # ID владельца папки (внешний ключ на таблицу users)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # === ВРЕМЕННЫЕ МЕТКИ ===
    
    # Дата и время создания папки
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Дата и время последнего обновления
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, 
                          onupdate=datetime.utcnow, nullable=False)
    
    # === СВЯЗИ С ДРУГИМИ ТАБЛИЦАМИ ===
    
    # Связь с документами в этой папке (один-ко-многим)
    # backref='folder' создает обратную связь: document.folder
    # lazy='dynamic' означает, что документы загружаются только при обращении
    documents = db.relationship('Document', backref='folder', lazy='dynamic',
                               cascade='all, delete-orphan')
    
    # === МЕТОДЫ ===
    
    def get_document_count(self):
        """
        Возвращает количество документов в папке.
        
        Returns:
            Целое число - количество документов
        """
        return self.documents.count()
    
    def get_total_size(self):
        """
        Возвращает общий размер всех документов в папке (в байтах).
        
        Returns:
            Целое число - размер в байтах
        """
        total = 0
        for doc in self.documents:
            if doc.file_size:
                total += doc.file_size
        return total
    
    def get_total_size_mb(self):
        """
        Возвращает общий размер всех документов в папке в мегабайтах.
        
        Returns:
            Число с плавающей точкой - размер в МБ
        """
        return round(self.get_total_size() / (1024 * 1024), 2)
    
    def to_dict(self):
        """
        Преобразует объект папки в словарь.
        Полезно для API и сериализации.
        
        Returns:
            Словарь с данными папки
        """
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'document_count': self.get_document_count(),
            'total_size_mb': self.get_total_size_mb()
        }
    
    def __repr__(self):
        """
        Строковое представление объекта для отладки.
        """
        return f'<Folder {self.name} (User: {self.user_id})>'
