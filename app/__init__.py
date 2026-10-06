import os
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO
from config import Config

bcrypt = Bcrypt()
socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Custom Jinja Filter for Malaysian Time (MYT UTC+8)
    @app.template_filter('myt')
    def format_myt(dt, fmt='%d/%m/%Y %H:%M'):
        if not dt:
            return '-'
        from datetime import datetime, timedelta
        if isinstance(dt, str):
            try:
                dt = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
            except Exception:
                return dt
        if hasattr(dt, 'strftime'):
            local_dt = dt + timedelta(hours=8)
            return local_dt.strftime(fmt)
        return str(dt)
    
    # Init extensions
    bcrypt.init_app(app)
    socketio.init_app(app, async_mode='eventlet', cors_allowed_origins='*')
    
    # Create upload folder
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Auto migrate database schema
    try:
        from app.utils.db import auto_migrate_database
        auto_migrate_database()
    except Exception:
        pass
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.chat import chat_bp
    from app.routes.admin import admin_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(admin_bp)
    
    # Register SocketIO events
    from app.sockets import register_socket_events
    register_socket_events(socketio)
    
    return app, socketio
