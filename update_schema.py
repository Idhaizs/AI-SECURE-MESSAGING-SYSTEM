import pymysql

conn = pymysql.connect(host='127.0.0.1', user='root', password='', database='secure_messaging', cursorclass=pymysql.cursors.DictCursor)
cursor = conn.cursor()

# 1. Groups table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS groups (
        group_id INT AUTO_INCREMENT PRIMARY KEY,
        group_name VARCHAR(100) NOT NULL,
        created_by INT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

# 2. Group members table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS group_members (
        group_id INT NOT NULL,
        user_id INT NOT NULL,
        role ENUM('admin', 'member') DEFAULT 'member',
        joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (group_id, user_id)
    )
''')

# 3. Group messages table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS group_messages (
        group_msg_id INT AUTO_INCREMENT PRIMARY KEY,
        group_id INT NOT NULL,
        sender_id INT NOT NULL,
        encrypted_content TEXT NOT NULL,
        message_type ENUM('text', 'file', 'voice') DEFAULT 'text',
        is_flagged TINYINT(1) DEFAULT 0,
        threat_type VARCHAR(100) DEFAULT 'none',
        sent_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

# 4. Add columns to messages if needed
cursor.execute('DESCRIBE messages')
msg_cols = [r['Field'] for r in cursor.fetchall()]

if 'is_pinned' not in msg_cols:
    cursor.execute('ALTER TABLE messages ADD COLUMN is_pinned TINYINT(1) DEFAULT 0')

if 'is_deleted' not in msg_cols:
    cursor.execute('ALTER TABLE messages ADD COLUMN is_deleted TINYINT(1) DEFAULT 0')

conn.commit()
conn.close()
print("Group tables and message columns successfully updated!")
