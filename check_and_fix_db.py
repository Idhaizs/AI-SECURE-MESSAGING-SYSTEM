import pymysql

conn = pymysql.connect(host='127.0.0.1', user='root', password='', database='secure_messaging', cursorclass=pymysql.cursors.DictCursor)
cursor = conn.cursor()

def check_table(t):
    cursor.execute(f'DESCRIBE {t}')
    return [r['Field'] for r in cursor.fetchall()]

# Fix messages table
msg_cols = check_table('messages')
if 'message_id' not in msg_cols:
    cursor.execute('ALTER TABLE messages ADD COLUMN message_id INT')
    cursor.execute('UPDATE messages SET message_id = id')
    print('Added message_id to messages')

if 'sent_at' not in msg_cols:
    cursor.execute('ALTER TABLE messages ADD COLUMN sent_at DATETIME DEFAULT CURRENT_TIMESTAMP')
    cursor.execute('UPDATE messages SET sent_at = created_at')
    print('Added sent_at to messages')

if 'message_type' not in msg_cols:
    cursor.execute('ALTER TABLE messages ADD COLUMN message_type ENUM("text", "file") DEFAULT "text"')
    print('Added message_type to messages')

# Fix files table
file_cols = check_table('files')
if 'file_id' not in file_cols:
    cursor.execute('ALTER TABLE files ADD COLUMN file_id INT')
    cursor.execute('UPDATE files SET file_id = id')
    print('Added file_id to files')

if 'file_name' not in file_cols:
    cursor.execute('ALTER TABLE files ADD COLUMN file_name VARCHAR(255)')
    if 'original_filename' in file_cols:
        cursor.execute('UPDATE files SET file_name = original_filename')
    print('Added file_name to files')

if 'user_id' not in file_cols:
    cursor.execute('ALTER TABLE files ADD COLUMN user_id INT')
    if 'uploader_id' in file_cols:
        cursor.execute('UPDATE files SET user_id = uploader_id')
    print('Added user_id to files')

if 'message_id' not in file_cols:
    cursor.execute('ALTER TABLE files ADD COLUMN message_id INT NULL')
    print('Added message_id to files')

if 'file_hash' not in file_cols:
    cursor.execute('ALTER TABLE files ADD COLUMN file_hash VARCHAR(64) DEFAULT ""')
    print('Added file_hash to files')

if 'file_path' not in file_cols:
    cursor.execute('ALTER TABLE files ADD COLUMN file_path VARCHAR(500) DEFAULT ""')
    print('Added file_path to files')

if 'is_scanned' not in file_cols:
    cursor.execute('ALTER TABLE files ADD COLUMN is_scanned TINYINT(1) DEFAULT 0')
    print('Added is_scanned to files')

if 'scan_result' not in file_cols:
    cursor.execute('ALTER TABLE files ADD COLUMN scan_result VARCHAR(50) DEFAULT "clean"')
    print('Added scan_result to files')

# Fix alerts table
alert_cols = check_table('alerts')
if 'alert_id' not in alert_cols:
    cursor.execute('ALTER TABLE alerts ADD COLUMN alert_id INT')
    cursor.execute('UPDATE alerts SET alert_id = id')
    print('Added alert_id to alerts')

if 'user_id' not in alert_cols:
    cursor.execute('ALTER TABLE alerts ADD COLUMN user_id INT')
    if 'triggered_by_id' in alert_cols:
        cursor.execute('UPDATE alerts SET user_id = triggered_by_id')
    print('Added user_id to alerts')

if 'threat_type' not in alert_cols:
    cursor.execute('ALTER TABLE alerts ADD COLUMN threat_type VARCHAR(100) DEFAULT "none"')
    if 'alert_type' in alert_cols:
        cursor.execute('UPDATE alerts SET threat_type = alert_type')
    print('Added threat_type to alerts')

if 'alert_detail' not in alert_cols:
    cursor.execute('ALTER TABLE alerts ADD COLUMN alert_detail TEXT NULL')
    if 'details' in alert_cols:
        cursor.execute('UPDATE alerts SET alert_detail = details')
    print('Added alert_detail to alerts')

if 'status' not in alert_cols:
    cursor.execute('ALTER TABLE alerts ADD COLUMN status ENUM("unread", "read", "resolved") DEFAULT "unread"')
    if 'is_resolved' in alert_cols:
        cursor.execute('UPDATE alerts SET status = IF(is_resolved = 1, "resolved", "unread")')
    print('Added status to alerts')

conn.commit()
conn.close()
print("All tables in secure_messaging database successfully aligned and synchronized!")
