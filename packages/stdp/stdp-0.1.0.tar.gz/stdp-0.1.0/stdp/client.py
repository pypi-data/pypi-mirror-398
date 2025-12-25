from PyQt6.QtWidgets import QMainWindow, QPushButton, QTableWidgetItem, QTableWidget, QTextEdit, QLineEdit, QMessageBox
from PyQt6 import uic
from pathlib import Path
from datetime import datetime

from .database import connect

def setup_client_window(main_win, login):
    ui_path = Path(__file__).parent / "ui" / "ClientWindow.ui"
    uic.loadUi(str(ui_path), main_win)

    con = connect()
    with con.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE login = %s", (login,))
        user_row = cur.fetchone()
        user_id = user_row['id'] if user_row else None

    def fill_search_num_table(con, table):
        with con.cursor() as cur:
            cur.execute("SELECT r.room_no AS 'Номер', r.price AS 'Цена', rc.name AS 'Категория', r.room_status AS 'Статус' "
                       "FROM rooms r JOIN room_categories rc ON r.category_id = rc.id")
            rows = cur.fetchall()
        table.setRowCount(len(rows))
        for row_idx, row_data in enumerate(rows):
            for col_idx, col_name in enumerate(['Номер', 'Цена', 'Категория', 'Статус']):
                table.setItem(row_idx, col_idx, QTableWidgetItem(str(row_data.get(col_name, ""))))
        table.resizeColumnsToContents()

    def fill_client_booking_table(con, table, client_id):
        with con.cursor() as cur:
            cur.execute("SELECT b.check_in AS 'Заезд', b.check_out AS 'Выезд', r.room_no AS 'Номер', "
                       "r.price AS 'Цена', bs.name AS 'Статус' "
                       "FROM booking b JOIN rooms r ON r.id = b.room_id "
                       "JOIN booking_status bs ON bs.id = b.status_id WHERE b.client_id = %s ORDER BY b.check_in DESC",
                       (client_id,))
            rows = cur.fetchall()
        table.setRowCount(len(rows))
        for row_idx, row_data in enumerate(rows):
            check_in = str(row_data.get('Заезд', ""))
            check_out = str(row_data.get('Выезд', ""))
            room_no = str(row_data.get('Номер', ""))
            total = "0 руб."
            if row_data.get('Заезд') and row_data.get('Выезд') and row_data.get('Цена'):
                try:
                    days = (datetime.strptime(str(row_data['Выезд']), '%Y-%m-%d') - 
                           datetime.strptime(str(row_data['Заезд']), '%Y-%m-%d')).days
                    if days > 0:
                        total = f"{float(row_data['Цена']) * days:.2f} руб."
                except:
                    total = "Ошибка"
            table.setItem(row_idx, 0, QTableWidgetItem(check_in))
            table.setItem(row_idx, 1, QTableWidgetItem(check_out))
            table.setItem(row_idx, 2, QTableWidgetItem(room_no))
            table.setItem(row_idx, 3, QTableWidgetItem(total))
        table.resizeColumnsToContents()

    num_table = main_win.findChild(QTableWidget, "NumTable")
    booking_table = main_win.findChild(QTableWidget, "tableWidget")
    room_edit = main_win.findChild(QLineEdit, "lineEdit")
    date_in_edit = main_win.findChild(QLineEdit, "lineEdit_2")
    date_out_edit = main_win.findChild(QLineEdit, "lineEdit_3")
    fio_edit = main_win.findChild(QTextEdit, "textEdit")
    passport_edit = main_win.findChild(QTextEdit, "textEdit_2")
    book_btn = main_win.findChild(QPushButton, "pushButton")
    
    if num_table:
        fill_search_num_table(con, num_table)
    if booking_table and user_id:
        fill_client_booking_table(con, booking_table, user_id)

    if book_btn and booking_table:
        def on_book():
            room_no = room_edit.text().strip() if room_edit else ""
            check_in = date_in_edit.text().strip() if date_in_edit else ""
            check_out = date_out_edit.text().strip() if date_out_edit else ""
            fio = fio_edit.toPlainText().strip() if fio_edit else ""
            passport = passport_edit.toPlainText().strip() if passport_edit else ""

            if not all([room_no, check_in, check_out, fio, passport]):
                QMessageBox.warning(main_win, "Ошибка", "Заполните все поля")
                return

            try:
                check_in_date = datetime.strptime(check_in, "%Y-%m-%d")
                check_out_date = datetime.strptime(check_out, "%Y-%m-%d")
                if check_in_date >= check_out_date:
                    QMessageBox.warning(main_win, "Ошибка", "Дата выезда должна быть позже даты заезда")
                    return
            except ValueError:
                QMessageBox.warning(main_win, "Ошибка", "Неверный формат даты. Используйте формат ГГГГ-ММ-ДД")
                return
                
            row = booking_table.rowCount()
            booking_table.insertRow(row)
            try:
                days = (check_out_date - check_in_date).days
                total = f"{days * 1000:.2f} руб." if days > 0 else "0 руб."
            except:
                total = "0 руб."
            
            booking_table.setItem(row, 0, QTableWidgetItem(check_in))
            booking_table.setItem(row, 1, QTableWidgetItem(check_out))
            booking_table.setItem(row, 2, QTableWidgetItem(room_no))
            booking_table.setItem(row, 3, QTableWidgetItem(total))
            
            for widget in [room_edit, date_in_edit, date_out_edit, fio_edit, passport_edit]:
                if widget:
                    widget.clear()
            
            QMessageBox.information(main_win, "Успех", "Бронирование добавлено!")

        book_btn.clicked.connect(on_book)

    con.close()
