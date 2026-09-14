import pymysql
from config import Config

def get_db():
    conn = pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )
    return conn

def query_db(sql, args=(), one=False, commit=False):
    conn = get_db()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, args)
            if commit:
                conn.commit()
                return cursor.lastrowid
            rv = cursor.fetchall()
            return (rv[0] if rv else None) if one else rv
    finally:
        conn.close()
