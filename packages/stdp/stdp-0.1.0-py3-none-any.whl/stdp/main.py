import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from .auth import show_auth_window
from .admin import setup_main_window
from .client import setup_client_window


def main():
    app = QApplication(sys.argv)
    
    # Показываем окно авторизации
    role, login = show_auth_window()
    
    # Если роль не получена (пользователь закрыл окно) - закрываем приложение
    if not role:
        sys.exit(0)
    
    # Создаём главное окно
    main_win = QMainWindow()
    
    # В зависимости от роли настраиваем нужное окно
    if role == "client":
        setup_client_window(main_win, login)
    else:  # admin или manager
        setup_main_window(main_win)
    
    main_win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
