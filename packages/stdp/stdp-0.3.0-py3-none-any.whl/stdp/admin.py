from PyQt6.QtWidgets import QMainWindow, QTableWidget, QTableWidgetItem, QLineEdit, QPushButton, QDialog, QMessageBox
from PyQt6 import uic
from pathlib import Path

try:
    from .database import connect
except ImportError:
    from database import connect


# Заполнение таблицы основных записей
def fill_main_records_table(con, table):
    cur = con.cursor()
    cur.execute("""
        SELECT u.full_name AS 'ФИО', u.passport AS 'Документ', b.check_in AS 'Дата начала',
        b.check_out AS 'Дата конца', c.name AS 'Тип', r.room_no AS 'Код', s.name AS 'Статус'
        FROM booking b JOIN users u ON u.id = b.client_id JOIN rooms r ON r.id = b.room_id
        JOIN room_categories c ON c.id = r.category_id JOIN booking_status s ON s.id = b.status_id
        ORDER BY b.check_in DESC
    """)
    rows = cur.fetchall()
    cur.close()

    table.setRowCount(len(rows))
    for row_idx, row_data in enumerate(rows):
        for col_idx, col_name in enumerate(['ФИО', 'Документ', 'Дата начала', 'Дата конца', 'Тип', 'Код', 'Статус']):
            table.setItem(row_idx, col_idx, QTableWidgetItem(str(row_data.get(col_name, ""))))
    table.resizeColumnsToContents()


# Заполнение таблицы пользователей
def fill_users_table(con, table):
    cur = con.cursor()
    cur.execute("""
        SELECT u.full_name AS 'Имя', u.passport AS 'Документ', 
        b.check_in AS 'Дата начала', b.check_out AS 'Дата конца'
        FROM users u JOIN booking b ON u.id = b.client_id
    """)
    rows = cur.fetchall()
    cur.close()

    table.setRowCount(len(rows))
    for row_idx, row_data in enumerate(rows):
        for col_idx, col_name in enumerate(['Имя', 'Документ', 'Дата начала', 'Дата конца']):
            table.setItem(row_idx, col_idx, QTableWidgetItem(str(row_data.get(col_name, ""))))
    table.resizeColumnsToContents()


# Заполнение таблицы элементов
def fill_items_table(con, table):
    cur = con.cursor()
    cur.execute("""
        SELECT r.room_no AS 'Код', rc.name AS 'Тип', r.price AS 'Цена', r.room_status AS 'Статус'
        FROM rooms r JOIN room_categories rc ON r.category_id = rc.id
    """)
    rows = cur.fetchall()
    cur.close()

    table.setRowCount(len(rows))
    for row_idx, row_data in enumerate(rows):
        for col_idx, col_name in enumerate(['Код', 'Тип', 'Цена', 'Статус']):
            table.setItem(row_idx, col_idx, QTableWidgetItem(str(row_data.get(col_name, ""))))
    table.resizeColumnsToContents()


# Заполнение таблицы финансовых операций
def fill_financial_table(con, table):
    cur = con.cursor()
    cur.execute("""
        SELECT CURDATE() AS 'Дата', u.full_name AS 'Клиент', 
        (r.price * DATEDIFF(b.check_out, b.check_in)) AS 'Сумма', bs.name AS 'Статус'
        FROM users u JOIN booking b ON u.id = b.client_id
        JOIN rooms r ON b.room_id = r.id JOIN booking_status bs ON b.status_id = bs.id
    """)
    rows = cur.fetchall()
    cur.close()

    table.setRowCount(len(rows))
    for row_idx, row_data in enumerate(rows):
        for col_idx, col_name in enumerate(['Дата', 'Клиент', 'Сумма', 'Статус']):
            table.setItem(row_idx, col_idx, QTableWidgetItem(str(row_data.get(col_name, ""))))
    table.resizeColumnsToContents()


# Настройка главного окна администратора
def setup_main_window(main_win):
    ui_path = Path(__file__).parent / "ui" / "MainWindow.ui"
    uic.loadUi(str(ui_path), main_win)

    con = connect()
    # Поиск таблиц в интерфейсе
    main_table = main_win.findChild(QTableWidget, "ViewWidget_booking")
    users_table = main_win.findChild(QTableWidget, "ViewWidget_people")
    items_table = main_win.findChild(QTableWidget, "ViewWidget_number")
    financial_table = main_win.findChild(QTableWidget, "ViewWidget_paying")

    # Загрузка данных в таблицы
    if main_table:
        fill_main_records_table(con, main_table)
    if users_table:
        fill_users_table(con, users_table)
    if items_table:
        fill_items_table(con, items_table)
    if financial_table:
        fill_financial_table(con, financial_table)

    con.close()

    # Поиск по таблице основных записей
    search_edit = main_win.findChild(QLineEdit, "SearchLabel")
    if search_edit and main_table:
        def apply_filter(text):
            text = text.strip().lower()
            for row in range(main_table.rowCount()):
                main_table.setRowHidden(row, bool(text) and not any(
                    main_table.item(row, col) and text in main_table.item(row, col).text().lower()
                    for col in range(main_table.columnCount())))

        search_edit.textChanged.connect(apply_filter)

    # Кнопка добавления новой записи
    add_btn = main_win.findChild(QPushButton, "AddButton_booking")
    if add_btn and main_table:
        def on_add():
            # Открытие диалога для ввода данных
            dialog = QDialog()
            uic.loadUi(str(Path(__file__).parent / "ui" / "AddDialog.ui"), dialog)

            # Поиск полей ввода в диалоге
            fields = [dialog.findChild(QLineEdit, name) for name in
                      ["lineEdit", "lineEdit_2", "lineEdit_3", "lineEdit_4", "lineEdit_5", "lineEdit_6", "lineEdit_7"]]
            save_btn = dialog.findChild(QPushButton, "pushButton")

            # Обработка сохранения данных
            def on_save():
                # Получение значений из полей
                values = [f.text().strip() if f else "" for f in fields]
                if not all(values):
                    QMessageBox.warning(dialog, "Ошибка", "Заполните все поля")
                    return

                # Добавление новой строки в таблицу
                row_count = main_table.rowCount()
                main_table.insertRow(row_count)

                # Заполнение ячеек таблицы данными из диалога
                # Порядок: ФИО, Документ, Дата начала, Дата конца, Тип, Код, Статус
                main_table.setItem(row_count, 0, QTableWidgetItem(values[0]))  # ФИО
                main_table.setItem(row_count, 1, QTableWidgetItem(values[1]))  # Документ
                main_table.setItem(row_count, 2, QTableWidgetItem(values[2]))  # Дата начала
                main_table.setItem(row_count, 3, QTableWidgetItem(values[3]))  # Дата конца
                main_table.setItem(row_count, 4, QTableWidgetItem(values[4]))  # Тип
                main_table.setItem(row_count, 5, QTableWidgetItem(values[5]))  # Код
                main_table.setItem(row_count, 6, QTableWidgetItem(values[6]))  # Статус

                main_table.resizeColumnsToContents()
                QMessageBox.information(dialog, "Успех", "Запись добавлена в таблицу!")
                dialog.accept()

            if save_btn:
                save_btn.clicked.connect(on_save)
            dialog.exec()

        add_btn.clicked.connect(on_add)

    # Кнопка удаления записи
    delete_btn = main_win.findChild(QPushButton, "pushButton")
    if delete_btn and main_table:
        def on_delete():
            # Получение выбранной строки
            selected_row = main_table.currentRow()
            if selected_row < 0:
                QMessageBox.warning(main_win, "Ошибка", "Выберите строку для удаления")
                return

            # Удаление строки из таблицы
            main_table.removeRow(selected_row)
            QMessageBox.information(main_win, "Успех", "Запись удалена из таблицы!")

        delete_btn.clicked.connect(on_delete)
