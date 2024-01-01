import logging
from flask import Flask, session, redirect ,url_for
from config import Config
from app.routes.main_bp import main_bp
from app.routes.auth_bp import auth_bp
from app.routes.shop import shop
from app.routes.shop_cart import shop_cart
from app.routes.order import order
from app.routes.profile import profile
from app.routes.google_verify import google_verify
from app.routes.facebook_verify import facebook_verify
from app.routes.twitter_verify import twitter_verify
from app.routes.ECPay import ec_pay_bp
# from app.routes.ECPaySDK import ec_pay_bp_sdk
from smtp import SMTPManager
from app.routes.socket_io import socket_io_bp, socketio
from app.routes.oauth import oauth

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config['SESSION_TYPE'] = 'filesystem'
    app.secret_key = app.config['SECRET_KEY']

    # 初始化 OAuth 提供者
    oauth.init_app(app)

    # 註冊藍圖
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(shop)
    app.register_blueprint(shop_cart)
    app.register_blueprint(order)
    app.register_blueprint(profile)
    app.register_blueprint(google_verify)
    app.register_blueprint(facebook_verify)
    app.register_blueprint(twitter_verify)
    app.register_blueprint(ec_pay_bp)
    
    # 設定 SocketIO
    socketio.init_app(app, cors_allowed_origins="*")  # 允許所有源
    

    # 初始化 SMTPManager 並將其添加到應用程序配置中
    smtp_manager = SMTPManager(app)
    
    app.config['SMTP_MANAGER'] = smtp_manager

    return app