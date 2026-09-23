import os
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify
from werkzeug.utils import secure_filename
from app.utils.db import query_db
from app.utils.encryption import encrypt_message, decrypt_message, hash_file
from app.utils.ai_detection import full_message_scan, check_file_extension, scan_file_virustotal
from app.utils.audit import log_action
from config import Config
from functools import wraps

chat_bp = Blueprint('chat', __name__)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'user':
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.path.startswith('/chat/meetings') or request.path.startswith('/chat/send') or request.path.startswith('/chat/upload'):
                return jsonify({'success': False, 'error': 'Session expired. Please log in again.', 'redirect': '/login'}), 401
            return redirect(url_for('auth.login'))
        
        # Check if user account status is blocked in database
        u = query_db("SELECT status FROM users WHERE user_id = %s", (session['user_id'],), one=True)
        if u and u.get('status') == 'blocked':
            session.clear()
            from flask import flash
            flash('🚫 Your account has been suspended by Admin due to a security violation.', 'danger')
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.path.startswith('/chat/meetings') or request.path.startswith('/chat/send') or request.path.startswith('/chat/upload'):
                return jsonify({'success': False, 'error': '🚫 Your account has been suspended by Admin due to a security violation.', 'account_blocked': True, 'redirect': '/login'}), 401
            return redirect(url_for('auth.login'))
            
        return f(*args, **kwargs)
    return decorated

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

# ─── Chat Home ────────────────────────────────────────────────────
@chat_bp.route('/chat')
@login_required
def index():
    user_id = session['user_id']
    users = query_db("SELECT user_id, username FROM users WHERE user_id != %s AND role = 'user' AND status = 'active'", (user_id,))
    
    groups = query_db("""
        SELECT g.id as group_id, g.name as group_name, g.created_by_id, g.created_at 
        FROM `groups` g
        JOIN `group_members` gm ON g.id = gm.group_id
        WHERE gm.user_id = %s
        ORDER BY g.created_at DESC
    """, (user_id,))
    
    return render_template('chat/index.html', users=users, groups=groups or [])

# ─── Get Messages ─────────────────────────────────────────────────
@chat_bp.route('/chat/messages/<int:receiver_id>')
@login_required
def get_messages(receiver_id):
    user_id = session['user_id']
    is_group = request.args.get('is_group') in ['true', '1', 'True']
    
    try:
        if is_group:
            messages = query_db("""
                SELECT gm.*, 
                       s.username as sender_name,
                       f.file_name, f.file_id, f.scan_result, f.is_password_protected
                FROM group_messages gm
                JOIN users s ON gm.sender_id = s.user_id
                LEFT JOIN files f ON (gm.file_id = f.file_id OR (gm.id = f.message_id AND gm.message_type = 'file'))
                WHERE gm.group_id = %s AND (gm.is_deleted IS NULL OR gm.is_deleted = 0)
                ORDER BY gm.id ASC
            """, (receiver_id,))
            
            result = []
            for msg in (messages or []):
                if msg.get('is_deleted'):
                    content = "🚫 This message was deleted"
                else:
                    try:
                        content = decrypt_message(msg['encrypted_content'])
                        if isinstance(content, bytes):
                            content = content.decode('utf-8', errors='ignore')
                    except Exception:
                        content = msg.get('file_name') or "Encrypted Content"
                    
                time_val = msg.get('sent_at') or msg.get('created_at')
                time_str = time_val.strftime('%Y-%m-%d %H:%M:%S') if (time_val and hasattr(time_val, 'strftime')) else str(time_val or '')

                result.append({
                    'message_id': msg.get('message_id') or msg.get('id'),
                    'sender_id': msg['sender_id'],
                    'sender_name': msg['sender_name'],
                    'content': content,
                    'message_type': msg.get('message_type') or 'text',
                    'is_flagged': bool(msg.get('is_flagged')),
                    'threat_type': msg.get('threat_type') or 'none',
                    'is_deleted': bool(msg.get('is_deleted')),
                    'sent_at': time_str,
                    'file_name': msg.get('file_name'),
                    'file_id': msg.get('file_id'),
                    'scan_result': msg.get('scan_result'),
                    'is_password_protected': 1 if msg.get('is_password_protected') == 1 else 0,
                    'is_group': True,
                    'group_id': receiver_id
                })
            return jsonify(result)

        messages = query_db("""
            SELECT m.*, 
                   s.username as sender_name,
                   r.username as receiver_name,
                   f.file_name, f.file_id, f.scan_result, f.is_password_protected, f.uploader_id
            FROM messages m
            JOIN users s ON m.sender_id = s.user_id
            JOIN users r ON m.receiver_id = r.user_id
            LEFT JOIN files f ON (m.id = f.message_id OR m.message_id = f.message_id)
            WHERE ((m.sender_id = %s AND m.receiver_id = %s)
               OR (m.sender_id = %s AND m.receiver_id = %s))
              AND (m.is_deleted IS NULL OR m.is_deleted = 0)
            ORDER BY m.sent_at ASC, m.id ASC
        """, (user_id, receiver_id, receiver_id, user_id))
        
        result = []
        for msg in (messages or []):
            if msg.get('is_deleted'):
                content = "🚫 This message was deleted"
            else:
                try:
                    content = decrypt_message(msg['encrypted_content'])
                    if isinstance(content, bytes):
                        content = content.decode('utf-8', errors='ignore')
                except Exception:
                    content = msg.get('file_name') or "Encrypted Content"
                
            time_val = msg.get('sent_at') or msg.get('created_at')
            time_str = time_val.strftime('%Y-%m-%d %H:%M:%S') if (time_val and hasattr(time_val, 'strftime')) else str(time_val or '')

            result.append({
                'message_id': msg.get('message_id') or msg.get('id'),
                'sender_id': msg['sender_id'],
                'sender_name': msg['sender_name'],
                'content': content,
                'message_type': msg.get('message_type') or 'text',
                'is_flagged': bool(msg.get('is_flagged')),
                'threat_type': msg.get('threat_type') or 'none',
                'is_deleted': bool(msg.get('is_deleted')),
                'sent_at': time_str,
                'file_name': msg.get('file_name'),
                'file_id': msg.get('file_id'),
                'scan_result': msg.get('scan_result'),
                'is_password_protected': 1 if msg.get('is_password_protected') == 1 else 0
            })
        
        # Mark messages from receiver_id as read
        query_db("UPDATE messages SET is_read = 1 WHERE sender_id = %s AND receiver_id = %s AND (is_read = 0 OR is_read IS NULL)", (receiver_id, user_id), commit=True)
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ─── Unread Counts & Mark Read Endpoints ─────────────────────────
@chat_bp.route('/chat/unread-counts')
@login_required
def get_unread_counts():
    user_id = session['user_id']
    counts = query_db("""
        SELECT sender_id, COUNT(*) as count 
        FROM messages 
        WHERE receiver_id = %s AND (is_read = 0 OR is_read IS NULL) AND (is_deleted IS NULL OR is_deleted = 0)
        GROUP BY sender_id
    """, (user_id,))
    
    unread_map = {row['sender_id']: row['count'] for row in counts}
    return jsonify({'success': True, 'unread_counts': unread_map})

@chat_bp.route('/chat/mark-read/<int:sender_id>', methods=['POST'])
@login_required
def mark_messages_read(sender_id):
    user_id = session['user_id']
    query_db("UPDATE messages SET is_read = 1 WHERE sender_id = %s AND receiver_id = %s AND (is_read = 0 OR is_read IS NULL)", (sender_id, user_id), commit=True)
    return jsonify({'success': True})

# ─── Send Message ─────────────────────────────────────────────────
@chat_bp.route('/chat/send', methods=['POST'])
@login_required
def send_message():
    user_id = session['user_id']
    receiver_id = request.form.get('receiver_id')
    content = request.form.get('content', '').strip()
    is_group = request.form.get('is_group') in ['true', '1', 'True']
    
    if not content or not receiver_id:
        return jsonify({'success': False, 'error': 'Missing content or receiver'}), 400
    
    # AI Scan
    scan_result = full_message_scan(content)
    is_flagged = scan_result['is_suspicious']
    threat_type = scan_result['threat_type'] if is_flagged else 'none'
    
    # Encrypt
    encrypted = encrypt_message(content)
    
    if is_group:
        member = query_db("SELECT * FROM group_members WHERE group_id = %s AND user_id = %s", (receiver_id, user_id), one=True)
        if not member:
            return jsonify({'success': False, 'error': 'Not a member of this group'}), 403
            
        message_id = query_db(
            "INSERT INTO group_messages (group_id, sender_id, encrypted_content, message_type, is_flagged, threat_type, sent_at) VALUES (%s, %s, %s, 'text', %s, %s, NOW())",
            (receiver_id, user_id, encrypted, is_flagged, threat_type), commit=True
        )
        query_db("UPDATE group_messages SET message_id = id WHERE id = %s", (message_id,), commit=True)
    else:
        # Save to DB
        message_id = query_db(
            "INSERT INTO messages (sender_id, receiver_id, encrypted_content, message_type, is_flagged, threat_type, message_id) VALUES (%s, %s, %s, 'text', %s, %s, 0)",
            (user_id, receiver_id, encrypted, is_flagged, threat_type), commit=True
        )
        query_db("UPDATE messages SET message_id = id WHERE id = %s", (message_id,), commit=True)
    
    # Create alert & auto-block user account if suspicious
    if is_flagged:
        sender_info = query_db("SELECT username FROM users WHERE user_id = %s", (user_id,), one=True)
        sender_name = sender_info['username'] if sender_info else f"User {user_id}"
        
        if is_group:
            group_info = query_db("SELECT group_name FROM `groups` WHERE group_id = %s OR id = %s", (receiver_id, receiver_id), one=True)
            receiver_name = f"Group '{group_info['group_name']}'" if group_info and group_info.get('group_name') else f"Group {receiver_id}"
        else:
            receiver_info = query_db("SELECT username FROM users WHERE user_id = %s", (receiver_id,), one=True)
            receiver_name = receiver_info['username'] if receiver_info else f"User {receiver_id}"
        
        query_db("UPDATE users SET status = 'blocked' WHERE user_id = %s", (user_id,), commit=True)
        
        alert_detail = f"User '{sender_name}' sent {threat_type} to '{receiver_name}': \"{content[:100]}\" ({scan_result.get('detail', '')})"
        query_db(
            "INSERT INTO alerts (message_id, user_id, threat_type, alert_detail, severity) VALUES (%s, %s, %s, %s, %s)",
            (message_id, user_id, threat_type, alert_detail, 'high'), commit=True
        )
        log_action(user_id, 'AUTO_BLOCK_SUSPICIOUS', request.remote_addr, f"User '{sender_name}' (ID: {user_id}) was AUTO-BLOCKED for sending {threat_type} to '{receiver_name}': \"{content[:100]}\"")
        
        try:
            from app import socketio
            socketio.emit('account_blocked', {
                'error': f"🚫 Security Threat Detected ({threat_type})! Your account has been automatically suspended by System."
            }, room=f'user_{user_id}')
            socketio.emit('admin_threat_alert', {
                'sender_name': sender_name,
                'user_id': user_id,
                'threat_type': threat_type,
                'alert_detail': alert_detail
            }, room='admin_room')
        except Exception:
            pass

        session.clear()
        from flask import flash
        flash('🚫 Your account has been automatically suspended by Admin due to a security violation.', 'danger')
        return jsonify({
            'success': False,
            'account_blocked': True,
            'redirect': '/login',
            'error': f"🚫 Security Threat Detected ({threat_type})! Your account has been automatically suspended by Admin."
        })
    
    log_action(user_id, 'SEND_MESSAGE', request.remote_addr, f"To {'group' if is_group else 'user'}: {receiver_id}")
    
    return jsonify({
        'success': True,
        'message_id': message_id,
        'is_flagged': is_flagged,
        'threat_type': threat_type,
        'warning': scan_result['detail'] if is_flagged else None
    })

# ─── Upload File ──────────────────────────────────────────────────
@chat_bp.route('/chat/upload', methods=['POST'])
@login_required
def upload_file():
    user_id = session['user_id']
    receiver_id = request.form.get('receiver_id')
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    sender_info = query_db("SELECT username FROM users WHERE user_id = %s", (user_id,), one=True)
    receiver_info = query_db("SELECT username FROM users WHERE user_id = %s", (receiver_id,), one=True) if receiver_id else None
    sender_name = sender_info['username'] if sender_info else f"User {user_id}"
    receiver_name = receiver_info['username'] if receiver_info else "System"

    # Check extension threat first (e.g. .bat, .vbs, .exe, .cmd, .ps1)
    ext_check = check_file_extension(file.filename)
    if ext_check['is_suspicious']:
        query_db("UPDATE users SET status = 'blocked' WHERE user_id = %s", (user_id,), commit=True)
        
        # Insert flagged message record for visibility in suspicious messages table
        encrypted_blocked_content = encrypt_message(f"🚫 Blocked File Threat Attempt: {file.filename} (Extension: {ext_check['extension']})")
        msg_id = query_db(
            "INSERT INTO messages (sender_id, receiver_id, encrypted_content, message_type, is_flagged, threat_type, message_id) VALUES (%s, %s, %s, 'file', 1, 'suspicious_attachment', 0)",
            (user_id, receiver_id or 0, encrypted_blocked_content), commit=True
        )
        query_db("UPDATE messages SET message_id = id WHERE id = %s", (msg_id,), commit=True)
        
        # Insert file record
        query_db(
            "INSERT INTO files (uploader_id, user_id, receiver_id, message_id, file_name, file_hash, file_path, is_scanned, scan_result, original_filename, stored_filename, encrypted_key, iv, is_password_protected) VALUES (%s, %s, %s, %s, %s, '', '', 1, 'blocked', %s, %s, '', '', 0)",
            (user_id, user_id, receiver_id or 0, msg_id, file.filename, file.filename, file.filename), commit=True
        )
        
        alert_detail = f"User '{sender_name}' (ID: {user_id}) was AUTO-BLOCKED attempting to upload suspicious file: '{file.filename}' (Extension: {ext_check['extension']})"
        query_db(
            "INSERT INTO alerts (message_id, user_id, triggered_by_id, threat_type, alert_detail, severity, status) VALUES (%s, %s, %s, 'suspicious_attachment', %s, 'high', 'unread')",
            (msg_id, user_id, user_id, alert_detail), commit=True
        )
        log_action(user_id, 'AUTO_BLOCK_FILE_THREAT', request.remote_addr, f"User '{sender_name}' (ID: {user_id}) was AUTO-BLOCKED for attempting to upload blocked threat file: '{file.filename}'")

        try:
            from app import socketio
            socketio.emit('account_blocked', {
                'error': f"🚫 Suspicious file type blocked: {ext_check['extension']}. Account automatically suspended due to security violation."
            }, room=f'user_{user_id}')
            socketio.emit('admin_threat_alert', {
                'sender_name': sender_name,
                'user_id': user_id,
                'threat_type': 'suspicious_attachment',
                'alert_detail': alert_detail
            }, room='admin_room')
        except Exception:
            pass

        session.clear()
        from flask import flash
        flash('🚫 Your account has been automatically suspended by Admin due to a security violation.', 'danger')
        return jsonify({'success': False, 'account_blocked': True, 'redirect': '/login', 'error': f"🚫 Suspicious file type blocked: {ext_check['extension']}. Account automatically suspended due to security violation."}), 400

    if not allowed_file(file.filename):
        alert_detail = f"User '{sender_name}' attempted to upload unallowed file format: '{file.filename}'"
        query_db(
            "INSERT INTO alerts (message_id, user_id, triggered_by_id, threat_type, alert_detail, severity, status) VALUES (NULL, %s, %s, 'unallowed_file_type', %s, 'medium', 'unread')",
            (user_id, user_id, alert_detail), commit=True
        )
        log_action(user_id, 'BLOCKED_FILE_UPLOAD', request.remote_addr, alert_detail)
        return jsonify({'success': False, 'error': 'File type not allowed'}), 400
    
    # Check max file size setting
    size_setting = query_db("SELECT setting_value FROM system_settings WHERE setting_key = 'max_file_size_mb'", one=True)
    max_mb = int(size_setting['setting_value']) if size_setting else 25
    file.seek(0, os.SEEK_END)
    file_size_bytes = file.tell()
    file.seek(0)
    
    if file_size_bytes > max_mb * 1024 * 1024:
        return jsonify({'success': False, 'error': f"File exceeds maximum allowed limit of {max_mb}MB"}), 400
    
    # Save file
    filename = secure_filename(file.filename)
    upload_path = os.path.join(Config.UPLOAD_FOLDER, str(user_id))
    os.makedirs(upload_path, exist_ok=True)
    file_path = os.path.join(upload_path, filename)
    file.save(file_path)
    
    # Check optional file password
    file_password = request.form.get('file_password', '').strip()
    from werkzeug.security import generate_password_hash, check_password_hash
    is_password_protected = 1 if file_password else 0
    file_password_hash = generate_password_hash(file_password) if file_password else None

    # Generate SHA-256 hash
    file_hash = hash_file(file_path)
    
    # VirusTotal scan (hash only - no file upload for privacy)
    vt_result = scan_file_virustotal(file_hash)
    scan_result = vt_result.get('scan_result', 'pending')
    
    # Block malicious files
    if scan_result == 'malicious':
        os.remove(file_path)
        query_db("UPDATE users SET status = 'blocked' WHERE user_id = %s", (user_id,), commit=True)
        
        encrypted_malicious_content = encrypt_message(f"🚫 VirusTotal Malicious File: {filename}")
        msg_id = query_db(
            "INSERT INTO messages (sender_id, receiver_id, encrypted_content, message_type, is_flagged, threat_type, message_id) VALUES (%s, %s, %s, 'file', 1, 'malicious_file', 0)",
            (user_id, receiver_id or 0, encrypted_malicious_content), commit=True
        )
        query_db("UPDATE messages SET message_id = id WHERE id = %s", (msg_id,), commit=True)
        
        alert_detail = f"User '{sender_name}' was AUTO-BLOCKED for uploading malicious file '{filename}' confirmed by VirusTotal scan."
        query_db(
            "INSERT INTO alerts (message_id, user_id, threat_type, alert_detail, severity) VALUES (%s, %s, 'malicious_file', %s, 'high')",
            (msg_id, user_id, alert_detail), commit=True
        )
        log_action(user_id, 'AUTO_BLOCK_MALICIOUS_FILE', request.remote_addr, f"User '{sender_name}' (ID: {user_id}) was AUTO-BLOCKED for malicious file: '{filename}' (VirusTotal scan confirmed)")
        session.clear()
        from flask import flash
        flash('🚫 Your account has been automatically suspended by Admin due to a security violation.', 'danger')
        return jsonify({'success': False, 'account_blocked': True, 'redirect': '/login', 'error': 'File blocked: detected as malicious by security scan. Account automatically suspended for security review.'}), 400
    
    is_group = request.form.get('is_group') in ['true', '1', 'True']
    
    # Save message record
    encrypted_path = encrypt_message(file_path)
    if is_group:
        message_id = query_db(
            "INSERT INTO group_messages (group_id, sender_id, encrypted_content, message_type, is_flagged, threat_type, sent_at) VALUES (%s, %s, %s, 'file', %s, %s, NOW())",
            (receiver_id, user_id, encrypted_path, 1 if scan_result == 'suspicious' else 0, 'suspicious_attachment' if scan_result == 'suspicious' else 'none'),
            commit=True
        )
        query_db("UPDATE group_messages SET message_id = id WHERE id = %s", (message_id,), commit=True)
    else:
        message_id = query_db(
            "INSERT INTO messages (sender_id, receiver_id, encrypted_content, message_type, is_flagged, threat_type, message_id) VALUES (%s, %s, %s, %s, %s, %s, 0)",
            (user_id, receiver_id, encrypted_path, 'file', 1 if scan_result == 'suspicious' else 0, 'suspicious_attachment' if scan_result == 'suspicious' else 'none'),
            commit=True
        )
        query_db("UPDATE messages SET message_id = id WHERE id = %s", (message_id,), commit=True)
    
    # Save file record with password protection details
    file_id = query_db(
        "INSERT INTO files (uploader_id, user_id, receiver_id, message_id, file_name, file_hash, file_path, is_scanned, scan_result, original_filename, stored_filename, encrypted_key, iv, is_password_protected, file_password_hash) VALUES (%s, %s, %s, %s, %s, %s, %s, 1, %s, %s, %s, %s, %s, %s, %s)",
        (user_id, user_id, receiver_id, message_id, filename, file_hash, file_path, scan_result, filename, filename, '', '', is_password_protected, file_password_hash),
        commit=True
    )
    
    if is_group:
        query_db("UPDATE group_messages SET file_id = %s WHERE id = %s", (file_id, message_id), commit=True)
    
    if scan_result == 'suspicious':
        query_db(
            "INSERT INTO alerts (message_id, user_id, triggered_by_id, threat_type, alert_detail, severity, status) VALUES (%s, %s, %s, 'suspicious_attachment', %s, 'medium', 'unread')",
            (message_id, user_id, user_id, f"Uploaded suspicious file: '{filename}' (Scan: {scan_result})"), commit=True
        )
    
    log_action(user_id, 'UPLOAD_FILE', request.remote_addr, f"File: {filename}, Scan: {scan_result}, Group: {is_group}")
    
    return jsonify({
        'success': True,
        'message_id': message_id,
        'file_id': file_id,
        'file_name': filename,
        'scan_result': scan_result,
        'is_password_protected': is_password_protected,
        'is_group': is_group
    })

# ─── Download File ────────────────────────────────────────────────
@chat_bp.route('/chat/download/<file_id>')
@login_required
def download_file(file_id):
    from flask import send_file
    from werkzeug.security import check_password_hash
    user_id = session['user_id']
    
    if not str(file_id).isdigit():
        return jsonify({'error': 'Invalid file ID'}), 400

    file_id_num = int(file_id)
    file = query_db("""
        SELECT f.*, m.sender_id, m.receiver_id 
        FROM files f JOIN messages m ON (f.message_id = m.message_id OR f.message_id = m.id)
        WHERE f.file_id = %s OR f.id = %s OR m.id = %s OR m.message_id = %s
    """, (file_id_num, file_id_num, file_id_num, file_id_num), one=True)
    
    if not file:
        return jsonify({'error': 'File not found'}), 404
    
    uploader_id = file.get('uploader_id') or file.get('sender_id')
    # Only sender or receiver (or admin) can access
    if int(file['sender_id']) != int(user_id) and int(file['receiver_id']) != int(user_id) and session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    filename = file.get('file_name') or file.get('original_filename') or 'file'

    # Check password protection for recipients (uploader and admin can download directly)
    if file.get('is_password_protected') == 1 and int(uploader_id) != int(user_id) and session.get('role') != 'admin':
        provided_password = request.args.get('password', '')
        if not provided_password:
            return jsonify({'requires_password': True, 'file_id': file_id_num, 'file_name': filename}), 403

        if not check_password_hash(file['file_password_hash'], provided_password):
            log_action(user_id, 'FILE_DOWNLOAD_FAILED_PASSWORD', request.remote_addr, f"Failed password attempt for File ID: {file_id_num} ({filename})")
            return jsonify({'error': 'Incorrect file password'}), 401

    ext = filename.split('.')[-1].lower() if '.' in filename else ''
    
    mimetype = None
    if ext == 'webm':
        mimetype = 'audio/webm'
    elif ext == 'mp3':
        mimetype = 'audio/mpeg'
    elif ext == 'wav':
        mimetype = 'audio/wav'
    elif ext == 'ogg':
        mimetype = 'audio/ogg'
        
    log_action(user_id, 'FILE_DOWNLOAD_SUCCESS', request.remote_addr, f"File ID: {file_id} ({filename})")
    as_attachment = True if request.args.get('download') == '1' else False

    target_path = file['file_path']
    if not os.path.isabs(target_path) or not os.path.exists(target_path):
        from flask import current_app
        proj_root = os.path.dirname(current_app.root_path)
        candidate = os.path.abspath(os.path.join(proj_root, target_path))
        if os.path.exists(candidate):
            target_path = candidate
        else:
            target_path = os.path.abspath(target_path)

    return send_file(target_path, mimetype=mimetype, as_attachment=as_attachment, download_name=filename)

# ─── Delete Message ───────────────────────────────────────────────
@chat_bp.route('/chat/message/<int:message_id>/delete', methods=['POST'])
@login_required
def delete_message(message_id):
    user_id = session['user_id']
    msg = query_db("SELECT sender_id FROM messages WHERE message_id = %s", (message_id,), one=True)
    if not msg:
        return jsonify({'success': False, 'error': 'Message not found'}), 404
        
    if int(msg['sender_id']) != int(user_id) and session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
    query_db("UPDATE messages SET is_deleted = 1 WHERE message_id = %s", (message_id,), commit=True)
    log_action(user_id, 'DELETE_MESSAGE', request.remote_addr, f"Message ID: {message_id}")
    return jsonify({'success': True})

# ─── Get Users List ───────────────────────────────────────────────
@chat_bp.route('/chat/users')
@login_required
def get_users():
    user_id = session['user_id']
    users = query_db(
        "SELECT user_id, username FROM users WHERE user_id != %s AND role = 'user' AND status = 'active'",
        (user_id,)
    )
    return jsonify(list(users))

# ─── Create Group ─────────────────────────────────────────────────
@chat_bp.route('/chat/groups/create', methods=['POST'])
@login_required
def create_group():
    user_id = session['user_id']
    data = request.get_json() or {}
    group_name = data.get('group_name', '').strip()
    member_ids = data.get('member_ids', [])
    
    if not group_name or not member_ids:
        return jsonify({'success': False, 'error': 'Group name and registered members are required'}), 400
    
    # Ensure all selected member_ids exist in users table
    valid_users = query_db("SELECT user_id FROM users WHERE role = 'user' AND status = 'active'")
    valid_ids = {u['user_id'] for u in valid_users}
    
    selected_members = [int(m) for m in member_ids if int(m) in valid_ids]
    if not selected_members:
        return jsonify({'success': False, 'error': 'No valid registered members selected'}), 400
    
    # Create group
    group_id = query_db(
        "INSERT INTO `groups` (name, created_by_id, created_at) VALUES (%s, %s, NOW())",
        (group_name, user_id), commit=True
    )
    
    # Add creator as admin
    query_db("INSERT INTO `group_members` (group_id, user_id, role, joined_at) VALUES (%s, %s, 'admin', NOW())", (group_id, user_id), commit=True)
    
    # Add selected members
    for mid in selected_members:
        if mid != user_id:
            query_db("INSERT INTO `group_members` (group_id, user_id, role, joined_at) VALUES (%s, %s, 'member', NOW())", (group_id, mid), commit=True)
            
    log_action(user_id, 'CREATE_GROUP', request.remote_addr, f"Group ID: {group_id}")
    return jsonify({'success': True, 'group_id': group_id, 'group_name': group_name})

# ─── Get User Groups ──────────────────────────────────────────────
@chat_bp.route('/chat/groups')
@login_required
def get_groups():
    user_id = session['user_id']
    groups = query_db("""
        SELECT g.id as group_id, g.name as group_name, g.description, g.created_by_id, g.created_at 
        FROM `groups` g
        JOIN `group_members` gm ON g.id = gm.group_id
        WHERE gm.user_id = %s
        ORDER BY g.created_at DESC
    """, (user_id,))
    return jsonify(list(groups))

# ─── Group Management Endpoints ────────────────────────────────────

@chat_bp.route('/chat/groups/<int:group_id>/details')
@login_required
def get_group_details(group_id):
    user_id = session['user_id']
    
    membership = query_db("SELECT role FROM `group_members` WHERE group_id = %s AND user_id = %s", (group_id, user_id), one=True)
    if not membership:
        return jsonify({'success': False, 'error': 'Access denied'}), 403
        
    group = query_db("SELECT id, name, description, created_by_id, created_at FROM `groups` WHERE id = %s", (group_id,), one=True)
    if not group:
        return jsonify({'success': False, 'error': 'Group not found'}), 404
        
    is_admin = (group['created_by_id'] == user_id) or (membership.get('role') == 'admin')
    
    members = query_db("""
        SELECT u.user_id, u.username, gm.role, gm.joined_at
        FROM `group_members` gm
        JOIN users u ON gm.user_id = u.user_id
        WHERE gm.group_id = %s
        ORDER BY gm.role DESC, u.username ASC
    """, (group_id,))
    
    member_user_ids = [m['user_id'] for m in members]
    all_users = query_db("SELECT user_id, username FROM users WHERE role = 'user' AND status = 'active'")
    available_users = [u for u in all_users if u['user_id'] not in member_user_ids]
    
    return jsonify({
        'success': True,
        'group': group,
        'is_admin': is_admin,
        'members': list(members),
        'available_users': available_users
    })

@chat_bp.route('/chat/groups/<int:group_id>/update', methods=['POST'])
@login_required
def update_group(group_id):
    user_id = session['user_id']
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    
    if not name:
        return jsonify({'success': False, 'error': 'Group name is required'}), 400
        
    group = query_db("SELECT created_by_id FROM `groups` WHERE id = %s", (group_id,), one=True)
    membership = query_db("SELECT role FROM `group_members` WHERE group_id = %s AND user_id = %s", (group_id, user_id), one=True)
    
    is_admin = group and ((group['created_by_id'] == user_id) or (membership and membership.get('role') == 'admin'))
    if not is_admin:
        return jsonify({'success': False, 'error': 'Admin permission required'}), 403
        
    query_db("UPDATE `groups` SET name = %s, description = %s WHERE id = %s", (name, description, group_id), commit=True)
    log_action(user_id, 'UPDATE_GROUP', request.remote_addr, f"Group ID: {group_id}")
    return jsonify({'success': True, 'name': name, 'description': description})

@chat_bp.route('/chat/groups/<int:group_id>/members/add', methods=['POST'])
@login_required
def add_group_member(group_id):
    user_id = session['user_id']
    data = request.get_json() or {}
    target_user_id = data.get('user_id')
    
    if not target_user_id:
        return jsonify({'success': False, 'error': 'User ID required'}), 400
        
    group = query_db("SELECT created_by_id FROM `groups` WHERE id = %s", (group_id,), one=True)
    membership = query_db("SELECT role FROM `group_members` WHERE group_id = %s AND user_id = %s", (group_id, user_id), one=True)
    
    is_admin = group and ((group['created_by_id'] == user_id) or (membership and membership.get('role') == 'admin'))
    if not is_admin:
        return jsonify({'success': False, 'error': 'Admin permission required'}), 403
        
    existing = query_db("SELECT id FROM `group_members` WHERE group_id = %s AND user_id = %s", (group_id, target_user_id), one=True)
    if existing:
        return jsonify({'success': False, 'error': 'User already in group'}), 400
        
    query_db("INSERT INTO `group_members` (group_id, user_id, role, joined_at) VALUES (%s, %s, 'member', NOW())", (group_id, target_user_id), commit=True)
    log_action(user_id, 'ADD_GROUP_MEMBER', request.remote_addr, f"Group ID: {group_id}, User ID: {target_user_id}")
    return jsonify({'success': True})

@chat_bp.route('/chat/groups/<int:group_id>/members/remove', methods=['POST'])
@login_required
def remove_group_member(group_id):
    user_id = session['user_id']
    data = request.get_json() or {}
    target_user_id = data.get('user_id')
    
    if not target_user_id:
        return jsonify({'success': False, 'error': 'User ID required'}), 400
        
    group = query_db("SELECT created_by_id FROM `groups` WHERE id = %s", (group_id,), one=True)
    membership = query_db("SELECT role FROM `group_members` WHERE group_id = %s AND user_id = %s", (group_id, user_id), one=True)
    
    is_admin = group and ((group['created_by_id'] == user_id) or (membership and membership.get('role') == 'admin'))
    if not is_admin:
        return jsonify({'success': False, 'error': 'Admin permission required'}), 403
        
    query_db("DELETE FROM `group_members` WHERE group_id = %s AND user_id = %s", (group_id, target_user_id), commit=True)
    log_action(user_id, 'REMOVE_GROUP_MEMBER', request.remote_addr, f"Group ID: {group_id}, User ID: {target_user_id}")
    return jsonify({'success': True})

@chat_bp.route('/chat/groups/<int:group_id>/leave', methods=['POST'])
@login_required
def leave_group(group_id):
    user_id = session['user_id']
    query_db("DELETE FROM `group_members` WHERE group_id = %s AND user_id = %s", (group_id, user_id), commit=True)
    log_action(user_id, 'LEAVE_GROUP', request.remote_addr, f"Group ID: {group_id}")
    return jsonify({'success': True})

@chat_bp.route('/chat/groups/<int:group_id>/delete', methods=['POST'])
@login_required
def delete_group(group_id):
    user_id = session['user_id']
    group = query_db("SELECT created_by_id FROM `groups` WHERE id = %s", (group_id,), one=True)
    membership = query_db("SELECT role FROM `group_members` WHERE group_id = %s AND user_id = %s", (group_id, user_id), one=True)
    
    is_admin = group and ((group['created_by_id'] == user_id) or (membership and membership.get('role') == 'admin'))
    if not is_admin:
        return jsonify({'success': False, 'error': 'Admin permission required'}), 403
        
    query_db("DELETE FROM `group_members` WHERE group_id = %s", (group_id,), commit=True)
    query_db("DELETE FROM `groups` WHERE id = %s", (group_id,), commit=True)
    log_action(user_id, 'DELETE_GROUP', request.remote_addr, f"Group ID: {group_id}")
    return jsonify({'success': True})

# ─── User Settings Endpoints ──────────────────────────────────────────

@chat_bp.route('/chat/settings/change-password', methods=['POST'])
@login_required
def change_password():
    user_id = session['user_id']
    data = request.get_json() or {}
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    
    if not old_password or not new_password:
        return jsonify({'success': False, 'error': 'All fields are required'}), 400
        
    if len(new_password) < 6:
        return jsonify({'success': False, 'error': 'New password must be at least 6 characters'}), 400
        
    user = query_db("SELECT password_hash FROM users WHERE user_id = %s", (user_id,), one=True)
    from werkzeug.security import check_password_hash, generate_password_hash
    if not user or not check_password_hash(user['password_hash'], old_password):
        return jsonify({'success': False, 'error': 'Current password is incorrect'}), 400
        
    new_hash = generate_password_hash(new_password)
    query_db("UPDATE users SET password_hash = %s WHERE user_id = %s", (new_hash, user_id), commit=True)
    log_action(user_id, 'CHANGE_PASSWORD', request.remote_addr, "User changed password")
    return jsonify({'success': True, 'message': 'Password changed successfully'})

@chat_bp.route('/chat/settings/update-security-question', methods=['POST'])
@login_required
def update_security_question():
    user_id = session['user_id']
    data = request.get_json() or {}
    question = data.get('question', '').strip()
    answer = data.get('answer', '').strip().lower()
    
    if not question or not answer:
        return jsonify({'success': False, 'error': 'Question and answer are required'}), 400
        
    import hashlib
    answer_hash = hashlib.sha256(answer.encode('utf-8')).hexdigest()
    
    existing = query_db("SELECT question_id FROM security_questions WHERE user_id = %s", (user_id,), one=True)
    if existing:
        query_db("UPDATE security_questions SET question = %s, answer_hash = %s WHERE user_id = %s", (question, answer_hash, user_id), commit=True)
    else:
        query_db("INSERT INTO security_questions (user_id, question, answer_hash) VALUES (%s, %s, %s)", (user_id, question, answer_hash), commit=True)
        
    log_action(user_id, 'UPDATE_SECURITY_QUESTION', request.remote_addr, "Updated security question")
    return jsonify({'success': True, 'message': 'Security question updated successfully'})

@chat_bp.route('/chat/settings/update-username', methods=['POST'])
@login_required
def update_username():
    user_id = session['user_id']
    data = request.get_json() or {}
    new_username = data.get('username', '').strip()
    
    if not new_username:
        return jsonify({'success': False, 'error': 'Username cannot be empty'}), 400
        
    if len(new_username) < 3:
        return jsonify({'success': False, 'error': 'Username must be at least 3 characters'}), 400
        
    existing = query_db("SELECT user_id FROM users WHERE (username = %s OR LOWER(username) = %s) AND user_id != %s", (new_username, new_username.lower(), user_id), one=True)
    if existing:
        return jsonify({'success': False, 'error': 'Username is already taken'}), 400
        
    query_db("UPDATE users SET username = %s WHERE user_id = %s", (new_username, user_id), commit=True)
    session['username'] = new_username
    log_action(user_id, 'UPDATE_USERNAME', request.remote_addr, f"Updated username to {new_username}")
    return jsonify({'success': True, 'username': new_username})

# ─── Pin/Unpin Message ───────────────────────────────────────────
@chat_bp.route('/chat/message/<int:message_id>/pin', methods=['POST'])
@login_required
def pin_message(message_id):
    user_id = session['user_id']
    msg = query_db("SELECT is_pinned FROM messages WHERE message_id = %s AND (sender_id = %s OR receiver_id = %s)", (message_id, user_id, user_id), one=True)
    if not msg:
        return jsonify({'success': False, 'error': 'Message not found'}), 404
        
    new_pinned = 0 if msg['is_pinned'] else 1
    query_db("UPDATE messages SET is_pinned = %s WHERE message_id = %s", (new_pinned, message_id), commit=True)
    return jsonify({'success': True, 'is_pinned': new_pinned})

# ─── Edit Message ────────────────────────────────────────────────
@chat_bp.route('/chat/message/<int:message_id>/edit', methods=['POST'])
@login_required
def edit_message(message_id):
    user_id = session['user_id']
    data = request.get_json() or {}
    new_content = data.get('content', '').strip()
    
    if not new_content:
        return jsonify({'success': False, 'error': 'Content cannot be empty'}), 400
        
    msg = query_db("SELECT sender_id, is_deleted FROM messages WHERE message_id = %s", (message_id,), one=True)
    if not msg or msg['sender_id'] != user_id or msg.get('is_deleted'):
        return jsonify({'success': False, 'error': 'Unauthorized or message deleted'}), 403
        
    threat_info = detect_threats(new_content)
    is_flagged = threat_info['is_flagged']
    threat_type = threat_info['threat_type']
    
    encrypted_new = encrypt_message(new_content)
    query_db(
        "UPDATE messages SET encrypted_content = %s, is_flagged = %s, threat_type = %s WHERE message_id = %s",
        (encrypted_new, is_flagged, threat_type, message_id), commit=True
    )
    
    log_action(user_id, 'EDIT_MESSAGE', request.remote_addr, f"Message ID: {message_id}")
    return jsonify({
        'success': True,
        'is_flagged': is_flagged,
        'threat_type': threat_type
    })

# ─── Calendar & Meetings Endpoints ─────────────────────────────────────

@chat_bp.route('/chat/meetings', methods=['GET'])
@login_required
def get_meetings():
    user_id = session['user_id']
    
    meetings = query_db("""
        SELECT DISTINCT m.*, u.username as organizer_name
        FROM meetings m
        JOIN users u ON m.organizer_id = u.user_id
        LEFT JOIN meeting_participants mp ON m.meeting_id = mp.meeting_id
        WHERE m.organizer_id = %s OR mp.user_id = %s
        ORDER BY m.start_time ASC
    """, (user_id, user_id))
    
    result = []
    for m in meetings:
        participants = query_db("""
            SELECT mp.user_id, u.username, mp.status
            FROM meeting_participants mp
            JOIN users u ON mp.user_id = u.user_id
            WHERE mp.meeting_id = %s
        """, (m['meeting_id'],))
        
        result.append({
            'meeting_id': m['meeting_id'],
            'title': m['title'],
            'organizer_id': m['organizer_id'],
            'organizer_name': m['organizer_name'],
            'meeting_type': m['meeting_type'],
            'location_or_link': m['meeting_link_or_location'],
            'start_time': m['start_time'].strftime('%Y-%m-%d %H:%M') if m['start_time'] else '',
            'end_time': m['end_time'].strftime('%Y-%m-%d %H:%M') if m['end_time'] else '',
            'description': m['description'] or '',
            'created_at': m['created_at'].strftime('%Y-%m-%d %H:%M') if m['created_at'] else '',
            'participants': list(participants),
            'is_organizer': (int(m['organizer_id']) == int(user_id))
        })
        
    return jsonify({'success': True, 'meetings': result})


@chat_bp.route('/chat/meetings/create', methods=['POST'])
@login_required
def create_meeting():
    user_id = session['user_id']
    data = request.get_json() or {}
    
    title = data.get('title', '').strip()
    meeting_type = data.get('meeting_type', 'google_meet')
    start_time_str = data.get('start_time', '').strip()
    end_time_str = data.get('end_time', '').strip()
    description = data.get('description', '').strip()
    custom_location = data.get('location', '').strip()
    participant_ids = data.get('participant_ids', [])
    send_chat_invite = data.get('send_chat_invite', True)
    target_chat_id = data.get('target_chat_id')
    
    if not title or not start_time_str or not end_time_str:
        return jsonify({'success': False, 'error': 'Title, Start Time, and End Time are required'}), 400
        
    if custom_location:
        meeting_link_or_location = custom_location
    elif meeting_type == 'google_meet':
        meeting_link_or_location = 'https://meet.google.com'
    elif meeting_type == 'teams':
        meeting_link_or_location = 'https://teams.microsoft.com'
    else:
        meeting_link_or_location = 'Physical Location'
        
    meeting_id = query_db("""
        INSERT INTO meetings (title, organizer_id, meeting_type, meeting_link_or_location, start_time, end_time, description)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (title, user_id, meeting_type, meeting_link_or_location, start_time_str, end_time_str, description), commit=True)
    
    query_db("INSERT INTO meeting_participants (meeting_id, user_id, status) VALUES (%s, %s, 'accepted')", (meeting_id, user_id), commit=True)
    
    type_badge = "📹 Google Meet" if meeting_type == "google_meet" else "🟦 MS Teams" if meeting_type == "teams" else "📍 Physical"
    chat_content = f"📅 MEETING INVITE: {title}\n[{type_badge}]\n🕒 {start_time_str} - {end_time_str}\n🔗 {meeting_link_or_location}\n📝 {description}"
    encrypted = encrypt_message(chat_content)

    for pid in participant_ids:
        try:
            pid_int = int(pid)
            if pid_int != user_id:
                query_db("INSERT INTO meeting_participants (meeting_id, user_id, status) VALUES (%s, %s, 'invited')", (meeting_id, pid_int), commit=True)
                # Auto-post encrypted meeting invite card to participant's direct chat thread
                msg_id = query_db(
                    "INSERT INTO messages (sender_id, receiver_id, encrypted_content, message_type, is_flagged, threat_type, message_id, is_read) VALUES (%s, %s, %s, 'text', 0, 'none', 0, 0)",
                    (user_id, pid_int, encrypted), commit=True
                )
                if msg_id:
                    query_db("UPDATE messages SET message_id = id WHERE id = %s", (msg_id,), commit=True)
        except Exception as e:
            print('Participant invite error:', e)

    log_action(user_id, 'CREATE_MEETING', request.remote_addr, f"Meeting ID: {meeting_id}, Title: {title}")
    
    return jsonify({
        'success': True,
        'meeting_id': meeting_id,
        'title': title,
        'meeting_link_or_location': meeting_link_or_location
    })


@chat_bp.route('/chat/meetings/unread-count')
@login_required
def unread_meetings_count():
    user_id = session['user_id']
    count = query_db("""
        SELECT COUNT(*) as count 
        FROM meeting_participants mp
        JOIN meetings m ON mp.meeting_id = m.meeting_id
        WHERE mp.user_id = %s AND mp.status = 'invited'
    """, (user_id,), one=True)['count']
    return jsonify({'success': True, 'count': count})


@chat_bp.route('/chat/meetings/<int:meeting_id>/delete', methods=['POST'])
@login_required
def delete_meeting(meeting_id):
    user_id = session['user_id']
    meeting = query_db("SELECT organizer_id FROM meetings WHERE meeting_id = %s", (meeting_id,), one=True)
    if not meeting:
        return jsonify({'success': False, 'error': 'Meeting not found'}), 404
        
    if int(meeting['organizer_id']) != int(user_id) and session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
    query_db("DELETE FROM meeting_participants WHERE meeting_id = %s", (meeting_id,), commit=True)
    query_db("DELETE FROM meetings WHERE meeting_id = %s", (meeting_id,), commit=True)
    log_action(user_id, 'DELETE_MEETING', request.remote_addr, f"Meeting ID: {meeting_id}")
    return jsonify({'success': True})


@chat_bp.route('/chat/meetings/<int:meeting_id>/update', methods=['POST'])
@login_required
def update_meeting(meeting_id):
    user_id = session['user_id']
    data = request.get_json() or {}
    
    meeting = query_db("SELECT organizer_id FROM meetings WHERE meeting_id = %s", (meeting_id,), one=True)
    if not meeting:
        return jsonify({'success': False, 'error': 'Meeting not found'}), 404
        
    if int(meeting['organizer_id']) != int(user_id) and session.get('role') != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403

    title = data.get('title', '').strip()
    meeting_type = data.get('meeting_type', 'google_meet')
    start_time_str = data.get('start_time', '').strip()
    end_time_str = data.get('end_time', '').strip()
    description = data.get('description', '').strip()
    custom_location = data.get('location', '').strip()
    participant_ids = data.get('participant_ids', [])
    
    if not title or not start_time_str or not end_time_str:
        return jsonify({'success': False, 'error': 'Title, Start Time, and End Time are required'}), 400

    if custom_location:
        meeting_link_or_location = custom_location
    elif meeting_type == 'google_meet':
        meeting_link_or_location = 'https://meet.google.com'
    elif meeting_type == 'teams':
        meeting_link_or_location = 'https://teams.microsoft.com'
    else:
        meeting_link_or_location = 'Physical Location'

    query_db("""
        UPDATE meetings 
        SET title = %s, meeting_type = %s, meeting_link_or_location = %s, start_time = %s, end_time = %s, description = %s
        WHERE meeting_id = %s
    """, (title, meeting_type, meeting_link_or_location, start_time_str, end_time_str, description, meeting_id), commit=True)

    query_db("DELETE FROM meeting_participants WHERE meeting_id = %s AND user_id != %s", (meeting_id, user_id), commit=True)
    for pid in participant_ids:
        try:
            pid_int = int(pid)
            if pid_int != user_id:
                query_db("INSERT INTO meeting_participants (meeting_id, user_id, status) VALUES (%s, %s, 'invited')", (meeting_id, pid_int), commit=True)
        except Exception:
            pass

    log_action(user_id, 'UPDATE_MEETING', request.remote_addr, f"Meeting ID: {meeting_id}, Title: {title}")
    return jsonify({'success': True})
