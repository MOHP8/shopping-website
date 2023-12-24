# google_verify.py
from flask import Blueprint, redirect, url_for, flash, request ,jsonify, session, render_template ,current_app,make_response
from flask_dance.contrib.google import make_google_blueprint, google
import json
import secrets
import requests
from database import Database
from oauthlib.oauth2.rfc6749.errors import InvalidClientIdError, TokenExpiredError
import oauthlib
import time
from config import Config

google_verify = Blueprint('google_verify', __name__)
database = Database()

login_source = 'google website'

# 生成一个安全的密鑰
secret_key = secrets.token_hex(24)
google_verify.secret_key = secret_key  # 替換為自己的密鑰

# # 讀取 JSON 文件
# with open('client_secret_565481039292-kfilnia3d2513brdmgakmhdrtp8os9j1.apps.googleusercontent.com.json', 'r') as json_file:
#     client_info = json.load(json_file)

# 將藍圖的設定與憑證一同配置
google_bp = make_google_blueprint(
    client_id= Config.GOOGLE_CLIENT_ID, # 您在 Google Cloud Console 中註冊應用程式時獲得的客戶端ID
    client_secret=Config.GOOGLE_CLIENT_SECRET, # 您在 Google Cloud Console 中註冊應用程式時所獲得的客戶端金鑰
    scope=['openid', 'https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/userinfo.email'],
    offline=True, #請求離線存取權限，允許存取使用者資料的同時取得刷新令牌
    reprompt_consent=False, #使用者同意時不重新提示
    reprompt_select_account=False, # 不重新提示使用者選擇帳戶
    redirect_to='google_verify.google_authorized',
    login_url='/google', # 當使用者需要登入時重新導向的 URL
    authorized_url='/google/authorized',
    session_class=None, # 保存使用者會話資訊的類，預設為 Flask 會話
    storage=None, # 用於儲存 OAuth 2.0 令牌的儲存對象，預設為 Flask-Dance 預設存儲
    hosted_domain=None, # 允許特定 Google 託管網域的使用者存取應用程序，如果不需要可以設定 None
    rule_kwargs=None # 提交給 Flask url_for 函數的關鍵字參數
)


# # 將藍圖附加到你的 Flask 應用程式
# google_verify.register_blueprint(google_bp)
google_verify.register_blueprint(google_bp, url_prefix="/login")


# 查詢用戶信息
def get_user_info(email):
    user_query = "SELECT MemberID,MemberName,Password FROM Members WHERE Email = %s AND Login_source =%s;"
    user_data = database.get_data(user_query ,(email, login_source))
    return user_data[0] if user_data else None

# # 新增一個路由來處理成功驗證後的頁面
@google_verify.route('/google/authorized')
def google_authorized():
    
    userinfo_response = google.get('/oauth2/v2/userinfo')
    # 檢查回應狀態碼
    if userinfo_response.status_code == 200:
        try:
            # 嘗試解析 JSON
            user_info = userinfo_response.json()
            print(user_info)
            user_id = user_info['id']
            user_name = user_info['name']
            user_email = user_info['email']
            # given_name = user_info['given_name']
            # family_name = user_info['family_name']
            # picture_url = user_info['picture']
            # locale = user_info['locale']


            # 查詢是否已存在具有相同電子郵件的記錄
            check_query = "SELECT Email FROM Members WHERE Email = %s AND Login_source =%s;"
            existing_email = database.get_data(check_query ,(user_email, login_source))

            if not existing_email:
                # 插入新記錄
                insert_query = "INSERT INTO Members (Login_user_id,MemberName, Email, RegistrationDate, ModificationDate, State, Login_source) VALUES (%s,%s,%s, NOW(), NOW(), '1',%s)"
                # print(insert_query)
                database.insert_data(insert_query ,(user_id ,user_name ,user_email ,login_source))
    
            # 從數據中換取用戶信息
            if user_email:
                user_info = get_user_info(user_email)
                if user_info:
                    session['user_info'] = {'MemberID': user_info[0], 'MemberName': user_info[1]}

        except requests.exceptions.JSONDecodeError:
            # 處理 JSON 解析錯誤
            print('JSON 解析錯誤：回應內容不是有效的 JSON 字串')
    else:
        # 處理伺服器回應錯誤
        error_message = f'錯誤：伺服器回應代碼 {userinfo_response.status_code}'
        print(error_message)
        flash(error_message, 'error')  # 使用 Flask 的 flash 記錄錯誤
        return render_template('login_authorized.html')

    # 如果還未驗證成功，返回正常的頁面
    return render_template('login_authorized.html')


@google_verify.route('/logout', methods=['GET'])
def logout():
    """
    This endpoint tries to revoke the token
    and then it clears the session
    """
    if google.authorized:
        try:
            google.get(
                'https://accounts.google.com/o/oauth2/revoke',
                params={
                    'token':
                        current_app.blueprints['google'].token['access_token']},
            )
        except TokenExpiredError:
            pass
        except InvalidClientIdError:
            # Our OAuth session apparently expired. We could renew the token
            # and logout again but that seems a bit silly, so for now fake
            # it.
            pass
    _empty_session()
    return redirect(url_for('auth.registration_successful'))


def _empty_session():
    """
    Deletes the google token and clears the session
    """
    if 'google' in current_app.blueprints and hasattr(current_app.blueprints['google'], 'token'):
        del current_app.blueprints['google'].token
    session.clear()


@google_verify.errorhandler(oauthlib.oauth2.rfc6749.errors.TokenExpiredError)
@google_verify.errorhandler(oauthlib.oauth2.rfc6749.errors.InvalidClientIdError)

def token_expired(_):
    _empty_session()
    return redirect(url_for('auth.registration_successful'))

@google_verify.route("/")
def index():

    if not google.authorized:
        return redirect(url_for("google.login"))

    user_info_url = 'https://openidconnect.googleapis.com/v1/userinfo'
    resp = google.get(user_info_url)
    user_info = resp.json()
    return "You are {user_name} on Google. Time: {t}".format(user_name=user_info['name'], t=time.time())


#-----------------------------------------


# JS 登入 google
@google_verify.route('/google_login', methods=['POST'])
def google_login():
    try:
        # 從前端請求中獲取 ID token 和用戶資訊
        data = request.json
        user_profile = data.get('userProfile')
        # 在這裡進行 ID token 的驗證，你可以使用 Google 提供的驗證方法，或其他相應的方法
        # 假設驗證成功，獲取用戶資訊
        user_id = user_profile.get('sub')
        user_email = user_profile.get('email')
        user_name = user_profile.get('name')

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

        # 返回成功的 JSON 響應
        return jsonify({'status': 'success', 'message': 'Login successful'})

    except Exception as e:
        # 返回錯誤的 JSON 響應
        return jsonify({'status': 'error', 'message': str(e)})