from flask import Flask, url_for, current_app
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
from config import Config

class SMTPManager:
    def __init__(self, app: Flask):
        self.mail = Mail(app)
        self.ts = URLSafeTimedSerializer(Config.SECRET_KEY)

    def send_email(self, to: str, subject: str, body: str, confirmation_route: str = None, **kwargs):
        msg = Message(subject, recipients=[to])

        # 需要寄驗證碼
        if confirmation_route:
            confirmation_url = self.build_confirmation_url(confirmation_route, **kwargs)
            msg.html = body + confirmation_url
        else:
            msg.html = body

        self.mail.send(msg)

    def build_confirmation_url(self, route: str, **kwargs):
        # 添加參數驗證邏輯
        try:
            # 構建 URL
            return url_for(route, _external=True, **kwargs)
        except Exception as e:
            #處理 URL 異常
            print(f"Error building confirmation URL: {e}")
            return ""
