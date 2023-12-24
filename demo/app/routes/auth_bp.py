from flask import Blueprint, render_template, request, redirect, url_for, flash, session ,current_app
from database import Database
from werkzeug.security import generate_password_hash ,check_password_hash
from functools import wraps
from app.routes.mail_util import generate_reset_token ,verify_reset_token  #生成令牌的函數
import requests

auth_bp = Blueprint('auth', __name__)
database = Database()
login_source = 'main website'

# 登入會員才能進到會員後台
def login_required(route_func):
    @wraps(route_func)
    def decorated_route(*args, **kwargs):
        if 'user_info' in session:
            return route_func(*args, **kwargs)
        else:
            return redirect(url_for('auth.login'))
    return decorated_route

# 註冊過直接導向首頁 
def login_home(route_func):
    @wraps(route_func)
    def decorated_route(*args, **kwargs):
        # print(session)
        if 'user_info' in session:
            return redirect(url_for('main.home'))
        else:
            return route_func(*args, **kwargs)
    return decorated_route

# 查詢用戶信息
def get_user_info(email):
    user_query = "SELECT MemberID,MemberName,Password FROM Members WHERE Email = %s AND Login_source = %s;"
    user_data = database.get_data(user_query, (email, login_source))
    return user_data[0] if user_data else None

def verify_recaptcha_v2(response):
    # 在這裡執行 reCAPTCHA 驗證
    secret_key = current_app.config['SECRET_KEY_V2']
    verification_url = f"https://www.google.com/recaptcha/api/siteverify?secret={secret_key}&response={response}"

    response = requests.get(verification_url)
    data = response.json()

    return data['success']

def verify_recaptcha_v3(token):
    # 在這裡執行 reCAPTCHA v3 驗證
    secret_key = current_app.config['SECRET_KEY_V3']
    verification_url = 'https://www.google.com/recaptcha/api/siteverify'
    payload = {
        'secret': secret_key,
        'response': token,
    }

    response = requests.post(verification_url, data=payload)
    data = response.json()

    return data['success']

@auth_bp.route('/login', methods=['GET', 'POST'])
@login_home
def login():
    # Google組件 客戶ID
    # client_id = ''

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # 檢查 reCAPTCHA v2 驗證結果
        recaptcha_response = request.form['g-recaptcha-response']
        is_recaptcha_valid = verify_recaptcha_v2(recaptcha_response)

        if not is_recaptcha_valid:
            flash('reCAPTCHA v2 驗證失敗', 'error')
            return render_template('login.html')

        # 檢查 reCAPTCHA v3 驗證結果
        recaptcha_token = request.form['recaptcha_token']
        is_recaptcha_valid = verify_recaptcha_v3(recaptcha_token)

        if not is_recaptcha_valid:
            flash('reCAPTCHA v3 驗證失敗', 'error')
            return render_template('login.html')
        
        # print(email)
        # 查詢用戶是否存在
        user_info = get_user_info(email)
        # print(user_info)
        if user_info:
            stored_password_hash = user_info[2]
            password_match = check_password_hash(stored_password_hash, password)
            
            # 使用 check_password_hash 檢查密碼是否匹配
            if password_match:
                # 記錄使用者訊息
                user_info = {'MemberID': user_info[0], 'MemberName': user_info[1]}
                session['user_info'] = user_info  # 將用戶信息儲存到會話中

                return redirect(url_for('main.home'))
            else:
                flash('登入失敗，用戶名或密碼不正確', 'error')
        else:
            flash('登入失敗，該信箱還未申請用戶', 'error')
                
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
@login_home
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # 檢查密碼是否匹配
        if password != confirm_password:
            flash('密碼和確認密碼不一致', 'error')
            
            # 儲存原始數據以便重新填充表單
            session['original_data'] = {
                'username': username,
                'email': email,
            }
            return redirect(url_for('auth.register'))
        
        # 查詢是否已存在具有相同電子郵件的記錄
        user_info = get_user_info(email)
        if user_info:
            flash('此電子郵件已註冊', 'error')
            session.pop('original_data', None)
            return redirect(url_for('auth.register'))

        session.pop('original_data', None)
        
        password = generate_password_hash(password)

        session['user_email'] = email

        # 插入新記錄
        insert_query = "INSERT INTO Members (MemberName, Email, Password, RegistrationDate, ModificationDate, State, Login_source) VALUES (%s, %s, %s, NOW(), NOW(), '1', %s)"        
        
        database.insert_data(insert_query, (username, email, password, login_source))

        flash('註冊成功', 'success')

        # 重定向到註冊成功頁面或其他適當的頁面
        return redirect(url_for('auth.registration_successful'))
    
    original_data = session.get('original_data', {})
    return render_template('register.html', original_data=original_data)

@auth_bp.route('/logout')
def logout():
    session.pop('user_info', None)  # 清除用戶訊息
    return redirect(url_for('main.home'))  # 重新指向回首頁

@auth_bp.route('/dashboard')
@login_required
def dashboard():
    # 這是用戶登入後的頁面
    return render_template('dashboard.html')

@auth_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']

        # 如果 email 不存在，顯示錯誤消息
        user_info = get_user_info(email)
        if not user_info:
            flash('此電子郵件不存在', 'error')
            return render_template('forgot_password.html')

        try:
            # 生成重置令牌
            token = generate_reset_token(user_info)
            
            # 實例化 SMTPManager
            smtp_manager = current_app.config['SMTP_MANAGER']
            
            username = user_info[1]

            # 發送帶有重置連結的郵件
            subject = 'PM&HO_忘記密碼發信-測試'
            body = render_template('reset_password_email_template.html', user=username, token=token)
            smtp_manager.send_email(email, subject, body, confirmation_route='auth.reset_password')
            # 顯示成功消息
            flash('重置郵件已發送，請檢查您的電子郵件。', 'success')

        except Exception as e:
            # 顯示失敗消息
            flash(f'郵件發送失敗: {str(e)}', 'error')
    
    return render_template('forgot_password.html')

@auth_bp.route('/send_reset_email', methods=['POST'])
def send_reset_email():
    return render_template('send_reset_email.html')

@auth_bp.route('/registration_successful')
def registration_successful():
    # 查詢用戶信息,此處省略查詢代碼
    user_email  = session.get('user_email', None)

    # 從數據中換取用戶信息
    if user_email:
        user_info = get_user_info(user_email)
        if user_info:
            session['user_info'] = {'MemberID': user_info[0], 'MemberName': user_info[1]}
    return render_template('registration_successful.html')

@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # 解析令牌
    user_info = verify_reset_token(token)

    if user_info:
        if request.method == 'POST':
            new_password = request.form['password']
            confirm_password = request.form['confirm_password']

            # 檢查新密碼與確認密碼是否相符
            if new_password != confirm_password:
                flash('新密碼和確認密碼不相符', 'error')
                print('新密碼和確認密碼不相符')
                return redirect(url_for('auth.reset_password', token=token))
                
            # 將新密碼進行雜湊
            hashed_password = generate_password_hash(new_password)
            
            # 更新資料庫中的密碼
            user_id = user_info[0]
            # print(user_id)
            
            # 假設你的資料庫表名稱為 Members，Password 欄位名稱為 Password
            update_query = "UPDATE Members SET Password = %s WHERE MemberID = %s"
            database.update_data(update_query, (hashed_password, user_id))

            flash('密碼重置成功', 'success')
            return redirect(url_for('auth.login'))

        # 令牌有效，顯示重置密碼的頁面
        return render_template('reset_password.html', user_info=user_info)
    else:
        # 令牌無效，顯示錯誤消息或轉到錯誤頁面
        flash('重置令牌無效或已過期', 'error')
        return redirect(url_for('auth.forgot_password')) 
