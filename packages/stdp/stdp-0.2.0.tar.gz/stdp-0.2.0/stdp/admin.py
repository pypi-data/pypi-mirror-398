from PyQt6.QtWidgets import QMainWindow, QTableWidget, QTableWidgetItem, QLineEdit, QPushButton, QDialog, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6 import uic
from pathlib import Path

try:
    from .database import connect
except ImportError:
    from database import connect


def fill_booking_table(con, table):
    cur = con.cursor()
    cur.execute("""
        SELECT b.id AS 'booking_id', u.id AS 'user_id', r.id AS 'room_id', s.id AS 'status_id',
        u.full_name AS 'ФИО гостя', u.passport AS 'Паспорт', b.check_in AS 'Заезд',
        b.check_out AS 'Выезд', c.name AS 'Тип номера', r.room_no AS 'Номер', s.name AS 'Статус'
        FROM booking b JOIN users u ON u.id = b.client_id JOIN rooms r ON r.id = b.room_id
        JOIN room_categories c ON c.id = r.category_id JOIN booking_status s ON s.id = b.status_id
        ORDER BY b.check_in DESC
    """)
    rows = cur.fetchall()
    cur.close()
    
    table.setRowCount(len(rows))
    for row_idx, row_data in enumerate(rows):
        for col_idx, col_name in enumerate(['ФИО гостя', 'Паспорт', 'Заезд', 'Выезд', 'Тип номера', 'Номер', 'Статус']):
            item = QTableWidgetItem(str(row_data.get(col_name, "")))
            if col_idx == 0:
                item.setData(1000, row_data.get('booking_id'))
                item.setData(1001, row_data.get('status_id'))
                item.setData(1002, row_data.get('user_id'))
                item.setData(1003, row_data.get('room_id'))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            table.setItem(row_idx, col_idx, item)
    table.resizeColumnsToContents()


def fill_guests_table(con, table):
    cur = con.cursor()
    cur.execute("""
        SELECT u.id AS 'user_id', b.id AS 'booking_id', u.full_name AS 'ФИО гостя',
        u.passport AS 'Паспорт', b.check_in AS 'Дата въезда', b.check_out AS 'Дата выезда'
        FROM users u JOIN booking b ON u.id = b.client_id
    """)
    rows = cur.fetchall()
    cur.close()
    
    table.setRowCount(len(rows))
    for row_idx, row_data in enumerate(rows):
        for col_idx, col_name in enumerate(['ФИО гостя', 'Паспорт', 'Дата въезда', 'Дата выезда']):
            item = QTableWidgetItem(str(row_data.get(col_name, "")))
            if col_idx == 0:
                item.setData(1000, row_data.get('user_id'))
                item.setData(1001, row_data.get('booking_id'))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            table.setItem(row_idx, col_idx, item)
    table.resizeColumnsToContents()


def fill_number_table(con, table):
    cur = con.cursor()
    cur.execute("""
        SELECT r.id AS 'room_id', r.category_id AS 'category_id', r.room_no AS 'Номер',
        rc.name AS 'Тип', r.price AS 'Цена', r.room_status AS 'Статус'
        FROM rooms r JOIN room_categories rc ON r.category_id = rc.id
    """)
    rows = cur.fetchall()
    cur.close()
    
    table.setRowCount(len(rows))
    for row_idx, row_data in enumerate(rows):
        for col_idx, col_name in enumerate(['Номер', 'Тип', 'Цена', 'Статус']):
            item = QTableWidgetItem(str(row_data.get(col_name, "")))
            if col_idx == 0:
                item.setData(1000, row_data.get('room_id'))
                item.setData(1001, row_data.get('category_id'))
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            table.setItem(row_idx, col_idx, item)
    table.resizeColumnsToContents()


def fill_paying_table(con, table):
    cur = con.cursor()
    cur.execute("""
        SELECT b.id AS 'booking_id', b.status_id AS 'status_id', CURDATE() AS 'Дата',
        u.full_name AS 'Гость', (r.price * DATEDIFF(b.check_out, b.check_in)) AS 'Сумма', bs.name AS 'Статус'
        FROM users u JOIN booking b ON u.id = b.client_id
        JOIN rooms r ON b.room_id = r.id JOIN booking_status bs ON b.status_id = bs.id
    """)
    rows = cur.fetchall()
    cur.close()
    
    table.setRowCount(len(rows))
    for row_idx, row_data in enumerate(rows):
        for col_idx, col_name in enumerate(['Дата', 'Гость', 'Сумма', 'Статус']):
            item = QTableWidgetItem(str(row_data.get(col_name, "")))
            if col_idx == 0:
                item.setData(1000, row_data.get('booking_id'))
                item.setData(1001, row_data.get('status_id'))
            if col_idx in [1, 3]:
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
            table.setItem(row_idx, col_idx, item)
    table.resizeColumnsToContents()


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
    
    def save_cell(table, row, col, updates_func):
        item, first = table.item(row, col), table.item(row, 0)
        if not (item and first):
            return
        con = connect()
        try:
            with con.cursor() as cur:
                updates_func(cur, first, item.text().strip(), col)
            con.commit()
        except Exception as e:
            con.rollback()
            QMessageBox.warning(main_win, "Ошибка", f"Не удалось сохранить: {str(e)}")
        finally:
            con.close()
    
    for table in [booking_table, guests_table, number_table, paying_table]:
        if table:
            table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.SelectedClicked)
    
    if booking_table:
        
        def booking_updates(cur, first, value, col):
            booking_id, user_id, room_id = first.data(1000), first.data(1002), first.data(1003)
            updates = {
                0: ("UPDATE users SET full_name = %s WHERE id = %s", (value, user_id)),
                1: ("UPDATE users SET passport = %s WHERE id = %s", (value, user_id)),
                2: ("UPDATE booking SET check_in = %s WHERE id = %s", (value, booking_id)),
                3: ("UPDATE booking SET check_out = %s WHERE id = %s", (value, booking_id)),
                5: ("UPDATE rooms SET room_no = %s WHERE id = %s", (value, room_id)),
            }
            if col in updates:
                cur.execute(*updates[col])
            elif col == 4:
                cur.execute("SELECT id FROM room_categories WHERE name = %s", (value,))
                if row := cur.fetchone():
                    cur.execute("UPDATE rooms SET category_id = %s WHERE id = %s", (row['id'], room_id))
            elif col == 6:
                cur.execute("SELECT id FROM booking_status WHERE name = %s", (value,))
                if row := cur.fetchone():
                    cur.execute("UPDATE booking SET status_id = %s WHERE id = %s", (row['id'], booking_id))
        
        booking_table.cellChanged.connect(lambda r, c: save_cell(booking_table, r, c, booking_updates))
    
    if guests_table:
        def guests_updates(cur, first, value, col):
            user_id, booking_id = first.data(1000), first.data(1001)
            updates = {
                0: ("UPDATE users SET full_name = %s WHERE id = %s", (value, user_id)),
                1: ("UPDATE users SET passport = %s WHERE id = %s", (value, user_id)),
                2: ("UPDATE booking SET check_in = %s WHERE id = %s", (value, booking_id)),
                3: ("UPDATE booking SET check_out = %s WHERE id = %s", (value, booking_id)),
            }
            if col in updates:
                cur.execute(*updates[col])
        
        guests_table.cellChanged.connect(lambda r, c: save_cell(guests_table, r, c, guests_updates))
    
    if number_table:
        def number_updates(cur, first, value, col):
            room_id = first.data(1000)
            updates = {
                0: ("UPDATE rooms SET room_no = %s WHERE id = %s", (value, room_id)),
                2: ("UPDATE rooms SET price = %s WHERE id = %s", (value, room_id)),
                3: ("UPDATE rooms SET room_status = %s WHERE id = %s", (value, room_id)),
            }
            if col in updates:
                cur.execute(*updates[col])
            elif col == 1:
                cur.execute("SELECT id FROM room_categories WHERE name = %s", (value,))
                if row := cur.fetchone():
                    cur.execute("UPDATE rooms SET category_id = %s WHERE id = %s", (row['id'], room_id))
        
        number_table.cellChanged.connect(lambda r, c: save_cell(number_table, r, c, number_updates))
    
    if paying_table:
        def paying_updates(cur, first, value, col):
            if col == 3:
                booking_id = first.data(1000)
                cur.execute("SELECT id FROM booking_status WHERE name = %s", (value,))
                if row := cur.fetchone():
                    cur.execute("UPDATE booking SET status_id = %s WHERE id = %s", (row['id'], booking_id))
        
        paying_table.cellChanged.connect(lambda r, c: save_cell(paying_table, r, c, paying_updates))

    search_edit = main_win.findChild(QLineEdit, "SearchLabel")
    if search_edit and booking_table:
        def apply_booking_filter(text):
            text = text.strip().lower()
            for row in range(booking_table.rowCount()):
                booking_table.setRowHidden(row, bool(text) and not any(
                    booking_table.item(row, col) and text in booking_table.item(row, col).text().lower()
                    for col in range(booking_table.columnCount())))
        search_edit.textChanged.connect(apply_booking_filter)
    
    add_btn = main_win.findChild(QPushButton, "AddButton_booking")
    if add_btn and booking_table:
        def on_add():
            dialog = QDialog()
            uic.loadUi(str(Path(__file__).parent / "ui" / "AddDialog.ui"), dialog)
            
            fields = [dialog.findChild(QLineEdit, name) for name in ["lineEdit", "lineEdit_2", "lineEdit_3", "lineEdit_4", "lineEdit_5", "lineEdit_6", "lineEdit_7"]]
            save_btn = dialog.findChild(QPushButton, "pushButton")
            
            def on_save():
                values = [f.text().strip() if f else "" for f in fields]
                if not all(values):
                    QMessageBox.warning(dialog, "Ошибка", "Заполните все поля")
                    return
                fio, passport, check_in, check_out, category_name, room_no, status_name = values
                con = connect()
                try:
                    with con.cursor() as cur:
                        cur.execute("SELECT id FROM users WHERE full_name = %s AND passport = %s", (fio, passport))
                        user_id = (cur.fetchone() or {}).get('id')
                        if not user_id:
                            cur.execute("INSERT INTO users (full_name, passport, role) VALUES (%s, %s, 'client')", (fio, passport))
                            user_id = cur.lastrowid
                        cur.execute("SELECT id FROM room_categories WHERE name = %s", (category_name,))
                        if not (cat := cur.fetchone()):
                            QMessageBox.warning(dialog, "Ошибка", f"Тип номера '{category_name}' не найден")
                            return
                        cur.execute("SELECT id FROM rooms WHERE room_no = %s AND category_id = %s", (room_no, cat['id']))
                        if not (room := cur.fetchone()):
                            QMessageBox.warning(dialog, "Ошибка", f"Номер '{room_no}' с типом '{category_name}' не найден")
                            return
                        cur.execute("SELECT id FROM booking_status WHERE name = %s", (status_name,))
                        if not (status := cur.fetchone()):
                            QMessageBox.warning(dialog, "Ошибка", f"Статус '{status_name}' не найден")
                            return
                        cur.execute("INSERT INTO booking (check_in, check_out, client_id, room_id, status_id) VALUES (%s, %s, %s, %s, %s)",
                                  (check_in, check_out, user_id, room['id'], status['id']))
                    con.commit()
                    QMessageBox.information(dialog, "Успех", "Бронирование добавлено!")
                    con_refresh = connect()
                    fill_booking_table(con_refresh, booking_table)
                    con_refresh.close()
                    dialog.accept()
                except Exception as e:
                    con.rollback()
                    QMessageBox.critical(dialog, "Ошибка", f"Не удалось добавить: {str(e)}")
                finally:
                    con.close()
            
            save_btn.clicked.connect(on_save)
            dialog.exec()
        
        add_btn.clicked.connect(on_add)

    delete_btn = main_win.findChild(QPushButton, "pushButton")
    if delete_btn and booking_table:
        def on_delete():
            row = booking_table.currentRow()
            if row < 0:
                QMessageBox.warning(main_win, "Ошибка", "Выберите строку для удаления")
                return
            first = booking_table.item(row, 0)
            if not first:
                return
            con = connect()
            try:
                with con.cursor() as cur:
                    cur.execute("DELETE FROM booking WHERE id = %s", (first.data(1000),))
                con.commit()
                booking_table.removeRow(row)
                QMessageBox.information(main_win, "Успех", "Бронирование удалено!")
            except Exception as e:
                con.rollback()
                QMessageBox.warning(main_win, "Ошибка", f"Не удалось удалить: {str(e)}")
            finally:
                con.close()
        delete_btn.clicked.connect(on_delete)