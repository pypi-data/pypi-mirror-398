import pymysql


def connect():
    return pymysql.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password="0210", 
        database="hotel",
        cursorclass=pymysql.cursors.DictCursor  # результаты как словари (удобнее: row['role'])
    )