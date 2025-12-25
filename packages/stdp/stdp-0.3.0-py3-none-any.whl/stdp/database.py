import pymysql

# Подключение к базе данных
def connect():
    conn = pymysql.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="0210", 
        database="hotel",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )
    return conn