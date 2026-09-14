-- ============================================================
-- AI Secure Messaging - Database Setup Script
-- ============================================================

CREATE DATABASE IF NOT EXISTS ai_secure_messaging CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ai_secure_messaging;

-- ─── Users Table ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    user_id     INT AUTO_INCREMENT PRIMARY KEY,
    username    VARCHAR(50)  NOT NULL UNIQUE,
    email       VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role        ENUM('user', 'admin') NOT NULL DEFAULT 'user',
    status      ENUM('active', 'blocked') NOT NULL DEFAULT 'active',
    created_at  DATETIME DEFAULT NOW(),
    last_login  DATETIME NULL
);

-- ─── Security Questions Table ─────────────────────────────────────
CREATE TABLE IF NOT EXISTS security_questions (
    sq_id       INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL,
    question    VARCHAR(255) NOT NULL,
    answer_hash VARCHAR(255) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- ─── Messages Table ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS messages (
    message_id        INT AUTO_INCREMENT PRIMARY KEY,
    sender_id         INT NOT NULL,
    receiver_id       INT NOT NULL,
    encrypted_content TEXT NOT NULL,
    message_type      ENUM('text', 'file') NOT NULL DEFAULT 'text',
    is_flagged        TINYINT(1) NOT NULL DEFAULT 0,
    threat_type       VARCHAR(100) DEFAULT 'none',
    sent_at           DATETIME DEFAULT NOW(),
    FOREIGN KEY (sender_id)   REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- ─── Files Table ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS files (
    file_id     INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NOT NULL,
    message_id  INT NOT NULL,
    file_name   VARCHAR(255) NOT NULL,
    file_hash   VARCHAR(64)  NOT NULL,
    file_path   VARCHAR(500) NOT NULL,
    is_scanned  TINYINT(1) NOT NULL DEFAULT 0,
    scan_result VARCHAR(50) DEFAULT 'pending',
    uploaded_at DATETIME DEFAULT NOW(),
    FOREIGN KEY (user_id)    REFERENCES users(user_id)    ON DELETE CASCADE,
    FOREIGN KEY (message_id) REFERENCES messages(message_id) ON DELETE CASCADE
);

-- ─── Alerts Table ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS alerts (
    alert_id     INT AUTO_INCREMENT PRIMARY KEY,
    message_id   INT NOT NULL,
    user_id      INT NOT NULL,
    threat_type  VARCHAR(100) NOT NULL,
    alert_detail TEXT,
    severity     ENUM('low', 'medium', 'high') NOT NULL DEFAULT 'medium',
    status       ENUM('unread', 'read', 'resolved') NOT NULL DEFAULT 'unread',
    created_at   DATETIME DEFAULT NOW(),
    FOREIGN KEY (message_id) REFERENCES messages(message_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id)    REFERENCES users(user_id)       ON DELETE CASCADE
);

-- ─── Audit Logs Table ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id      INT AUTO_INCREMENT PRIMARY KEY,
    user_id     INT NULL,
    action      VARCHAR(100) NOT NULL,
    ip_address  VARCHAR(45),
    detail      TEXT,
    timestamp   DATETIME DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

-- ─── Default Admin Account ────────────────────────────────────────
-- Password: Admin@123  (bcrypt hashed)
-- Security Question: What is your secret code?  Answer: admin123
INSERT IGNORE INTO users (username, email, password_hash, role, status)
VALUES (
    'admin',
    'admin@aisecure.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMUkDFQO0sRjgA7Pj1mLzNfJuC',
    'admin',
    'active'
);

-- Insert security question for admin (answer_hash for 'admin123')
INSERT IGNORE INTO security_questions (user_id, question, answer_hash)
SELECT user_id, 'What is your secret code?', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMUkDFQO0sRjgA7Pj1mLzNfJuC'
FROM users WHERE username = 'admin';

SELECT 'Database setup complete!' AS status;
