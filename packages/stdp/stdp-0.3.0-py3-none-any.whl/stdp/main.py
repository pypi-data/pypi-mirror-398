import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
try:
    from .auth import show_auth_window
    from .admin import setup_main_window
    from .client import setup_client_window
except ImportError:
    from auth import show_auth_window
    from admin import setup_main_window
    from client import setup_client_window

# Главная функция приложения
def main():
    app = QApplication(sys.argv)
    # Аутентификация пользователя
    role, login = show_auth_window()
    if not role:
        sys.exit(0)
    
    # Создание главного окна в зависимости от роли
    main_win = QMainWindow()
    if role == "client":
        setup_client_window(main_win, login)
    else:
        setup_main_window(main_win)
    main_win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
