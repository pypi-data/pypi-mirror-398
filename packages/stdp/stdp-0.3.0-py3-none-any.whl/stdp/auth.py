from pathlib import Path
from PyQt6.QtWidgets import QMainWindow, QMessageBox, QPushButton, QTextEdit, QApplication
from PyQt6 import uic

try:
    from .database import connect
except ImportError:
    from database import connect


# Проверка учетных данных пользователя
def check_login(login, password):
    con = connect()
    try:
        with con.cursor() as cur:
            cur.execute("SELECT role FROM users WHERE login = %s AND password = %s", (login, password))
            return (cur.fetchone() or {}).get('role')
    finally:
        con.close()


# Окно аутентификации
def show_auth_window():
    auth_win = QMainWindow()
    uic.loadUi(str(Path(__file__).parent / "ui" / "AuthWindow.ui"), auth_win)

    login_field = auth_win.findChild(QTextEdit, "LoginText")
    password_field = auth_win.findChild(QTextEdit, "PasswordText")
    login_btn = auth_win.findChild(QPushButton, "pushButton")

    role = user_login = None

    # Обработка нажатия кнопки входа
    def on_login():
        nonlocal role, user_login
        login = login_field.toPlainText().strip()
        password = password_field.toPlainText().strip()
        if not login or not password:
            QMessageBox.warning(auth_win, "Ошибка", "Введите логин и пароль")
            return
        role = check_login(login, password)
        if not role:
            QMessageBox.critical(auth_win, "Ошибка", "Неверный логин или пароль")
            return
        user_login = login
        auth_win.close()

    if login_btn:
        login_btn.clicked.connect(on_login)

    auth_win.show()
    app = QApplication.instance()
    while auth_win.isVisible():
        app.processEvents()
    return role, user_login



