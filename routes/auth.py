# routes/auth.py
"""
Маршруты для аутентификации пользователей.
Включает регистрацию, вход, выход.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from werkzeug.security import check_password_hash
import logging

from models import db
from models.user import User
from utils.validators import validate_email, validate_password, validate_username

# Настраиваем логирование
logger = logging.getLogger(__name__)

# Создаем blueprint для маршрутов аутентификации
auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Страница входа в систему.
    GET: отображает форму входа
    POST: обрабатывает данные формы и выполняет вход
    """
    # Если пользователь уже авторизован, перенаправляем в библиотеку
    if current_user.is_authenticated:
        return redirect(url_for("documents.library"))

    if request.method == "POST":
        # Получаем данные из формы
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        remember = request.form.get("remember", False)

        logger.info(f"Попытка входа: username={username}")

        # Валидация входных данных
        if not username:
            flash("Введите имя пользователя", "danger")
            return render_template("auth/login.html")

        if not password:
            flash("Введите пароль", "danger")
            return render_template("auth/login.html")

        # Ищем пользователя в базе данных
        user = User.query.filter_by(username=username).first()

        # Проверяем существование пользователя и правильность пароля
        if not user or not user.check_password(password):
            logger.warning(f"Неудачная попытка входа: username={username}")
            flash("Неверное имя пользователя или пароль", "danger")
            return render_template("auth/login.html")

        # Проверяем, активен ли пользователь
        if not user.is_active:
            logger.warning(f"Попытка входа заблокированным пользователем: {user.id}")
            flash("Ваш аккаунт заблокирован. Обратитесь к администратору.", "danger")
            return render_template("auth/login.html")

        # Выполняем вход
        login_user(user, remember=remember)

        # Обновляем время последнего входа
        user.update_last_login()

        logger.info(f"Успешный вход: user_id={user.id}, username={username}")

        # Определяем, куда перенаправить после входа
        next_page = request.args.get("next")
        if next_page and next_page.startswith("/"):
            return redirect(next_page)
        else:
            # По умолчанию перенаправляем в библиотеку
            return redirect(url_for("documents.library"))

    # GET запрос - отображаем форму входа
    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    Страница регистрации нового пользователя.
    GET: отображает форму регистрации
    POST: обрабатывает данные формы и создает нового пользователя
    """
    # Если пользователь уже авторизован, перенаправляем в библиотеку
    if current_user.is_authenticated:
        return redirect(url_for("documents.library"))

    if request.method == "POST":
        # Получаем данные из формы
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")
        full_name = request.form.get("full_name", "").strip()

        logger.info(f"Попытка регистрации: username={username}, email={email}")

        # Валидация имени пользователя
        is_valid, error_msg = validate_username(username)
        if not is_valid:
            flash(error_msg, "danger")
            return render_template("auth/register.html")

        # Валидация email
        is_valid, error_msg = validate_email(email)
        if not is_valid:
            flash(error_msg, "danger")
            return render_template("auth/register.html")

        # Валидация пароля
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            flash(error_msg, "danger")
            return render_template("auth/register.html")

        # Проверка совпадения паролей
        if password != password_confirm:
            flash("Пароли не совпадают", "danger")
            return render_template("auth/register.html")

        # Проверка уникальности имени пользователя
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Пользователь с таким именем уже существует", "danger")
            return render_template("auth/register.html")

        # Проверка уникальности email
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash("Пользователь с таким email уже существует", "danger")
            return render_template("auth/register.html")

        try:
            # Создаем нового пользователя
            new_user = User(
                username=username,
                email=email,
                full_name=full_name if full_name else username,
                is_admin=False,
                is_active=True,
            )
            new_user.set_password(password)

            # Сохраняем в базу данных
            db.session.add(new_user)
            db.session.commit()

            logger.info(
                f"Новый пользователь зарегистрирован: user_id={new_user.id}, username={username}"
            )

            # Автоматически входим под новым пользователем
            login_user(new_user)

            flash("Регистрация успешна! Добро пожаловать!", "success")
            return redirect(url_for("documents.library"))

        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка при регистрации: {str(e)}", exc_info=True)
            flash("Произошла ошибка при регистрации. Попробуйте еще раз.", "danger")
            return render_template("auth/register.html")

    # GET запрос - отображаем форму регистрации
    return render_template("auth/register.html")


@auth_bp.route("/logout")
def logout():
    """
    Выход из системы.
    Завершает сессию пользователя и перенаправляет на страницу входа.
    """
    if current_user.is_authenticated:
        logger.info(f"Пользователь вышел: user_id={current_user.id}")

    logout_user()
    flash("Вы успешно вышли из системы", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/profile")
def profile():
    """
    Страница профиля пользователя.
    Отображает информацию о текущем пользователе.
    """
    from utils.decorators import login_required

    @login_required
    def _profile():
        return render_template("auth/profile.html", user=current_user)

    return _profile()
