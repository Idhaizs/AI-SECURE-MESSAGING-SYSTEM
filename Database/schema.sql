-- ============================================
-- AI Secure Messaging System - Database Schema
-- Database: MariaDB
-- ============================================

CREATE DATABASE IF NOT EXISTS ai_secure_messaging;
USE ai_secure_messaging;

-- ============================================
-- TABLE 1: USERS
-- ============================================
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('admin', 'user') NOT NULL DEFAULT 'user',
    status ENUM('active', 'blocked') NOT NULL DEFAULT 'active',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login DATETIME DEFAULT NULL
);

-- ============================================
-- TABLE 2: SECURITY_QUESTIONS
-- ============================================
CREATE TABLE security_questions (
    question_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    question VARCHAR(255) NOT NULL,
    answer_hash VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- ============================================
-- TABLE 3: MESSAGES
-- ============================================
CREATE TABLE messages (
    message_id INT AUTO_INCREMENT PRIMARY KEY,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    encrypted_content TEXT NOT NULL,
    message_type ENUM('text', 'file') NOT NULL DEFAULT 'text',
    is_flagged BOOLEAN DEFAULT FALSE,
    threat_type ENUM('none', 'phishing', 'malicious_link', 'suspicious_attachment', 'spam') DEFAULT 'none',
    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sender_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- ============================================
-- TABLE 4: FILES
-- ============================================
CREATE TABLE files (
    file_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    message_id INT DEFAULT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_hash VARCHAR(64) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT DEFAULT 0,
    file_type VARCHAR(50) DEFAULT NULL,
    is_scanned BOOLEAN DEFAULT FALSE,
    scan_result ENUM('pending', 'clean', 'malicious', 'suspicious') DEFAULT 'pending',
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (message_id) REFERENCES messages(message_id) ON DELETE SET NULL
);

-- ============================================
-- TABLE 5: ALERTS
-- ============================================
CREATE TABLE alerts (
    alert_id INT AUTO_INCREMENT PRIMARY KEY,
    message_id INT DEFAULT NULL,
    user_id INT NOT NULL,
    threat_type VARCHAR(100) NOT NULL,
    alert_detail TEXT DEFAULT NULL,
    severity ENUM('low', 'medium', 'high') NOT NULL DEFAULT 'medium',
    status ENUM('unread', 'read', 'resolved') NOT NULL DEFAULT 'unread',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (message_id) REFERENCES messages(message_id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- ============================================
-- TABLE 6: AUDIT_LOGS
-- ============================================
CREATE TABLE audit_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT DEFAULT NULL,
    action VARCHAR(100) NOT NULL,
    ip_address VARCHAR(45) DEFAULT NULL,
    detail TEXT DEFAULT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
);

-- ============================================
-- DEFAULT ADMIN ACCOUNT
-- password: Admin@123 (bcrypt hashed)
-- ============================================
INSERT INTO users (username, email, password_hash, role, status)
VALUES (
    'admin',
    'admin@aisecuremsg.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBpj2FKFg0lXey',
    'admin',
    'active'
);
