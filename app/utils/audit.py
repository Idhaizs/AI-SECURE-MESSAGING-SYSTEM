from app.utils.db import query_db

def log_action(user_id, action, ip_address=None, detail=None):
    try:
        query_db(
            "INSERT INTO audit_logs (user_id, action, ip_address, detail) VALUES (%s, %s, %s, %s)",
            (user_id, action, ip_address, detail),
            commit=True
        )
    except Exception:
        pass
