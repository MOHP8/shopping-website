import os
from flask import current_app
from werkzeug.utils import secure_filename
import base64

# ˊ指定儲存資料夾（該執行檔的上上層）
UPLOAD_FOLDER_NAME = 'uploads'
UPLOAD_FOLDER = os.path.join("../.", UPLOAD_FOLDER_NAME)


ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_product_image(product_img, product_name):
    if product_img and allowed_file(product_img.filename):
        current_app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
        # 将图片保存到服务器
        product_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], product_name)
        os.makedirs(product_folder, exist_ok=True)
        img_jpeg = secure_filename(product_img.filename)
        product_path = os.path.join(product_folder, img_jpeg)
        product_img.save(product_path)
        # 读取图片的二进制数据
        with open(product_path, 'rb') as img_file:
            img_data = img_file.read()
        return img_data
    else:
        return None
    
def image_to_base64(img_data):
    return base64.b64encode(img_data).decode('utf-8')
