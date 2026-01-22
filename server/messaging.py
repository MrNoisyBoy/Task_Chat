import grpc
from time import sleep
import jwt
from datetime import datetime, timezone
from google.protobuf import timestamp_pb2
from proto.messaging_pb2 import *
from proto.messaging_pb2_grpc import MessagingServicer

JWT_SECRET = "your-secret-key-here12345"

class MessagingService(MessagingServicer):
    MESSAGE_STREAM_INTERVAL: 0.1

    def __init__(self):
        self._history = []

    def _validate_token(self, context):
        try:
            metadata = dict(context.invocation_metadata())
            token = metadata.get('token', '')

            if not token:
                context.abort(grpc.StatusCode.UNAUTHENTICATED, "Token required")
                return None

            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            return payload
        except Exception as e:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, f"Invalid token: {e}")
            return None

    def MessageStream(self, request, context: grpc.ServicerContext):
        user_info = self._validate_token(context)
        if not user_info:
            return
        last_read = len(self._history) - 1
        while context.is_active():
            while last_read < len(self._history) - 1:
                last_read += 1
                message = self._history[last_read]
                yield message
            sleep(0.1)

    def SendMessage(self, message: Message, context):
        server_time = timestamp_pb2.Timestamp()
        server_time.FromDatetime(datetime.now(timezone.utc))
        message.send_time.CopyFrom(server_time)

        time_str = server_time.ToDatetime().strftime('%H:%M:%S')
        print(f'[{time_str}] {message.author}: {message.text}')
        self._history.append(message)

        # ТОЛЬКО ДИАГНОСТИКА - потом удалим
        response = SendResponse()
        print("=== ДИАГНОСТИКА SendResponse ===")
        print("Все атрибуты:", [attr for attr in dir(response) if not attr.startswith('_')])
        print("Тип response:", type(response))

        return SendResponse()