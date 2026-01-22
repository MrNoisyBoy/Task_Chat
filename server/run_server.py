import grpc
from concurrent import futures
import sqlite3
from proto.auth_pb2_grpc import add_AuthServicer_to_server
from proto.messaging_pb2_grpc import add_MessagingServicer_to_server
from proto.otp_pb2_grpc import add_OtpServicer_to_server


from auth import AuthService
from messaging import MessagingService
from otp import OtpService

def serve():
    conn = sqlite3.connect('users.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users  
    (id INTEGER PRIMARY KEY, login TEXT UNIQUE, password_hash TEXT, secret TEXT)''')
    conn.commit()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_AuthServicer_to_server(AuthService(conn), server)
    add_MessagingServicer_to_server(MessagingService(), server)
    add_OtpServicer_to_server(OtpService(conn), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print('Server started on port 50051')
    server.wait_for_termination()
if __name__ == '__main__':
    serve()