import threading
from proto.auth_pb2 import *
from proto.auth_pb2_grpc import *
from proto.messaging_pb2 import *
from proto.messaging_pb2_grpc import *
from proto.otp_pb2 import *
from proto.otp_pb2_grpc import *
import qrcode

class ChatClient:
    def __init__(self, port=50051, host='127.0.0.1'):
        self._port = port
        self._host = host
        self._on_message_receive = None
        self._channel = grpc.insecure_channel(f'{self._host}:{self._port}')
        self._msgs_service = MessagingStub(self._channel)
        self._auth_service = AuthStub(self._channel)
        self._otp_service = OtpStub(self._channel)
        self._token = None

    def register(self, login, password):
        resp = self._auth_service.Register(RegisterRequest(login=login, password=password))
        if not resp.success:
            print(f'Ошибка регистрации: {resp.error}')
            return
        resp_otp = self._otp_service.InitOtp(RequestInitOtp(login=login))
        if resp_otp.error:
            print(f"Ошибка инициализации OTP: {resp_otp.error}")
            return
        if resp_otp.secret == "":
            print(f"Пустой секрет OTP")
            return
        img = qrcode.make(resp_otp.secret)
        img.save("./qr/my_secret.png")
    def auth(self, login, password):
        login_response = self._auth_service.Login(LoginRequest(login=login, password=password))
        if not login_response.success:
            print(f'Ошибка: {login_response.error}')
            return None

        self._token = login_response.token
        print(f'Успех! Токен: {login_response.token}')
        return login_response.token
    def start_listen_messages(self, message_received):
        self._on_message_receive = message_received
        threading.Thread(target=self._listen_for_messages, daemon=True).start()
    def _listen_for_messages(self):
        metadata = [('token', self._token)] if self._token else []
        try:
            for message in self._msgs_service.MessageStream(Empty(), metadata=metadata):
                if self._on_message_receive(message):
                    self._on_message_receive(message)
        except grpc.RpcError as e:
            print(f"Ошибка подключения: {e}")

    def send_message(self, username, text):
        metadata = [('token', self._token)] if self._token else []
        message = Message()
        message.author = username
        message.text = text
        try:
            self._msgs_service.SendMessage(message, metadata=metadata)
            print(f"Сообщение отправлено")
            return True

        except grpc.RpcError as e:
            print(f"Не удалось отправить сообщение: {e.details()}")
            return False

    def check_otp(self, login, otp):
        otp_response = self._otp_service.CheckOtp(RequestCheckOtp(login=login, otp=otp))
        if otp_response.error:
            print(f"Ошибка проверки OTP: {otp_response.error}")
            return None
        return otp_response.valid

    def close(self):
        self._channel.close()
