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

def auto_migrate_database():
    try:
        conn = get_db()
        with conn.cursor() as cursor:
            cursor.execute("DESCRIBE group_messages")
            cols = [r['Field'] for r in cursor.fetchall()]
            
            # Ensure iv and encrypted_content allow Null/Text insertions without MySQL Strict Mode errors
            try:
                cursor.execute("ALTER TABLE group_messages MODIFY COLUMN iv BLOB NULL DEFAULT NULL")
                cursor.execute("ALTER TABLE group_messages MODIFY COLUMN encrypted_content TEXT NOT NULL")
            except Exception:
                pass

            if 'message_type' not in cols:
                cursor.execute("ALTER TABLE group_messages ADD COLUMN message_type ENUM('text', 'file', 'voice') DEFAULT 'text'")
            if 'file_id' not in cols:
                cursor.execute("ALTER TABLE group_messages ADD COLUMN file_id INT NULL")
            if 'message_id' not in cols:
                cursor.execute("ALTER TABLE group_messages ADD COLUMN message_id INT NULL")
            if 'sent_at' not in cols:
                cursor.execute("ALTER TABLE group_messages ADD COLUMN sent_at DATETIME DEFAULT CURRENT_TIMESTAMP")
            if 'is_deleted' not in cols:
                cursor.execute("ALTER TABLE group_messages ADD COLUMN is_deleted TINYINT(1) DEFAULT 0")
            conn.commit()
    except Exception as e:
        print(f"Auto-migration note: {e}")
    finally:
        try:
            conn.close()
        except Exception:
            pass
