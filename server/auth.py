import grpc
import sqlite3
import jwt
import datetime
from hashlib import sha256
from proto.auth_pb2 import *
from proto.auth_pb2_grpc import AuthServicer

JWT_SECRET = "your-secret-key-here12345"

class AuthService(AuthServicer):
    def __init__(self, db):
        self.db = db
        self.cursor = self.db.cursor()
    def Register(self, request, context: grpc.ServicerContext):
        try:
            hashed_password = sha256(request.password.encode()).hexdigest()
            self.cursor.execute('INSERT INTO users (login,password_hash) VALUES (?, ?)', (request.login, hashed_password))
            self.db.commit()
            return RegisterResponse(success=True)
        except sqlite3.IntegrityError:
            return RegisterResponse(success=False,  error='Login already exists')
    def Login(self, request, context: grpc.ServicerContext):
        try:
            self.cursor.execute('SELECT id, password_hash FROM users WHERE login = ?', (request.login,))
            row = self.cursor.fetchone()

            if not row:
                return LoginResponse(success=False, error='User not found')

            user_id, stored_hash = row

            input_password_hash = sha256(request.password.encode()).hexdigest()

            if stored_hash != input_password_hash:
                return LoginResponse(success=False, error='Invalid password')

            token_payload = {
                'user_id': user_id,
                'login': request.login,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }

            token = jwt.encode(token_payload, JWT_SECRET, algorithm='HS256')

            return LoginResponse(success=True, token=token)

        except Exception as e:
            return LoginResponse(success=False, error=str(e))
