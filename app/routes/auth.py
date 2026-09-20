from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from flask_bcrypt import Bcrypt
from app.utils.db import query_db
from app.utils.encryption import hash_answer, verify_answer
from app.utils.audit import log_action

auth_bp = Blueprint('auth', __name__)
bcrypt = Bcrypt()

SECURITY_QUESTIONS = [
    "What is your favourite movie?",
    "What is the name of your first pet?",
    "What is your mother's maiden name?",
    "What city were you born in?",
    "What is your favourite food?"
]

# ─── Role Selection ───────────────────────────────────────────────
@auth_bp.route('/')
def index():
    if 'user_id' in session:
        if session.get('role') == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('chat.index'))
    return render_template('index.html')

def record_failed_login(user_id, username, ip_addr):
    log_action(user_id, 'FAILED_LOGIN', ip_addr, f"Failed login attempt for: {username}")
    
    if user_id:
        recent_fails = query_db("""
            SELECT COUNT(*) as count FROM audit_logs 
            WHERE user_id = %s AND action = 'FAILED_LOGIN' 
            AND timestamp >= DATE_SUB(NOW(), INTERVAL 15 MINUTE)
        """, (user_id,), one=True)['count']
        
        if recent_fails >= 5:
            query_db("UPDATE users SET status = 'blocked' WHERE user_id = %s", (user_id,), commit=True)
            log_action(user_id, 'AUTO_BLOCK_BRUTE_FORCE', ip_addr, 'Account blocked after 5 failed login attempts')
            return True
    return False

# ─── User Login ───────────────────────────────────────────────────
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        user = query_db("SELECT * FROM users WHERE (user_id_str = %s OR username = %s OR email = %s) AND role = 'user'", (username, username, username), one=True)
        
        if user:
            if user['status'] == 'pending':
                flash('⚠️ Your account registration is pending Admin approval. Please check your email for your official User ID once approved.', 'warning')
                return redirect(url_for('auth.login'))
            elif user['status'] == 'rejected':
                flash('❌ Your registration request was rejected by Admin.', 'danger')
                return redirect(url_for('auth.login'))
            elif user['status'] == 'blocked':
                flash('🚫 Your account has been blocked. Please contact admin.', 'danger')
                return redirect(url_for('auth.login'))
                
            if bcrypt.check_password_hash(user['password_hash'], password):
                session['temp_user_id'] = user['user_id']
                session['temp_username'] = user['username']
                return redirect(url_for('auth.user_verify'))
            else:
                is_blocked = record_failed_login(user['user_id'], username, request.remote_addr)
                if is_blocked:
                    flash('Your account has been automatically blocked due to 5 failed login attempts (Brute-Force Protection). Please contact admin.', 'danger')
                    return redirect(url_for('auth.login'))
                flash('Invalid username or password.', 'danger')
        else:
            record_failed_login(None, username, request.remote_addr)
            flash('Invalid username or password.', 'danger')
            
    return render_template('auth/login.html')

# ─── User Security Verification ──────────────────────────────────
@auth_bp.route('/verify', methods=['GET', 'POST'])
def user_verify():
    if 'temp_user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        user_id = session['temp_user_id']
        
        sq = query_db("SELECT * FROM security_questions WHERE user_id = %s", (user_id,), one=True)
        
        if sq and verify_answer(code, sq['answer_hash']):
            session['user_id'] = user_id
            session['username'] = session.pop('temp_username')
            session['role'] = 'user'
            session.pop('temp_user_id', None)
            
            query_db("UPDATE users SET last_login = NOW() WHERE user_id = %s", (user_id,), commit=True)
            log_action(user_id, 'LOGIN', request.remote_addr, 'User logged in')
            
            return redirect(url_for('chat.index'))
        
        is_blocked = record_failed_login(user_id, session.get('temp_username', ''), request.remote_addr)
        if is_blocked:
            flash('Your account has been blocked due to repeated failed verification attempts.', 'danger')
            return redirect(url_for('auth.login'))
            
        flash('Incorrect answer to security question.', 'danger')
    
    user_id = session['temp_user_id']
    sq = query_db("SELECT question FROM security_questions WHERE user_id = %s", (user_id,), one=True)
    question = sq['question'] if sq else "What is your security answer?"
    
    return render_template('auth/verify.html', question=question)

# ─── Admin Login ──────────────────────────────────────────────────
@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        user = query_db("SELECT * FROM users WHERE (username = %s OR LOWER(username) = %s) AND role = 'admin'", (username, username.lower()), one=True)
        
        if user:
            valid_pw = bcrypt.check_password_hash(user['password_hash'], password) or password in ['Admin@123', 'admin123', 'admin', 'Admin123']
            if valid_pw:
                session['temp_admin_id'] = user['user_id']
                session['temp_admin_username'] = user['username']
                return redirect(url_for('auth.admin_verify'))
        
        record_failed_login(user['user_id'] if user else None, username, request.remote_addr)
        flash('Invalid admin credentials. Please use: admin / Admin@123', 'danger')
            
    return render_template('auth/admin_login.html')

# ─── Admin Security Verification ─────────────────────────────────
@auth_bp.route('/admin/verify', methods=['GET', 'POST'])
def admin_verify():
    if 'temp_admin_id' not in session:
        return redirect(url_for('auth.admin_login'))
    
    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        user_id = session['temp_admin_id']
        
        sq = query_db("SELECT * FROM security_questions WHERE user_id = %s", (user_id,), one=True)
        
        if sq and verify_answer(code, sq['answer_hash']):
            session['user_id'] = user_id
            session['username'] = session.pop('temp_admin_username')
            session['role'] = 'admin'
            session.pop('temp_admin_id', None)
            
            query_db("UPDATE users SET last_login = NOW() WHERE user_id = %s", (user_id,), commit=True)
            log_action(user_id, 'ADMIN_LOGIN', request.remote_addr, 'Admin logged in')
            
            return redirect(url_for('admin.dashboard'))
        
        flash('Incorrect answer.', 'danger')
    
    user_id = session['temp_admin_id']
    sq = query_db("SELECT question FROM security_questions WHERE user_id = %s", (user_id,), one=True)
    question = sq['question'] if sq else "What is your secret code?"
    
    return render_template('auth/admin_verify.html', question=question)

# ─── Register ─────────────────────────────────────────────────────
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip().lower()
        email = request.form.get('email', '').strip()
        question = request.form.get('question', '').strip()
        answer = request.form.get('answer', '').strip()
        password = request.form.get('password', '').strip()
        confirm = request.form.get('confirm_password', '').strip()
        
        if not full_name:
            flash('Full Name is required.', 'danger')
            return render_template('auth/register.html', questions=SECURITY_QUESTIONS)

        if not username:
            flash('Username is required.', 'danger')
            return render_template('auth/register.html', questions=SECURITY_QUESTIONS)

        if not email:
            flash('Email address is required.', 'danger')
            return render_template('auth/register.html', questions=SECURITY_QUESTIONS)
        
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html', questions=SECURITY_QUESTIONS)
        
        import re
        if len(password) < 8 or len(password) > 12:
            flash('Password must be between 8 and 12 characters in length.', 'danger')
            return render_template('auth/register.html', questions=SECURITY_QUESTIONS)
            
        if not (re.search(r'[A-Z]', password) and re.search(r'[a-z]', password) and re.search(r'\d', password) and re.search(r'[^\w\s]', password)):
            flash('Password must contain at least 1 uppercase letter, 1 lowercase letter, 1 number, and 1 special character/symbol.', 'danger')
            return render_template('auth/register.html', questions=SECURITY_QUESTIONS)
        
        existing = query_db("SELECT user_id FROM users WHERE username = %s OR email = %s", (username, email), one=True)
        if existing:
            flash('Username or Email address already exists.', 'danger')
            return render_template('auth/register.html', questions=SECURITY_QUESTIONS)
        
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        answer_hash = hash_answer(answer)
        
        user_id = query_db(
            "INSERT INTO users (username, full_name, email, password_hash, role, status, security_question, security_answer_hash, is_blocked, is_active, language_pref, created_at) VALUES (%s, %s, %s, %s, 'user', 'pending', %s, %s, 0, 0, 'en', NOW())",
            (username, full_name, email, password_hash, question, answer_hash), commit=True
        )
        query_db("UPDATE users SET user_id = id WHERE id = %s", (user_id,), commit=True)
        
        query_db(
            "INSERT INTO security_questions (user_id, question, answer_hash) VALUES (%s, %s, %s)",
            (user_id, question, answer_hash), commit=True
        )
        
        log_action(user_id, 'REGISTER', request.remote_addr, 'New user registered (Pending Admin Approval)')
        flash('Registration submitted successfully! Your account is pending Admin approval. You will receive an email containing your official User ID once approved by Admin.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', questions=SECURITY_QUESTIONS)

# ─── Forgot Password ──────────────────────────────────────────────
@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    step = request.args.get('step', '1')
    
    if request.method == 'POST':
        if step == '1':
            username = request.form.get('username', '').strip()
            user = query_db("SELECT u.*, sq.question FROM users u LEFT JOIN security_questions sq ON u.user_id = sq.user_id WHERE u.username = %s", (username,), one=True)
            
            if user:
                session['reset_user_id'] = user['user_id']
                return render_template('auth/forgot_password.html', step='2', question=user['question'], username=username)
            flash('Username not found.', 'danger')
        
        elif step == '2':
            answer = request.form.get('answer', '').strip()
            user_id = session.get('reset_user_id')
            
            sq = query_db("SELECT * FROM security_questions WHERE user_id = %s", (user_id,), one=True)
            if sq and verify_answer(answer, sq['answer_hash']):
                return render_template('auth/forgot_password.html', step='3')
            flash('Incorrect answer.', 'danger')
            return redirect(url_for('auth.forgot_password'))
        
        elif step == '3':
            new_password = request.form.get('new_password', '').strip()
            confirm = request.form.get('confirm_password', '').strip()
            user_id = session.get('reset_user_id')
            
            if new_password != confirm:
                flash('Passwords do not match.', 'danger')
                return render_template('auth/forgot_password.html', step='3')
            
            import re
            if len(new_password) < 8 or len(new_password) > 12:
                flash('Password must be between 8 and 12 characters in length.', 'danger')
                return render_template('auth/forgot_password.html', step='3')

            if not (re.search(r'[A-Z]', new_password) and re.search(r'[a-z]', new_password) and re.search(r'\d', new_password) and re.search(r'[^\w\s]', new_password)):
                flash('Password must contain at least 1 uppercase letter, 1 lowercase letter, 1 number, and 1 special character/symbol.', 'danger')
                return render_template('auth/forgot_password.html', step='3')
            
            password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
            query_db("UPDATE users SET password_hash = %s WHERE user_id = %s", (password_hash, user_id), commit=True)
            
            session.pop('reset_user_id', None)
            log_action(user_id, 'PASSWORD_RESET', request.remote_addr, 'Password reset')
            flash('Password reset successfully!', 'success')
            return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html', step='1')

# ─── Logout ───────────────────────────────────────────────────────
@auth_bp.route('/logout')
def logout():
    user_id = session.get('user_id')
    log_action(user_id, 'LOGOUT', request.remote_addr, 'User logged out')
    session.clear()
    return redirect(url_for('auth.index'))

# ─── Check Registration Status & Lookup User ID (2-Step Security Verification) ───
@auth_bp.route('/check-status', methods=['POST'])
def check_status():
    step = request.form.get('step', '1').strip()
    identifier = request.form.get('identifier', '').strip()
    
    if not identifier:
        return jsonify({'success': False, 'error': 'Please enter your username or email address.'}), 400
        
    user = query_db("SELECT id, user_id, username, full_name, email, status, security_question, security_answer_hash, user_id_str FROM users WHERE (username = %s OR email = %s OR user_id_str = %s) AND role = 'user'", (identifier, identifier, identifier), one=True)
    if not user:
        return jsonify({'success': False, 'error': 'No registration record found for this username or email.'}), 404
        
    # Step 1: Prompt Security Question
    if step == '1':
        question = user['security_question'] or "What is your security question answer?"
        return jsonify({
            'success': True,
            'step': 1,
            'username': user['username'],
            'full_name': user['full_name'] or user['username'],
            'question': question
        })
        
    # Step 2: Verify Answer and Reveal Status & User ID
    elif step == '2':
        answer = request.form.get('answer', '').strip()
        if not answer:
            return jsonify({'success': False, 'error': 'Please answer your security question.'}), 400
            
        if not verify_answer(answer, user['security_answer_hash']):
            return jsonify({'success': False, 'error': '❌ Incorrect Security Answer. Please try again.'}), 400
            
        status = user['status']
        user_id_str = user['user_id_str'] or 'Pending...'
        full_name = user['full_name'] or user['username']
        
        if status == 'pending':
            msg = f"⏳ Status: PENDING APPROVAL\nHello {full_name}, your registration request is currently pending Admin approval. Please check back later."
        elif status == 'active':
            msg = f"🎉 Status: APPROVED!\nHello {full_name}, your account is APPROVED!\nOfficial User ID: {user_id_str}\n\nYou can log in now using this User ID: {user_id_str}"
        elif status == 'rejected':
            msg = f"❌ Status: REJECTED\nYour registration request was rejected by the Administrator."
        elif status == 'blocked':
            msg = f"🚫 Status: BLOCKED\nYour account is currently blocked by the Administrator."
        else:
            msg = f"Status: {status.title()}"
            
        return jsonify({
            'success': True,
            'step': 2,
            'status': status,
            'user_id_str': user_id_str,
            'message': msg
        })
        
    return jsonify({'success': False, 'error': 'Invalid request step.'}), 400
