import requests
from flask import current_app, Blueprint, request, jsonify, url_for, session ,render_template
import hashlib
import urllib.parse
from datetime import datetime
import json
from uuid import uuid4
from database import Database
from urllib.parse import parse_qs
from copy import deepcopy
import re

# 全方位金流付款
# 對應的API(前端導入)
'''
    <script>
        // 在按鈕點擊事件中呼叫此函式
        $(document).ready(function () {
            $("#checkoutButton").click(function () {
                // 在這裡呼叫後端程式碼
                createOrder();
            });
        });
    
        function createOrder() {
            $.ajax({
                type: "POST",
                url: "/get_order_data",  // 修改為實際的後端路由
                success: function (order_data) {
                    // 直接提交表單到綠界的 API 網址
                    submitToECPay(order_data);
                },
                error: function (error) {
                    console.error(error);
                    // 處理錯誤的邏輯
                }
            });
        }
    
        function submitToECPay(order_data) {
            var form = $('<form action="{{config.EC_PAY_API_BASE_URL}}" method="post" target="_self"></form>');
            
            // 將每個參數添加為一個input元素
            for (var key in order_data) {
                if (order_data.hasOwnProperty(key)) {
                    form.append('<input type="hidden" name="' + key + '" value="' + order_data[key] + '">');
                }
            }
            
            // 設定 contentType
            form.attr('enctype', 'application/x-www-form-urlencoded');

            $('body').append(form);
            form.submit();
        }

    </script>
'''

ec_pay_bp = Blueprint('ec_pay', __name__)
database = Database()

@ec_pay_bp.route('/get_order_data', methods=['POST'])
def get_order_data():
    # 取得訂單資訊
    order_info = session.get('order_info')
    # 取得當前時間的年月日時分秒毫秒
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")[2:-3]

    # 產生長度為 15 的鍵
    uuid = str(timestamp)
    # uuid = str(uuid4())
    # #使用正則表達式提取英數字大小寫混合部分
    # pattern = re.compile('[a-zA-Z0-9]+')
    # matches_uuid = pattern.findall(uuid)
    # print(uuid)
    order_info['UUID'] = 'PMHO'+uuid

    current_app.logger.info('取得訂單資訊。')  # 使用 Flask 應用程式的 logger
    order_data = generate_fake_order_data()
    result = create_ecpay_order(order_data)
    current_app.logger.info('get_order_data 的回應: %s', result)
    # print(result)
    return result

def create_ecpay_order(order_data):
    # 處理建立訂單的邏輯

    # 計算 CheckMacValue
    order_data['CheckMacValue'] = generate_check_mac(order_data)

    api_url = current_app.config['EC_PAY_API_BASE_URL']
    payload = {
            'MerchantID': order_data['MerchantID'],  # str: 特店編號
            'MerchantTradeNo': order_data['MerchantTradeNo'],  # str: 特店訂單編號
            'MerchantTradeDate': order_data['MerchantTradeDate'],  # str: 特店交易時間
            'PaymentType': order_data['PaymentType'],  # str: 交易類型
            'TotalAmount': order_data['TotalAmount'],  # int: 交易金額
            'TradeDesc': order_data['TradeDesc'],  # str: 交易描述
            'ItemName': order_data['ItemName'],  # str: 商品名稱
            'ReturnURL': order_data['ReturnURL'],  # str: 付款完成通知回傳網址
            'ChoosePayment': order_data['ChoosePayment'],  # str: 選擇預設付款方式
            'CheckMacValue': order_data['CheckMacValue'],  # str: 檢查碼 (應在 generate_check_mac 方法中計算)
            'EncryptType': order_data['EncryptType'],  # int: CheckMacValue加密類型 (固定使用 SHA256 加密)
            # 'StoreID': 'PMHO',  # str: 特店旗下店舖代號
            'ClientBackURL': order_data['ClientBackURL'],  # str: Client端返回特店的按鈕連結
            # 'ItemURL': order_data['ItemURL'],  # str: 商品銷售網址
            # 'Remark': order_data['Remark'],  # str: 備註欄位
            # 'ChooseSubPayment': order_data['ChooseSubPayment'],  # str: 付款子項目
            # 'OrderResultURL': order_data['OrderResultURL'],  # str: Client端回傳付款結果網址
            # 'NeedExtraPaidInfo': order_data['NeedExtraPaidInfo'],  # str: 是否需要額外的付款資訊
            # 'IgnorePayment': order_data['IgnorePayment'],  # str: 隱藏付款方式
            # 'PlatformID': order_data['PlatformID'],  # str: 特約合作平台商代號
            # 'CustomField1': order_data['CustomField1'],  # str: 自訂名稱欄位1
            # 'CustomField2': order_data['CustomField2'],  # str: 自訂名稱欄位2
            # 'CustomField3': order_data['CustomField3'],  # str: 自訂名稱欄位3
            # 'CustomField4': order_data['CustomField4'],  # str: 自訂名稱欄位4
            # 'Language': order_data['Language']  # str: 語系設定
        }
    

    # 取得訂單資訊
    order_info = session.get('order_info')
    # 插入訂單
    insert_order_query = "INSERT INTO Orders (UUID, MemberId, OrderDate, TotalPrice, State, Status) VALUES (%s, %s, NOW(), %s, 1, 1)"
    database.insert_data(insert_order_query, (order_info['UUID'], order_info["MemberId"], order_info["TotalPrice"]))

    # print(payload)
    return payload

@ec_pay_bp.route('/check_mac', methods=['POST'])
def check_mac():
    # 這裡處理產生檢查碼的邏輯
    order_data = request.json  # 獲取從前端發送的訂單資訊
    check_mac_value = generate_check_mac(order_data)  # 請參考下方的新函式
    return jsonify({'check_mac': check_mac_value})

# 在 create_ecpay_order 函式中
def generate_fake_order_data():
    # 取得訂單資訊
    order_info = session.get('order_info')
    order_data = {
        'MerchantID': current_app.config['EC_PAY_MERCHANT_ID'],
        'MerchantTradeNo': str(order_info["UUID"]),
        'MerchantTradeDate': datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
        'PaymentType': 'aio',
        'TotalAmount': order_info["TotalPrice"],  # 填入實際金額
        'TradeDesc': '促銷方案',
        'ItemName': '商品名稱',
        'ReturnURL': url_for('ec_pay.return_url', _external=True, _scheme='https'),
        'ChoosePayment': 'Credit',  # 付款方式，這裡假設為信用卡
        'EncryptType': 1,
        'ClientBackURL': url_for('main.home', _external=True),
        # 'ItemURL': 'YourItemURL',
        # 'Remark': 'YourRemark',
        # 'ChooseSubPayment': '',  # 付款子項目
        # 'OrderResultURL': 'YourOrderResultURL',
        # 'NeedExtraPaidInfo': 'N',  # 是否需要額外的付款資訊
        # 'IgnorePayment': 'CVS#BARCODE',  # 隱藏付款方式
        # 'PlatformID': '',  # 特約合作平台商代號
        # 'CustomField1': 'YourCustomField1',
        # 'CustomField2': 'YourCustomField2',
        # 'CustomField3': 'YourCustomField3',
        # 'CustomField4': 'YourCustomField4',
        # 'Language': 'zh-tw',  # 語系設定
    }
    return order_data

# 回傳消費者付款訊息
@ec_pay_bp.route('/return_url', methods=['POST'])
def return_url():
    # 接收 POST 請求中的付款結果訊息
    received_data = request.form.to_dict()

    # 在這裡加上檢查碼驗證的邏輯，確保訊息的完整性
    is_check_mac_valid = verify_check_mac(received_data)
    if is_check_mac_valid:
        # 如果檢查碼驗證通過，回應 1|OK
        response_data = '1|OK'
        check_mac_valid = 'OK'
    else:
        # 如果檢查碼驗證失敗，回應其他訊息
        response_data = 'CheckMacValue verification failed'
        check_mac_valid = 'failed'

    # 使用 get 方法取得字典中的值，避免 KeyError
    payment_type = received_data.get('PaymentType', '')
    rtn_msg = received_data.get('RtnMsg', '')
    simulate_paid = received_data.get('SimulatePaid', '')
    custom_field2 = received_data.get('CustomField2', '')
    payment_date = received_data.get('PaymentDate', '')
    trade_no = received_data.get('TradeNo', '')
    
    # 使用 try-except 處理可能的轉換錯誤
    try:
        trade_amt = int(received_data.get('TradeAmt', '0'))
        payment_type_charge_fee = int(received_data.get('PaymentTypeChargeFee', '0'))
    except ValueError:
        trade_amt = 0
        payment_type_charge_fee = 0

    merchant_id = received_data.get('MerchantID', '')
    store_id = received_data.get('StoreID', '')
    custom_field3 = received_data.get('CustomField3', '')
    merchant_trade_no = received_data.get('MerchantTradeNo', '')
    custom_field4 = received_data.get('CustomField4', '')
    check_mac_value = received_data.get('CheckMacValue', '')
    trade_date = received_data.get('TradeDate', '')
    custom_field1 = received_data.get('CustomField1', '')
    rtn_code = received_data.get('RtnCode', '')

    insert_query = """
        INSERT INTO ECPay_Payment_Result (
            PaymentType, RtnMsg, SimulatePaid, CustomField2, PaymentDate, TradeNo, TradeAmt,
            MerchantID, StoreID, CustomField3, MerchantTradeNo, CustomField4, CheckMacValue,
            TradeDate, CustomField1, RtnCode, PaymentTypeChargeFee, IsCheckMacValid
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    data = (
        payment_type, rtn_msg, simulate_paid, custom_field2, payment_date, trade_no,
        trade_amt, merchant_id, store_id, custom_field3, merchant_trade_no, custom_field4,
        check_mac_value, trade_date, custom_field1, rtn_code, payment_type_charge_fee,
        check_mac_valid
    )

    # 執行插入操作
    database.insert_data(insert_query, data)

    # # 取得訂單資訊
    # order_info = session.get('order_info')
    # # # 更新庫存
    # for cart_item in order_info["cart_items"]:
    #     update_inv_query = "UPDATE Products SET stock = stock - %s WHERE ProductID = %s"
    #     database.update_data(update_inv_query, (cart_item['quantity'], cart_item['product_id']))
    
    # # 清除 session 中的 order_info
    # session.pop('order_info', None)
    # del session['order_info']

    # session.pop('cart', None)
    # del session['cart']
    

    return response_data

# 主要函數: 檢查碼排序
def generate_check_mac(order_data):

    # 1. 排序參數
    sorted_params = sort_params(order_data)
    # print('1')
    # print(sorted_params)
    # 2. 加入 HashKey 和 HashIV
    hashed_params = add_hash_key_and_iv(sorted_params)
    # print('2')
    # print(hashed_params)
    # 3. 進行 URL 編碼
    url_encoded_params = url_encode_params(hashed_params)
    # print('3')
    # print(url_encoded_params)

    # 4.符號編碼表 (反向)
    decoded_string  = dotnet_url_decode(url_encoded_params)
    # print('4')
    # print(decoded_string)

    # 5. 轉為小寫
    lowercased_params = decoded_string.lower()
    # print('5')
    # print(lowercased_params)
    # 6. 使用 SHA256 加密
    check_mac_value = calculate_sha256(lowercased_params)
    # print('6')
    # print(check_mac_value)
    # 7. 轉為大寫
    check_mac_value = check_mac_value.upper()
    # print('7')
    # print(check_mac_value)
    # 在這裡可以驗證 CheckMacValue 是否正確，然後進行其他邏輯處理
    return check_mac_value

# 輔助函數: 驗證 CheckMacValue
def verify_check_mac(received_data):
    # 從 received_data 中取得 CheckMacValue
    received_check_mac = received_data.get('CheckMacValue', '')

    # 使用深層拷貝創建 del_received_check_mac，以避免修改原始數據
    del_received_check_mac = deepcopy(received_data)
    del del_received_check_mac["CheckMacValue"]

    # 使用 generate_check_mac 函數計算出期望的 CheckMacValue
    expected_check_mac = generate_check_mac(del_received_check_mac)
    
    # 檢查計算出的 CheckMacValue 與接收到的 CheckMacValue 是否相符
    return expected_check_mac == received_check_mac

# 輔助函數: 將參數排序
def sort_params(params):
    # 將參數按照字母順序排序
    sorted_params = sorted(params.items())
    return '&'.join(['{}={}'.format(key, value) for key, value in sorted_params])

# 輔助函數: 加入 HashKey 和 HashIV
def add_hash_key_and_iv(params):
    # 加入 HashKey 和 HashIV
    hash_key = current_app.config['EC_PAY_HASH_KEY']  # 替換成你的 HashKey
    hash_iv = current_app.config['EC_PAY_HASH_IV']  # 替換成你的 HashIV
    return 'HashKey={}&{}&HashIV={}'.format(hash_key, params, hash_iv)

# 輔助函數: 將字串進行 URL 編碼
def url_encode_params(params):
    # 進行 URL 編碼
    return urllib.parse.quote(params)

def dotnet_url_decode(encoded_value):
    replacements = {
        '%2d': '-', '%5f': '_', '%2e': '.', '%21': '!',
        '%2a': '*', '%28': '(', '%29': ')','%20':'+','/':'%2f'
    }

    # 將編碼根據反向編碼表替換
    decoded_value = encoded_value
    for pattern, replacement in replacements.items():
        decoded_value = decoded_value.replace(pattern, replacement)

    return decoded_value

# 輔助函數: 計算 SHA256 雜湊值
def calculate_sha256(data):
    # 使用 SHA256 加密方式生成雜湊值
    sha256 = hashlib.sha256()
    sha256.update(data.encode('utf-8'))
    return sha256.hexdigest()
