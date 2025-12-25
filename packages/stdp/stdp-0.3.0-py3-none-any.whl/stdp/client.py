from PyQt6.QtWidgets import QMainWindow, QTableWidgetItem, QTableWidget, QPushButton, QLineEdit, QTextEdit, QMessageBox
from PyQt6 import uic
from pathlib import Path
from datetime import datetime

try:
    from .database import connect
except ImportError:
    from database import connect


# Настройка окна для обычного пользователя
def setup_client_window(main_win, login):
    ui_path = Path(__file__).parent / "ui" / "ClientWindow.ui"
    uic.loadUi(str(ui_path), main_win)

    con = connect()
    # Получение идентификатора текущего пользователя
    with con.cursor() as cur:
        cur.execute("SELECT id FROM users WHERE login = %s", (login,))
        user_id = (cur.fetchone() or {}).get('id')

    # Заполнение таблицы доступных элементов
    def fill_items_table(con, table):
        cur = con.cursor()
        cur.execute("""
            SELECT r.room_no AS 'Номер', r.price AS 'Цена', rc.name AS 'Категория', r.room_status AS 'Статус'
            FROM rooms r JOIN room_categories rc ON r.category_id = rc.id
        """)
        rows = cur.fetchall()
        cur.close()

        table.setRowCount(len(rows))
        for row_idx, row_data in enumerate(rows):
            for col_idx, col_name in enumerate(['Номер', 'Цена', 'Категория', 'Статус']):
                table.setItem(row_idx, col_idx, QTableWidgetItem(str(row_data.get(col_name, ""))))
        table.resizeColumnsToContents()

    # Заполнение таблицы записей пользователя
    def fill_user_records_table(con, table, user_id):
        cur = con.cursor()
        cur.execute("""
            SELECT b.check_in AS 'Заезд', b.check_out AS 'Выезд', r.room_no AS 'Номер', r.price AS 'Цена'
            FROM booking b JOIN rooms r ON r.id = b.room_id
            WHERE b.client_id = %s ORDER BY b.check_in DESC
        """, (user_id,))
        rows = cur.fetchall()
        cur.close()

        table.setRowCount(len(rows))
        for row_idx, row_data in enumerate(rows):
            date_start = str(row_data.get('Заезд', ""))
            date_end = str(row_data.get('Выезд', ""))
            item_code = str(row_data.get('Номер', ""))
            # Вычисление итоговой суммы
            try:
                days = (datetime.strptime(date_end, '%Y-%m-%d') - datetime.strptime(date_start, '%Y-%m-%d')).days
                total = f"{float(row_data.get('Цена', 0)) * days:.2f} руб." if days > 0 else "0 руб."
            except:
                total = "0 руб."
            table.setItem(row_idx, 0, QTableWidgetItem(date_start))
            table.setItem(row_idx, 1, QTableWidgetItem(date_end))
            table.setItem(row_idx, 2, QTableWidgetItem(item_code))
            table.setItem(row_idx, 3, QTableWidgetItem(total))
        table.resizeColumnsToContents()

    items_table = main_win.findChild(QTableWidget, "NumTable")
    records_table = main_win.findChild(QTableWidget, "tableWidget")

    # Поиск полей ввода
    room_edit = main_win.findChild(QLineEdit, "lineEdit")
    date_in_edit = main_win.findChild(QLineEdit, "lineEdit_2")
    date_out_edit = main_win.findChild(QLineEdit, "lineEdit_3")
    fio_edit = main_win.findChild(QTextEdit, "textEdit")
    passport_edit = main_win.findChild(QTextEdit, "textEdit_2")
    book_btn = main_win.findChild(QPushButton, "pushButton")

    # Загрузка данных в таблицы
    if items_table:
        fill_items_table(con, items_table)
    if records_table and user_id:
        fill_user_records_table(con, records_table, user_id)

    con.close()

    # Обработка кнопки бронирования
    if book_btn and records_table:
        def on_book():
            # Получение данных из полей ввода
            room_no = room_edit.text().strip() if room_edit else ""
            date_start = date_in_edit.text().strip() if date_in_edit else ""
            date_end = date_out_edit.text().strip() if date_out_edit else ""
            fio = fio_edit.toPlainText().strip() if fio_edit else ""
            passport = passport_edit.toPlainText().strip() if passport_edit else ""

            # Проверка заполненности всех полей
            if not all([room_no, date_start, date_end, fio, passport]):
                QMessageBox.warning(main_win, "Ошибка", "Заполните все поля")
                return

            # Проверка формата дат
            try:
                date_start_obj = datetime.strptime(date_start, "%Y-%m-%d")
                date_end_obj = datetime.strptime(date_end, "%Y-%m-%d")
                if date_start_obj >= date_end_obj:
                    QMessageBox.warning(main_win, "Ошибка", "Дата выезда должна быть позже даты заезда")
                    return
            except ValueError:
                QMessageBox.warning(main_win, "Ошибка", "Неверный формат даты (используйте ГГ-ММ-ДД)")
                return

            # Поиск цены номера в таблице доступных элементов
            price = 0
            if items_table:
                for row in range(items_table.rowCount()):
                    if items_table.item(row, 0) and items_table.item(row, 0).text() == room_no:
                        price_item = items_table.item(row, 1)
                        if price_item:
                            try:
                                price = float(price_item.text())
                            except:
                                price = 0
                        break

            # Вычисление итоговой суммы
            try:
                days = (date_end_obj - date_start_obj).days
                total = f"{price * days:.2f} руб." if days > 0 and price > 0 else "0 руб."
            except:
                total = "0 руб."

            # Добавление новой строки в таблицу "Мои брони"
            row_count = records_table.rowCount()
            records_table.insertRow(row_count)
            records_table.setItem(row_count, 0, QTableWidgetItem(date_start))
            records_table.setItem(row_count, 1, QTableWidgetItem(date_end))
            records_table.setItem(row_count, 2, QTableWidgetItem(room_no))
            records_table.setItem(row_count, 3, QTableWidgetItem(total))
            records_table.resizeColumnsToContents()

            # Очистка полей ввода
            if room_edit:
                room_edit.clear()
            if date_in_edit:
                date_in_edit.clear()
            if date_out_edit:
                date_out_edit.clear()
            if fio_edit:
                fio_edit.clear()
            if passport_edit:
                passport_edit.clear()

            QMessageBox.information(main_win, "Успех", "Бронирование добавлено в таблицу!")

        book_btn.clicked.connect(on_book)
