from flask import Blueprint, redirect, url_for, session ,render_template
from app.routes.oauth import oauth
from database import Database
from authlib.integrations.base_client.errors import OAuthError

twitter_verify = Blueprint('twitter_verify', __name__)
database = Database()

login_source = 'twitter website'

# 輔助函數從數據庫中獲取用戶信息
def get_user_info(email):
    user_query = "SELECT MemberID, MemberName, Password FROM Members WHERE Email = %s AND Login_source = %s;"
    user_data = database.get_data(user_query, (email, login_source))
    return user_data[0] if user_data else None

# 路由以啟動 Twitter OAuth
@twitter_verify.route('/twitter/login')
def twitter_login():
    try:
        return oauth.twitter.authorize_redirect(url_for('twitter_verify.twitter_authorized', _external=True))
    except OAuthError as e:
        # 重定向到自定義錯誤頁面
        return redirect(url_for('twitter_verify.custom_error'))
    
# 路由處理成功的授權
@twitter_verify.route('/twitter/authorized')
def twitter_authorized():
    try:
        # 從 Twitter 獲取 OAuth 響應
        response = oauth.twitter.authorize_access_token()
        # print(response)

        # 使用獲取的訪問令牌從 Twitter 獲取用戶信息
        # user_info = oauth.twitter.get('account/verify_credentials.json', token=(response['oauth_token'], response['oauth_token_secret']))
        # 使用獲取的訪問令牌從 Twitter 獲取用戶信息
        user_info = oauth.twitter.get('https://api.twitter.com/1.1/account/verify_credentials.json?include_email=true')

        # 提取用戶信息
        user_id = user_info.json().get('id_str')
        user_name = user_info.json().get('name')
        user_email = user_info.json().get('email')  # 嘗試獲取電子郵件地址
        # print(user_id)
        # print(user_name)
        # print(user_email)

        # 檢查是否在數據庫中存在具有相同電子郵件的用戶
        check_query = "SELECT Email FROM Members WHERE Email = %s AND Login_source = %s;"
        existing_email = database.get_data(check_query, (user_email, login_source))

        if not existing_email:
            # 在數據庫中插入一條新記錄
            insert_query = "INSERT INTO Members (Login_user_id, MemberName, Email, RegistrationDate, ModificationDate, State, Login_source) VALUES (%s, %s, %s, NOW(), NOW(), '1', %s)"
            database.insert_data(insert_query, (user_id, user_name, user_email, login_source))

        # 從數據庫中獲取用戶信息
        if user_email:
            user_info_db = get_user_info(user_email)
            if user_info_db:
                session['user_info'] = {'MemberID': user_info_db[0], 'MemberName': user_info_db[1]}
    
    except OAuthError as e:
        # 在控制台打印錯誤信息以進行調試
        print(f"OAuth error occurred: {e}")
        # 在這裡可以將錯誤信息傳遞給錯誤頁面，例如：
        return render_template('error.html', error_message='OAuth 錯誤發生了。請稍後再試。')

    except Exception as e:
        # 在控制台打印錯誤信息以進行調試
        print(f"An error occurred: {e}")
    
    return render_template('login_authorized.html')
    
# 新增自定義錯誤頁面的路由
@twitter_verify.route('/twitter/custom_error')
def custom_error():
    return render_template('error.html', error_message='OAuth 錯誤發生了。請稍後再試。')