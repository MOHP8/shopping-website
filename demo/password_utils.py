import hashlib
import os

def generate_password_hash(password, salt_length=16):
    # 生成一個隨機的鹽值
    salt = os.urandom(salt_length)
    
    # 將鹽值添加到密碼中
    salted_password = password.encode() + salt
    
    # 使用SHA-256哈希算法計算哈希值
    password_hash = hashlib.sha256(salted_password).hexdigest()
    
    return password_hash, salt

def verify_password(password, stored_password_hash, salt):
    # 驗證密碼
    input_password_hash, _ = generate_password_hash(password, salt_length=len(salt))
    return input_password_hash == stored_password_hash
