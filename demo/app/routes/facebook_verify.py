# facebook_verify.py
from flask import Blueprint, request, redirect, url_for, session
from database import Database

facebook_verify = Blueprint('facebook_verify', __name__)
database = Database()

login_source = 'facebook website'

# 查詢用戶信息
def get_user_info(email):
    user_query = "SELECT MemberID,MemberName,Password FROM Members WHERE Email = %s AND Login_source =%s;"
    user_data = database.get_data(user_query ,(email, login_source))
    return user_data[0] if user_data else None

# 新增一個路由來處理成功驗證後的頁面
@facebook_verify.route('/facebook/authorized', methods=['POST'])
def facebook_authorized():
    # 從 POST 請求中取得 JSON 數據
    data = request.get_json()

    # 提取使用者資訊
    user_id = data.get('userId')
    user_name = data.get('userName')
    user_email = data.get('userEmail')

    # 查詢是否已存在具有相同電子郵件的記錄
    check_query = "SELECT Email FROM Members WHERE Email = %s AND Login_source = %s;"
    existing_email = database.get_data(check_query, (user_email, login_source))

    if not existing_email:
        # 插入新記錄
        insert_query = "INSERT INTO Members (Login_user_id,MemberName, Email, RegistrationDate, ModificationDate, State, Login_source) VALUES (%s,%s,%s, NOW(), NOW(), '1',%s)"
        database.insert_data(insert_query, (user_id, user_name, user_email, login_source))

    # 從數據中換取用戶信息
    if user_email:
        user_info = get_user_info(user_email)
        if user_info:
            session['user_info'] = {'MemberID': user_info[0], 'MemberName': user_info[1]}

    return redirect(url_for('main.home'))
