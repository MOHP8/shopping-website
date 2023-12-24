from app import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    # User 模型的定義
    pass
