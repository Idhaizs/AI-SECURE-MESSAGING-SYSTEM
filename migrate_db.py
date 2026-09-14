import pymysql
import os
import sys

sys.path.append(os.path.abspath('.'))

from app.utils.encryption import hash_answer
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

conn = pymysql.connect(host='127.0.0.1', user='root', password='', database='secure_messaging', cursorclass=pymysql.cursors.DictCursor)
cursor = conn.cursor()

# 1. Add missing columns to users table if needed
cursor.execute('DESCRIBE users')
cols = [r['Field'] for r in cursor.fetchall()]

if 'user_id' not in cols:
    cursor.execute('ALTER TABLE users ADD COLUMN user_id INT')
    cursor.execute('UPDATE users SET user_id = id')
    print('Added user_id column')

if 'username' not in cols:
    cursor.execute('ALTER TABLE users ADD COLUMN username VARCHAR(50)')
    cursor.execute('UPDATE users SET username = user_id_str')
    print('Added username column')

if 'email' not in cols:
    cursor.execute('ALTER TABLE users ADD COLUMN email VARCHAR(100)')
    cursor.execute('UPDATE users SET email = CONCAT(user_id_str, "@example.com")')
    cursor.execute('UPDATE users SET email = "admin@aisecuremsg.com" WHERE user_id_str = "admin"')
    print('Added email column')

if 'status' not in cols:
    cursor.execute('ALTER TABLE users ADD COLUMN status ENUM("active", "blocked") DEFAULT "active"')
    cursor.execute('UPDATE users SET status = IF(is_blocked = 1, "blocked", "active")')
    print('Added status column')

# 2. Create security_questions table if not exists
cursor.execute('''
    CREATE TABLE IF NOT EXISTS security_questions (
        question_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL UNIQUE,
        question VARCHAR(255) NOT NULL,
        answer_hash VARCHAR(255) NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

# Map the exact answers user specified
user_answers = {
    'sarah.hassan': ('What is your favourite movie?', 'Batman'),
    'amir.zulkifli': ('What city were you born in?', 'Ampang'),
    'nurul.aina': ('What was the name of your first pet?', 'Loko'),
    'daniel.lim': ('What is your childhood nickname?', 'Ipan'),
    'Soparjo': ('What is your favourite movie?', 'Spiderman'),
    'admin': ('What is your secret code?', 'lqK9cR8XBw')
}

user_passwords = {
    'sarah.hassan': 'S@rah123',
    'amir.zulkifli': '@Mir123',
    'nurul.aina': 'Aina@123',
    'daniel.lim': 'D@niel123',
    'Soparjo': 'Sop@rjo123',
    'admin': 'Admin@123'
}

cursor.execute('SELECT id, user_id_str FROM users')
users = cursor.fetchall()

for u in users:
    uid = u['id']
    uname = u['user_id_str']
    
    if uname in user_answers:
        q, a = user_answers[uname]
        a_hash = hash_answer(a)
        cursor.execute('''
            INSERT INTO security_questions (user_id, question, answer_hash)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE question = VALUES(question), answer_hash = VALUES(answer_hash)
        ''', (uid, q, a_hash))
        
    if uname in user_passwords:
        pw_hash = bcrypt.generate_password_hash(user_passwords[uname]).decode('utf-8')
        cursor.execute('UPDATE users SET password_hash = %s WHERE id = %s', (pw_hash, uid))

# 3. Create audit_logs table if not exists
cursor.execute('''
    CREATE TABLE IF NOT EXISTS audit_logs (
        log_id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NULL,
        action VARCHAR(100) NOT NULL,
        ip_address VARCHAR(45),
        detail TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

conn.commit()
conn.close()
print('secure_messaging database fully synchronized!')
