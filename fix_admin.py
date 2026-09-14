import os
import sys

# Ensure app path is available
sys.path.append(os.path.abspath('.'))

from app.utils.db import get_db
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()
new_hash = bcrypt.generate_password_hash('Admin@123').decode('utf-8')

conn = get_db()
try:
    with conn.cursor() as cursor:
        cursor.execute("UPDATE users SET password_hash = %s WHERE username = 'admin'", (new_hash,))
    conn.commit()
    print(f"Success! Admin hash updated to: {new_hash}")
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
