from PyQt6.QtWidgets import QMainWindow, QTableWidget, QTableWidgetItem, QLineEdit, QPushButton, QDialog, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6 import uic
from pathlib import Path
from .database import connect


def fill_table(con, table, query, columns, save_ids=None, editable_all=True, editable_cols=None):
    with con.cursor() as cur:
        cur.execute(query)
        rows = cur.fetchall()
    
    table.setRowCount(len(rows))
    for row_idx, row_data in enumerate(rows):
        for col_idx, col_name in enumerate(columns):
            value = str(row_data[col_name]) if row_data.get(col_name) is not None else ""
            item = QTableWidgetItem(value)
            
            if save_ids and col_idx == 0:
                for role, field in save_ids.items():
                    item.setData(role, row_data.get(field))
            
            if editable_all and (editable_cols is None or col_idx in editable_cols):
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            table.setItem(row_idx, col_idx, item)
    table.resizeColumnsToContents()


def fill_booking_table(con, table):
    fill_table(con, table,
        "SELECT b.id AS 'booking_id', u.id AS 'user_id', r.id AS 'room_id', s.id AS 'status_id', "
        "u.full_name AS 'ФИО гостя', u.passport AS 'Паспорт', b.check_in AS 'Заезд', "
        "b.check_out AS 'Выезд', c.name AS 'Тип номера', r.room_no AS 'Номер', s.name AS 'Статус' "
        "FROM booking b JOIN users u ON u.id = b.client_id JOIN rooms r ON r.id = b.room_id "
        "JOIN room_categories c ON c.id = r.category_id JOIN booking_status s ON s.id = b.status_id "
        "ORDER BY b.check_in DESC",
        ['ФИО гостя', 'Паспорт', 'Заезд', 'Выезд', 'Тип номера', 'Номер', 'Статус'],
        {1000: 'booking_id', 1001: 'status_id', 1002: 'user_id', 1003: 'room_id'})


def fill_guests_table(con, table):
    fill_table(con, table,
        "SELECT u.id AS 'user_id', b.id AS 'booking_id', u.full_name AS 'ФИО гостя', "
        "u.passport AS 'Паспорт', b.check_in AS 'Дата въезда', b.check_out AS 'Дата выезда' "
        "FROM users u JOIN booking b ON u.id = b.client_id",
        ['ФИО гостя', 'Паспорт', 'Дата въезда', 'Дата выезда'],
        {1000: 'user_id', 1001: 'booking_id'})


def fill_number_table(con, table):
    fill_table(con, table,
        "SELECT r.id AS 'room_id', r.category_id AS 'category_id', r.room_no AS 'Номер', "
        "rc.name AS 'Тип', r.price AS 'Цена', r.room_status AS 'Статус' "
        "FROM rooms r JOIN room_categories rc ON r.category_id = rc.id",
        ['Номер', 'Тип', 'Цена', 'Статус'],
        {1000: 'room_id', 1001: 'category_id'})


def fill_paying_table(con, table):
    fill_table(con, table,
        "SELECT b.id AS 'booking_id', b.status_id AS 'status_id', CURDATE() AS 'Дата', "
        "u.full_name AS 'Гость', (r.price * DATEDIFF(b.check_out, b.check_in)) AS 'Сумма', bs.name AS 'Статус' "
        "FROM users u JOIN booking b ON u.id = b.client_id "
        "JOIN rooms r ON b.room_id = r.id JOIN booking_status bs ON b.status_id = bs.id",
        ['Дата', 'Гость', 'Сумма', 'Статус'],
        {1000: 'booking_id', 1001: 'status_id'},
        editable_all=False, editable_cols=[1, 3])


def setup_main_window(main_win):
    ui_path = Path(__file__).parent / "ui" / "MainWindow.ui"
    uic.loadUi(str(ui_path), main_win)
    
    con = connect()
    booking_table = main_win.findChild(QTableWidget, "ViewWidget_booking")
    guests_table = main_win.findChild(QTableWidget, "ViewWidget_people")
    number_table = main_win.findChild(QTableWidget, "ViewWidget_number")
    paying_table = main_win.findChild(QTableWidget, "ViewWidget_paying")
    
    if booking_table:
        fill_booking_table(con, booking_table)
    if guests_table:
        fill_guests_table(con, guests_table)
    if number_table:
        fill_number_table(con, number_table)
    if paying_table:
        fill_paying_table(con, paying_table)
    
    con.close()
    
    if booking_table:
        booking_table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.SelectedClicked)
    if guests_table:
        guests_table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.SelectedClicked)
    if number_table:
        number_table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.SelectedClicked)
    if paying_table:
        paying_table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.SelectedClicked)

    search_edit = main_win.findChild(QLineEdit, "SearchLabel")
    if search_edit and booking_table:
        def apply_booking_filter(text: str):
            text = text.strip().lower()
            for row in range(booking_table.rowCount()):
                match = False
                if not text:
                    match = True
                else:
                    for col in range(booking_table.columnCount()):
                        item = booking_table.item(row, col)
                        if item and text in item.text().lower():
                            match = True
                            break
                booking_table.setRowHidden(row, not match)

        search_edit.textChanged.connect(apply_booking_filter)
    
    add_btn = main_win.findChild(QPushButton, "AddButton_booking")
    if add_btn and booking_table:
        def on_add():
            dialog = QDialog()
            uic.loadUi(str(Path(__file__).parent / "ui" / "AddDialog.ui"), dialog)
            
            # В AddDialog нет lineEdit_1, поэтому перечисляем имена явно
            field_names = ["lineEdit", "lineEdit_2", "lineEdit_3",
                           "lineEdit_4", "lineEdit_5", "lineEdit_6", "lineEdit_7"]
            fields = [dialog.findChild(QLineEdit, name) for name in field_names]
            save_btn = dialog.findChild(QPushButton, "pushButton")
            
            def on_save():
                values = [f.text().strip() if f is not None else "" for f in fields]
                fio, passport, check_in, check_out, category_name, room_no, status_name = values
                
                if not all(values):
                    QMessageBox.warning(dialog, "Ошибка", "Заполните все поля")
                    return
                
                row = booking_table.rowCount()
                booking_table.insertRow(row)
                booking_table.setItem(row, 0, QTableWidgetItem(fio))
                booking_table.setItem(row, 1, QTableWidgetItem(passport))
                booking_table.setItem(row, 2, QTableWidgetItem(check_in))
                booking_table.setItem(row, 3, QTableWidgetItem(check_out))
                booking_table.setItem(row, 4, QTableWidgetItem(category_name))
                booking_table.setItem(row, 5, QTableWidgetItem(room_no))
                booking_table.setItem(row, 6, QTableWidgetItem(status_name))
                
                dialog.accept()
            
            save_btn.clicked.connect(on_save)
            dialog.exec()
        
        add_btn.clicked.connect(on_add)

    delete_btn = main_win.findChild(QPushButton, "pushButton")
    if delete_btn and booking_table:
        def on_delete():
            row = booking_table.currentRow()
            if row >= 0:
                booking_table.removeRow(row)
            else:
                QMessageBox.warning(main_win, "Ошибка", "Выберите строку для удаления")
        
        delete_btn.clicked.connect(on_delete)

