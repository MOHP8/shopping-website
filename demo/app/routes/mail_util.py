from itsdangerous import URLSafeTimedSerializer
from flask import current_app

def generate_reset_token(user_info):
    ts = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    token = ts.dumps(user_info, salt='reset-password-salt')
    return token

def verify_reset_token(token):
    ts = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        user_email = ts.loads(token, salt='reset-password-salt', max_age=current_app.config['MAIL_TOKEN_EXPIRATION'])  # 1 hour expiration
        return user_email
    except:
        return None
