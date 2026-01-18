# models/user.py
"""
Модель пользователя.
Содержит информацию о пользователе, его правах и методы аутентификации.
"""

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from models import db


class User(UserMixin, db.Model):
    """
    Модель пользователя системы.

    UserMixin предоставляет стандартные методы для Flask-Login:
    - is_authenticated: всегда True для аутентифицированных пользователей
    - is_active: можно использовать для блокировки пользователей
    - is_anonymous: всегда False для реальных пользователей
    - get_id(): возвращает уникальный идентификатор пользователя
    """

    # Название таблицы в базе данных
    __tablename__ = "users"

    # === ОСНОВНЫЕ ПОЛЯ ===

    # Уникальный идентификатор пользователя (первичный ключ)
    id = db.Column(db.Integer, primary_key=True)

    # Имя пользователя для входа (уникальное, обязательное)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)

    # Email пользователя (уникальный, обязательный)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)

    # Хеш пароля (никогда не храним пароли в открытом виде!)
    password_hash = db.Column(db.String(256), nullable=False)

    # === ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ ===

    # Полное имя пользователя (необязательное)
    full_name = db.Column(db.String(128), nullable=True)

    # Флаг администратора (True = администратор с расширенными правами)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    # Флаг активности (False = пользователь заблокирован)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # === ВРЕМЕННЫЕ МЕТКИ ===

    # Дата и время регистрации
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Дата и время последнего входа
    last_login = db.Column(db.DateTime, nullable=True)

    # === СВЯЗИ С ДРУГИМИ ТАБЛИЦАМИ ===

    # Связь с документами пользователя (один-ко-многим)
    # backref='owner' создает обратную связь: document.owner
    # lazy='dynamic' означает, что документы загружаются только при обращении
    # cascade='all, delete-orphan' означает, что при удалении пользователя удаляются его документы
    documents = db.relationship(
        "Document", backref="owner", lazy="dynamic", cascade="all, delete-orphan"
    )

    # Связь с папками пользователя (один-ко-многим)
    folders = db.relationship(
        "Folder", backref="owner", lazy="dynamic", cascade="all, delete-orphan"
    )

    # === МЕТОДЫ ===

    def set_password(self, password):
        """
        Устанавливает пароль пользователя.
        Пароль хешируется с использованием pbkdf2:sha256 перед сохранением.

        Args:
            password: пароль в открытом виде
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Проверяет, соответствует ли введенный пароль сохраненному хешу.

        Args:
            password: пароль в открытом виде для проверки

        Returns:
            True если пароль правильный, False в противном случае
        """
        return check_password_hash(self.password_hash, password)

    def update_last_login(self):
        """
        Обновляет время последнего входа пользователя.
        Вызывается при успешной аутентификации.
        """
        self.last_login = datetime.utcnow()
        db.session.commit()

    def get_document_count(self):
        """
        Возвращает количество документов пользователя.

        Returns:
            Целое число - количество документов
        """
        return self.documents.count()

    def get_folder_count(self):
        """
        Возвращает количество папок пользователя.

        Returns:
            Целое число - количество папок
        """
        return self.folders.count()

    def to_dict(self):
        """
        Преобразует объект пользователя в словарь.
        Полезно для API и сериализации.

        Returns:
            Словарь с данными пользователя (без пароля!)
        """
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "is_admin": self.is_admin,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "document_count": self.get_document_count(),
            "folder_count": self.get_folder_count(),
        }

    def __repr__(self):
        """
        Строковое представление объекта для отладки.
        """
        return f"<User {self.username}>"

    # === МЕТОДЫ КЛАССОВ (СТАТИЧЕСКИЕ) ===

    @staticmethod
    def create_admin(username="admin", email="admin@localhost", password="admin123"):
        """
        Создает администратора по умолчанию.
        Используется при первом запуске приложения.

        Args:
            username: имя пользователя администратора
            email: email администратора
            password: пароль администратора

        Returns:
            Объект User или None если администратор уже существует
        """
        # Проверяем, существует ли уже администратор
        existing_admin = User.query.filter_by(username=username).first()
        if existing_admin:
            return None

        # Создаем нового администратора
        admin = User(
            username=username,
            email=email,
            full_name="Администратор системы",
            is_admin=True,
            is_active=True,
        )
        admin.set_password(password)

        db.session.add(admin)
        db.session.commit()

        return admin
