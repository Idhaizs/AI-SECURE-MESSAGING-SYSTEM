from flask import session
from flask_socketio import emit, join_room, leave_room

def register_socket_events(socketio):

    @socketio.on('connect')
    def on_connect():
        user_id = session.get('user_id')
        role = session.get('role')
        if user_id:
            join_room(f'user_{user_id}')
            if role == 'admin':
                join_room('admin_room')
            emit('connected', {'user_id': user_id, 'role': role})

    @socketio.on('disconnect')
    def on_disconnect():
        user_id = session.get('user_id')
        role = session.get('role')
        if user_id:
            leave_room(f'user_{user_id}')
            if role == 'admin':
                leave_room('admin_room')

    @socketio.on('send_message')
    def on_send_message(data):
        receiver_id = data.get('receiver_id')
        message = data.get('message', {})
        
        # Emit to receiver's room
        emit('new_message', message, room=f'user_{receiver_id}')
        
        # Echo back to sender
        emit('message_sent', message)

    @socketio.on('typing')
    def on_typing(data):
        receiver_id = data.get('receiver_id')
        username = session.get('username')
        emit('user_typing', {'username': username}, room=f'user_{receiver_id}')

    @socketio.on('stop_typing')
    def on_stop_typing(data):
        receiver_id = data.get('receiver_id')
        emit('user_stop_typing', {}, room=f'user_{receiver_id}')
