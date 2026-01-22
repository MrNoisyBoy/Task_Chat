import grpc
from proto.otp_pb2 import *
from proto.otp_pb2_grpc import OtpServicer
import pyotp

class OtpService(OtpServicer):
    def __init__(self, db):
        self.db = db
        self.cursor = self.db.cursor()

    def InitOtp(self, request: RequestInitOtp, context: grpc.ServicerContext):
        secret = pyotp.random_base32()
        self.cursor.execute("UPDATE users SET secret = ? WHERE login = ?",
                            (secret, request.login))
        self.db.commit()
        secret_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=f'{request.login}@fa.ru', issuer_name='FA_RU')
        return ResponseInitOtp(secret=secret_uri, error=None)

    def CheckOtp(self, request:RequestCheckOtp, context: grpc.ServicerContext):
        self.cursor.execute("SELECT secret FROM users WHERE login = ?", (request.login,))
        row = self.cursor.fetchone()
        if not row:
            return ResponseCheckOtp(valid=False, error="No such user")
        otp = pyotp.TOTP(row[0])
        otp_now = otp.now()
        if otp_now != request.otp:
            return ResponseCheckOtp(valid=False, error="Invalid otp")
        return ResponseCheckOtp(valid=True, error=None)

