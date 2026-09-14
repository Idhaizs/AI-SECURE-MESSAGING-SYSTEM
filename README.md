# AI Secure Messaging System
### Final Year Project - Bachelor of Information Technology (Honours) in Cyber Security
### University Poly-Tech Malaysia (UPTM)
### Client: Salwa, Fairuz & Co.

---

## Setup Instructions

### 1. Prerequisites
- Python 3.10+
- MariaDB / XAMPP
- pip

### 2. Clone / Download Project
```
ai_secure_messaging/
├── app/
│   ├── __init__.py
│   ├── sockets.py
│   ├── routes/
│   │   ├── auth.py
│   │   ├── chat.py
│   │   └── admin.py
│   ├── utils/
│   │   ├── db.py
│   │   ├── encryption.py
│   │   ├── ai_detection.py
│   │   └── audit.py
│   ├── templates/
│   └── static/
├── config.py
├── run.py
├── requirements.txt
├── .env
└── schema.sql
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup Database
1. Start XAMPP / MariaDB
2. Open phpMyAdmin
3. Import `schema.sql`

### 5. Configure Environment
Edit `.env` file:
```
SECRET_KEY=your-secret-key
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=
DB_NAME=ai_secure_messaging
ENCRYPTION_KEY=  # Generate: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
GEMINI_API_KEY=your-gemini-api-key
VIRUSTOTAL_API_KEY=your-virustotal-api-key
```

### 6. Generate Encryption Key
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
Copy output to `ENCRYPTION_KEY` in `.env`

### 7. Run Application
```bash
python run.py
```

Open browser: `http://localhost:5000`

---

## Default Admin Account
- **Username:** admin
- **Password:** Admin@123
- **Security Answer:** (Set your own after first login)

---

## Tech Stack
| Component | Technology |
|-----------|-----------|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python Flask |
| Database | MariaDB |
| Real-time | Flask-SocketIO |
| Encryption | AES-256 (Fernet) |
| AI Detection | Gemini API, Scikit-learn, NLTK |
| File Scanning | VirusTotal API (SHA-256 Hash) |

---

## Features
- ✅ Secure encrypted real-time messaging
- ✅ Encrypted file sharing
- ✅ AI phishing & spam detection
- ✅ VirusTotal file scanning
- ✅ Role-based access (Admin & User)
- ✅ Security question verification
- ✅ Admin dashboard & reports
- ✅ Real-time alerts
- ✅ Audit logging
- ✅ CIA Triad implementation
