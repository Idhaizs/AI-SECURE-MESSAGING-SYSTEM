from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from app.utils.db import query_db
from app.utils.audit import log_action
from functools import wraps

admin_bp = Blueprint('admin', __name__)

@admin_bp.context_processor
def inject_admin_globals():
    if 'user_id' in session and session.get('role') == 'admin':
        try:
            unread = query_db("SELECT COUNT(*) as count FROM alerts WHERE status = 'unread'", one=True)
            return {'unread_alerts_count': unread['count'] if unread else 0}
        except Exception:
            return {'unread_alerts_count': 0}
    return {'unread_alerts_count': 0}

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated

# ─── Admin Dashboard ──────────────────────────────────────────────
@admin_bp.route('/admin')
@admin_required
def dashboard():
    # Summary stats
    total_messages = query_db("SELECT COUNT(*) as count FROM messages", one=True)['count']
    total_suspicious = query_db("SELECT COUNT(*) as count FROM messages WHERE is_flagged = 1", one=True)['count']
    total_blocked = query_db("SELECT COUNT(*) as count FROM users WHERE status = 'blocked'", one=True)['count']
    unread_alerts_count = query_db("SELECT COUNT(*) as count FROM alerts WHERE status = 'unread'", one=True)['count']
    unread_flagged_count = query_db("SELECT COUNT(*) as count FROM messages WHERE is_flagged = 1", one=True)['count']
    unread_alerts = max(unread_alerts_count, unread_flagged_count)
    
    # Recent suspicious messages
    recent_suspicious = query_db("""
        SELECT m.message_id, m.threat_type, m.sent_at,
               s.username as sender, r.username as receiver
        FROM messages m
        JOIN users s ON m.sender_id = s.user_id
        JOIN users r ON m.receiver_id = r.user_id
        WHERE m.is_flagged = 1
        ORDER BY m.sent_at DESC LIMIT 10
    """)
    
    # Recent alerts
    recent_alerts = query_db("""
        SELECT a.id as alert_id, a.threat_type, a.severity, a.created_at, u.username 
        FROM alerts a JOIN users u ON a.user_id = u.user_id
        WHERE a.status = 'unread'
        ORDER BY a.created_at DESC LIMIT 5
    """)

    if not recent_alerts:
        flagged_alerts = query_db("""
            SELECT m.id as alert_id, m.threat_type, 'high' as severity, m.sent_at as created_at, s.username
            FROM messages m JOIN users s ON m.sender_id = s.user_id
            WHERE m.is_flagged = 1
            ORDER BY m.sent_at DESC LIMIT 5
        """)
        recent_alerts = flagged_alerts
    
    # Threat breakdown for chart
    threat_breakdown = query_db("""
        SELECT threat_type, COUNT(*) as count 
        FROM messages WHERE is_flagged = 1 
        GROUP BY threat_type
    """)
    
    return render_template('admin/dashboard.html',
        total_messages=total_messages,
        total_suspicious=total_suspicious,
        total_blocked=total_blocked,
        unread_alerts=unread_alerts,
        recent_suspicious=recent_suspicious,
        recent_alerts=recent_alerts,
        threat_breakdown=list(threat_breakdown)
    )

# ─── Unread Alerts API (For Real-time Badge & Toast Notifications) ────
@admin_bp.route('/admin/api/unread-alerts')
@admin_required
def unread_alerts_api():
    unread_alerts_count = query_db("SELECT COUNT(*) as count FROM alerts WHERE status = 'unread'", one=True)['count']
    unread_flagged_count = query_db("SELECT COUNT(*) as count FROM messages WHERE is_flagged = 1", one=True)['count']
    total_unread = max(unread_alerts_count, unread_flagged_count)
    
    latest_alert = query_db("""
        SELECT a.*, COALESCE(u.username, u2.username, 'System') as username 
        FROM alerts a 
        LEFT JOIN users u ON a.user_id = u.user_id 
        LEFT JOIN users u2 ON a.triggered_by_id = u2.user_id
        ORDER BY a.id DESC LIMIT 1
    """, one=True)
    
    if not latest_alert:
        latest_msg = query_db("""
            SELECT m.threat_type, s.username, m.sent_at as created_at
            FROM messages m JOIN users s ON m.sender_id = s.user_id
            WHERE m.is_flagged = 1 ORDER BY m.id DESC LIMIT 1
        """, one=True)
        if latest_msg:
            latest_alert = {
                'username': latest_msg['username'],
                'threat_type': latest_msg['threat_type'],
                'alert_detail': f"Flagged threat message detected from {latest_msg['username']}"
            }

    return jsonify({
        'unread_count': total_unread,
        'latest_alert': dict(latest_alert) if latest_alert else None
    })

# ─── Suspicious Messages ──────────────────────────────────────────
@admin_bp.route('/admin/suspicious')
@admin_required
def suspicious():
    messages = query_db("""
        SELECT m.id, m.message_id, m.threat_type, m.sent_at, m.is_flagged, m.encrypted_content, m.message_type,
               s.username as sender, s.status as sender_status,
               COALESCE(r.username, 'System / Receiver') as receiver,
               f.file_name
        FROM messages m
        JOIN users s ON m.sender_id = s.user_id
        LEFT JOIN users r ON m.receiver_id = r.user_id
        LEFT JOIN files f ON (m.id = f.message_id OR m.message_id = f.message_id)
        WHERE m.is_flagged = 1
        ORDER BY m.sent_at DESC
    """)
    
    from app.utils.encryption import decrypt_message
    formatted_messages = []
    for msg in messages:
        msg_dict = dict(msg)
        try:
            content = decrypt_message(msg['encrypted_content'])
            if isinstance(content, bytes):
                content = content.decode('utf-8', errors='ignore')
            msg_dict['content'] = content
        except Exception:
            msg_dict['content'] = msg.get('file_name') or "Encrypted Content"
        formatted_messages.append(msg_dict)

    return render_template('admin/suspicious.html', messages=formatted_messages)

# ─── Alerts ───────────────────────────────────────────────────────
@admin_bp.route('/admin/alerts')
@admin_required
def alerts():
    alerts_list = query_db("""
        SELECT a.id as id, COALESCE(a.alert_id, a.id) as alert_id, a.*, 
               COALESCE(u.username, u2.username, 'System') as username,
               COALESCE(u.status, u2.status, 'active') as user_status,
               m.encrypted_content, m.message_type,
               r.username as receiver_name
        FROM alerts a 
        LEFT JOIN users u ON a.user_id = u.user_id
        LEFT JOIN users u2 ON a.triggered_by_id = u2.user_id
        LEFT JOIN messages m ON (a.message_id = m.id OR a.message_id = m.message_id)
        LEFT JOIN users r ON m.receiver_id = r.user_id
        ORDER BY a.id DESC
    """)
    
    flagged_messages = query_db("""
        SELECT m.id as id, m.id as message_id, m.threat_type, m.created_at, m.sent_at, m.encrypted_content, m.message_type,
               s.user_id, s.username, s.status as user_status,
               r.username as receiver_name
        FROM messages m
        JOIN users s ON m.sender_id = s.user_id
        LEFT JOIN users r ON m.receiver_id = r.user_id
        WHERE m.is_flagged = 1
        ORDER BY m.id DESC
    """)
    
    from app.utils.encryption import decrypt_message
    existing_msg_ids = set()
    formatted_alerts = []
    
    for alert in alerts_list:
        alert_dict = dict(alert)
        if alert.get('message_id'):
            existing_msg_ids.add(alert['message_id'])
            
        if alert.get('encrypted_content'):
            try:
                content = decrypt_message(alert['encrypted_content'])
                if isinstance(content, bytes):
                    content = content.decode('utf-8', errors='ignore')
                alert_dict['attempted_content'] = content
            except Exception:
                alert_dict['attempted_content'] = alert.get('alert_detail') or alert.get('details') or ''
        else:
            alert_dict['attempted_content'] = alert.get('alert_detail') or alert.get('details') or ''
        formatted_alerts.append(alert_dict)
        
    for msg in flagged_messages:
        if msg['id'] not in existing_msg_ids and msg.get('message_id') not in existing_msg_ids:
            try:
                content = decrypt_message(msg['encrypted_content'])
                if isinstance(content, bytes):
                    content = content.decode('utf-8', errors='ignore')
            except Exception:
                content = "Suspicious Content"
                
            formatted_alerts.append({
                'alert_id': f"m-{msg['id']}",
                'id': msg['id'],
                'user_id': msg['user_id'],
                'username': msg['username'],
                'user_status': msg['user_status'],
                'threat_type': msg['threat_type'],
                'alert_detail': f"Flagged threat message from '{msg['username']}': \"{content}\"",
                'attempted_content': content,
                'severity': 'high',
                'status': 'unread',
                'created_at': msg['sent_at'] or msg['created_at']
            })
            
    formatted_alerts.sort(key=lambda x: str(x.get('created_at', '')), reverse=True)
    return render_template('admin/alerts.html', alerts=formatted_alerts)

# ─── Mark Alert Read ──────────────────────────────────────────────
@admin_bp.route('/admin/alerts/<int:alert_id>/read', methods=['POST'])
@admin_required
def mark_alert_read(alert_id):
    query_db("UPDATE alerts SET status = 'read' WHERE alert_id = %s", (alert_id,), commit=True)
    return jsonify({'success': True})

# ─── Resolve Alert ────────────────────────────────────────────────
@admin_bp.route('/admin/alerts/<int:alert_id>/resolve', methods=['POST'])
@admin_required
def resolve_alert(alert_id):
    query_db("UPDATE alerts SET status = 'resolved' WHERE alert_id = %s OR id = %s", (alert_id, alert_id), commit=True)
    log_action(session['user_id'], 'RESOLVE_ALERT', request.remote_addr, f"Alert ID: {alert_id}")
    return jsonify({'success': True})

# ─── Delete Alert ─────────────────────────────────────────────────
@admin_bp.route('/admin/alerts/<int:alert_id>/delete', methods=['POST'])
@admin_required
def delete_alert(alert_id):
    query_db("DELETE FROM alerts WHERE alert_id = %s OR id = %s", (alert_id, alert_id), commit=True)
    log_action(session['user_id'], 'ADMIN_DELETE_ALERT', request.remote_addr, f"Deleted alert ID: {alert_id}")
    return jsonify({'success': True})

# ─── Delete Suspicious Message ─────────────────────────────────────
@admin_bp.route('/admin/suspicious/<int:message_id>/delete', methods=['POST'])
@admin_required
def delete_suspicious_message(message_id):
    query_db("DELETE FROM messages WHERE message_id = %s", (message_id,), commit=True)
    log_action(session['user_id'], 'ADMIN_DELETE_MESSAGE', request.remote_addr, f"Deleted suspicious message ID: {message_id}")
    return jsonify({'success': True})

# ─── User Management ──────────────────────────────────────────────
@admin_bp.route('/admin/users')
@admin_required
def users():
    users = query_db("SELECT id, COALESCE(user_id, id) as user_id, username, user_id_str, full_name, email, role, status, created_at, last_login FROM users ORDER BY id DESC")
    return render_template('admin/users.html', users=users)

# ─── Approve User Registration ─────────────────────────────────────
@admin_bp.route('/admin/users/<int:user_id>/approve', methods=['POST'])
@admin_required
def approve_user(user_id):
    user = query_db("SELECT * FROM users WHERE id = %s OR user_id = %s", (user_id, user_id), one=True)
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
        
    actual_id = user['id']
    assigned_id = f"SFC-{1000 + actual_id}"
    query_db("UPDATE users SET status = 'active', user_id_str = %s, user_id = %s WHERE id = %s", (assigned_id, actual_id, actual_id), commit=True)
    
    from app.utils.email_helper import send_approval_email
    send_approval_email(user['email'], user['full_name'] or user['username'], assigned_id)
    
    log_action(session['user_id'], 'APPROVE_USER', request.remote_addr, f"Approved user ID: {actual_id}, Assigned User ID: {assigned_id}")
    return jsonify({'success': True, 'assigned_id': assigned_id})

# ─── Reject User Registration ──────────────────────────────────────
@admin_bp.route('/admin/users/<int:user_id>/reject', methods=['POST'])
@admin_required
def reject_user(user_id):
    user = query_db("SELECT * FROM users WHERE id = %s OR user_id = %s", (user_id, user_id), one=True)
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
        
    actual_id = user['id']
    query_db("UPDATE users SET status = 'rejected' WHERE id = %s", (actual_id,), commit=True)
    
    from app.utils.email_helper import send_rejection_email
    send_rejection_email(user['email'], user['full_name'] or user['username'])
    
    log_action(session['user_id'], 'REJECT_USER', request.remote_addr, f"Rejected user ID: {actual_id}")
    return jsonify({'success': True})

# ─── Block/Unblock User ───────────────────────────────────────────
@admin_bp.route('/admin/users/<int:user_id>/toggle', methods=['POST'])
@admin_required
def toggle_user(user_id):
    user = query_db("SELECT * FROM users WHERE id = %s OR user_id = %s", (user_id, user_id), one=True)
    if not user:
        return jsonify({'success': False}), 404
    
    actual_id = user['id']
    new_status = 'blocked' if user['status'] == 'active' else 'active'
    query_db("UPDATE users SET status = %s WHERE id = %s", (new_status, actual_id), commit=True)
    log_action(session['user_id'], f'USER_{new_status.upper()}', request.remote_addr, f"User ID: {actual_id}")
    
    return jsonify({'success': True, 'new_status': new_status})

# ─── Admin Create User ─────────────────────────────────────────────
@admin_bp.route('/admin/users/create', methods=['POST'])
@admin_required
def create_user():
    from flask_bcrypt import Bcrypt
    from app.utils.encryption import hash_answer
    bcrypt = Bcrypt()
    
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    full_name = data.get('full_name', '').strip() or username
    email = data.get('email', '').strip() or f"{username}@example.com"
    password = data.get('password', '').strip()
    role = data.get('role', 'user')
    question = data.get('question', 'What is your favourite movie?')
    answer = data.get('answer', 'secret')
    
    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400
        
    existing = query_db("SELECT user_id FROM users WHERE username = %s", (username,), one=True)
    if existing:
        return jsonify({'success': False, 'error': 'Username already exists'}), 400
        
    pw_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    a_hash = hash_answer(answer)
    
    uid = query_db("INSERT INTO users (username, user_id_str, full_name, email, password_hash, role, status) VALUES (%s, %s, %s, %s, %s, %s, 'active')",
                   (username, username, full_name, email, pw_hash, role), commit=True)
                   
    query_db("INSERT INTO security_questions (user_id, question, answer_hash) VALUES (%s, %s, %s)", (uid, question, a_hash), commit=True)
    
    log_action(session['user_id'], 'ADMIN_CREATE_USER', request.remote_addr, f"Created user: {username}")
    return jsonify({'success': True, 'user_id': uid})

# ─── Admin Delete User ─────────────────────────────────────────────
@admin_bp.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    query_db("DELETE FROM users WHERE id = %s OR user_id = %s", (user_id, user_id), commit=True)
    log_action(session['user_id'], 'ADMIN_DELETE_USER', request.remote_addr, f"Deleted user ID: {user_id}")
    return jsonify({'success': True})

# ─── Security Reports ─────────────────────────────────────────────
@admin_bp.route('/admin/reports')
@admin_required
def reports():
    # Message stats per day (last 7 days)
    raw_daily = query_db("""
        SELECT DATE_FORMAT(sent_at, '%%d %%b') as date, 
               COUNT(*) as total,
               SUM(is_flagged) as suspicious
        FROM messages
        WHERE sent_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        GROUP BY DATE_FORMAT(sent_at, '%%d %%b'), DATE(sent_at)
        ORDER BY DATE(sent_at) ASC
    """)
    
    daily_stats = []
    for row in raw_daily:
        daily_stats.append({
            'date': str(row['date']),
            'total': int(row['total'] or 0),
            'suspicious': int(row['suspicious'] or 0)
        })
    
    # Top threat types
    threat_stats = query_db("""
        SELECT threat_type, COUNT(*) as count
        FROM messages WHERE is_flagged = 1
        GROUP BY threat_type ORDER BY count DESC
    """)
    
    # File scan stats
    file_stats = query_db("""
        SELECT scan_result, COUNT(*) as count
        FROM files GROUP BY scan_result
    """)
    
    # Overview Metrics
    total_messages = query_db("SELECT COUNT(*) as count FROM messages", one=True)['count']
    total_flagged = query_db("SELECT COUNT(*) as count FROM messages WHERE is_flagged = 1", one=True)['count']
    total_files = query_db("SELECT COUNT(*) as count FROM files", one=True)['count']
    total_blocked = query_db("SELECT COUNT(*) as count FROM users WHERE status = 'blocked'", one=True)['count']
    threat_rate = round((total_flagged / total_messages * 100), 1) if total_messages > 0 else 0.0
    
    # Recent threat incidents for security intelligence log table
    threat_incidents = query_db("""
        SELECT m.id, m.threat_type, m.sent_at,
               s.username as sender, s.status as sender_status,
               COALESCE(r.username, 'System') as receiver
        FROM messages m
        JOIN users s ON m.sender_id = s.user_id
        LEFT JOIN users r ON m.receiver_id = r.user_id
        WHERE m.is_flagged = 1
        ORDER BY m.sent_at DESC LIMIT 6
    """)
    
    return render_template('admin/reports.html',
        daily_stats=daily_stats,
        threat_stats=list(threat_stats),
        file_stats=list(file_stats),
        total_messages=total_messages,
        total_flagged=total_flagged,
        total_files=total_files,
        total_blocked=total_blocked,
        threat_rate=threat_rate,
        threat_incidents=threat_incidents
    )

# ─── Audit Logs ───────────────────────────────────────────────────
@admin_bp.route('/admin/audit-logs')
@admin_required
def audit_logs():
    logs = query_db("""
        SELECT al.*, u.username 
        FROM audit_logs al 
        LEFT JOIN users u ON al.user_id = u.user_id
        ORDER BY al.timestamp DESC LIMIT 200
    """)
    return render_template('admin/audit_logs.html', logs=logs)

# ─── Export Audit Logs to CSV ──────────────────────────────────────
@admin_bp.route('/admin/audit-logs/export-csv')
@admin_required
def export_audit_logs_csv():
    import csv
    from io import StringIO
    from flask import Response
    
    logs = query_db("""
        SELECT al.log_id, al.timestamp, u.username, al.action, al.ip_address, al.detail 
        FROM audit_logs al 
        LEFT JOIN users u ON al.user_id = u.user_id
        ORDER BY al.timestamp DESC
    """)
    
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Log ID', 'Timestamp', 'Username', 'Action', 'IP Address', 'Details'])
    
    for l in logs:
        cw.writerow([
            l['log_id'],
            l['timestamp'].strftime('%Y-%m-%d %H:%M:%S') if l['timestamp'] else '',
            l['username'] or 'System',
            l['action'],
            l['ip_address'] or '-',
            l['detail'] or '-'
        ])
        
    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=system_audit_logs.csv"}
    )

# ─── Printable PDF Audit Report ───────────────────────────────────
@admin_bp.route('/admin/audit-logs/export-pdf')
@admin_required
def export_audit_logs_pdf():
    logs = query_db("""
        SELECT al.*, u.username 
        FROM audit_logs al 
        LEFT JOIN users u ON al.user_id = u.user_id
        ORDER BY al.timestamp DESC LIMIT 200
    """)
    return render_template('admin/printable_audit_logs.html', logs=logs)

# ─── Delete Audit Log Entry ────────────────────────────────────────
@admin_bp.route('/admin/audit-logs/<int:log_id>/delete', methods=['POST'])
@admin_required
def delete_audit_log(log_id):
    query_db("DELETE FROM audit_logs WHERE log_id = %s", (log_id,), commit=True)
    return jsonify({'success': True})

@admin_bp.route('/admin/audit-logs/clear-all', methods=['POST'])
@admin_required
def clear_all_audit_logs():
    query_db("DELETE FROM audit_logs", commit=True)
    log_action(session['user_id'], 'CLEAR_AUDIT_LOGS', request.remote_addr, "Cleared all system audit logs")
    return jsonify({'success': True})

# ─── Settings ─────────────────────────────────────────────────────
@admin_bp.route('/admin/settings')
@admin_required
def settings():
    auto_block = query_db("SELECT setting_value FROM system_settings WHERE setting_key = 'auto_block_threats'", one=True)
    max_size = query_db("SELECT setting_value FROM system_settings WHERE setting_key = 'max_file_size_mb'", one=True)
    
    return render_template('admin/settings.html',
        auto_block=auto_block['setting_value'] if auto_block else 'true',
        max_file_size=max_size['setting_value'] if max_size else '25'
    )

@admin_bp.route('/admin/settings/save', methods=['POST'])
@admin_required
def save_settings():
    data = request.get_json() or {}
    auto_block = 'true' if data.get('auto_block') else 'false'
    max_size = str(data.get('max_file_size', 25))
    
    query_db("INSERT INTO system_settings (setting_key, setting_value) VALUES ('auto_block_threats', %s) ON DUPLICATE KEY UPDATE setting_value = %s", (auto_block, auto_block), commit=True)
    query_db("INSERT INTO system_settings (setting_key, setting_value) VALUES ('max_file_size_mb', %s) ON DUPLICATE KEY UPDATE setting_value = %s", (max_size, max_size), commit=True)
    
    log_action(session['user_id'], 'UPDATE_SETTINGS', request.remote_addr, f"AutoBlock: {auto_block}, MaxSize: {max_size}MB")
    return jsonify({'success': True})
