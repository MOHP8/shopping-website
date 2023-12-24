from flask import Flask, render_template, jsonify, request, session, redirect, Blueprint, url_for ,render_template_string
from werkzeug.security import generate_password_hash, check_password_hash
import time
import os
import collections
import hashlib
from urllib.parse import quote_plus
from database import Database
# 載入 ECpay SDK
import importlib.util
filename = os.path.dirname(os.path.realpath(__file__))
spec = importlib.util.spec_from_file_location(
    "ecpay_payment_sdk", filename + "/sdk/ecpay_payment_sdk.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
from datetime import datetime

ec_pay_sdk_bp = Blueprint('ec_pay_sdk', __name__)
database = Database()


# SDK(前端導入)
'''
    <script>
        $(document).ready(function () {
            $("#checkoutButton").click(function () {
                createOrder();
            });
        });

        function createOrder() {
            $.ajax({
                type: "POST",
                url: "/to_ecpay",  // 修改為實際的後端路由
                success: function (html) {
                    // 直接將 SDK 生成的 HTML 嵌入到您的頁面中
                    $('#ecpayFormContainer').html(html);
                    
                    // 提交表單
                    $('#ecpayForm').submit();
                },
                error: function (error) {
                    console.error(error);
                    // 處理錯誤的邏輯
                }
            });
        }
    </script>
'''
# 環境參數
class Params:
    def __init__(self):
        web_type = 'test'
        if web_type == 'offical':
            # 正式環境
            self.params = {
                'MerchantID': '隱藏',
                'HashKey': '隱藏',
                'HashIV': '隱藏',
                'action_url':
                'https://payment.ecpay.com.tw/Cashier/AioCheckOut/V5'
            }
        else:
            # 測試環境
            self.params = {
                'MerchantID':
                '3002607',
                'HashKey':
                'pwFHCqoQZGmho4w6',
                'HashIV':
                'EkRm7iFT261dpevs',
                'action_url':
                'https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5'
            }

    @classmethod
    def get_params(cls):
        return cls().params

    # 驗證綠界傳送的 check_mac_value 值是否正確
    @classmethod
    def get_mac_value(cls, get_request_form):

        params = dict(get_request_form)
        if params.get('CheckMacValue'):
            params.pop('CheckMacValue')

        ordered_params = collections.OrderedDict(
            sorted(params.items(), key=lambda k: k[0].lower()))

        HahKy = cls().params['HashKey']
        HashIV = cls().params['HashIV']

        encoding_lst = []
        encoding_lst.append('HashKey=%s&' % HahKy)
        encoding_lst.append(''.join([
            '{}={}&'.format(key, value)
            for key, value in ordered_params.items()
        ]))
        encoding_lst.append('HashIV=%s' % HashIV)

        safe_characters = '-_.!*()'

        encoding_str = ''.join(encoding_lst)
        encoding_str = quote_plus(str(encoding_str),
                                  safe=safe_characters).lower()

        check_mac_value = ''
        check_mac_value = hashlib.sha256(
            encoding_str.encode('utf-8')).hexdigest().upper()

        return check_mac_value


# 建立訂單後跳轉至 ECpay 頁面
@ec_pay_sdk_bp.route('/to_ecpay', methods=['POST'])
def ecpay():

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

    # 插入訂單
    insert_order_query = "INSERT INTO Orders (UUID, MemberId, OrderDate, TotalPrice, State, Status) VALUES (%s, %s, NOW(), %s, 1, 1)"
    database.insert_data(insert_order_query, (order_info['UUID'], order_info["MemberId"], order_info["TotalPrice"]))

    params = Params.get_params()

    # 設定傳送給綠界參數
    order_params = {
        'MerchantTradeNo': datetime.now().strftime("NO%Y%m%d%H%M%S"),
        'StoreID': '',
        'MerchantTradeDate': datetime.now().strftime("%Y/%m/%d %H:%M:%S"),
        'PaymentType': 'aio',
        'TotalAmount': order_info["TotalPrice"],
        'TradeDesc': 'ToolsFactory',
        'ItemName': '商品名稱',
        'ReturnURL': url_for('ec_pay_sdk.end_return', _external=True, _scheme='https'),
        'ChoosePayment': 'Credit',
        'ClientBackURL': url_for('main.home', _external=True),
        'Remark': '交易備註',
        'ChooseSubPayment': '',
        # 'OrderResultURL': host_name + 'payment/trad_result',
        'NeedExtraPaidInfo': 'Y',
        'DeviceSource': '',
        'IgnorePayment': '',
        'PlatformID': '',
        'InvoiceMark': 'N',
        'CustomField1': '',
        'CustomField2': '',
        'CustomField3': '',
        'CustomField4': '',
        'EncryptType': 1,
    }

    extend_params_1 = {
        'BindingCard': 0,
        'MerchantMemberID': '',
    }

    extend_params_2 = {
        'Redeem': 'N',
        'UnionPay': 0,
    }

    inv_params = {
        # 'RelateNumber': 'Tea0001', # 特店自訂編號
        # 'CustomerID': 'TEA_0000001', # 客戶編號
        # 'CustomerIdentifier': '53348111', # 統一編號
        # 'CustomerName': '客戶名稱',
        # 'CustomerAddr': '客戶地址',
        # 'CustomerPhone': '0912345678', # 客戶手機號碼
        # 'CustomerEmail': 'abc@ecpay.com.tw',
        # 'ClearanceMark': '2', # 通關方式
        # 'TaxType': '1', # 課稅類別
        # 'CarruerType': '', # 載具類別
        # 'CarruerNum': '', # 載具編號
        # 'Donation': '1', # 捐贈註記
        # 'LoveCode': '168001', # 捐贈碼
        # 'Print': '1',
        # 'InvoiceItemName': '測試商品1|測試商品2',
        # 'InvoiceItemCount': '2|3',
        # 'InvoiceItemWord': '個|包',
        # 'InvoiceItemPrice': '35|10',
        # 'InvoiceItemTaxType': '1|1',
        # 'InvoiceRemark': '測試商品1的說明|測試商品2的說明',
        # 'DelayDay': '0', # 延遲天數
        # 'InvType': '07', # 字軌類別
    }

    ecpay_payment_sdk = module.ECPayPaymentSdk(MerchantID=params['MerchantID'],
                                               HashKey=params['HashKey'],
                                               HashIV=params['HashIV'])

    # 合併延伸參數
    order_params.update(extend_params_1)
    order_params.update(extend_params_2)

    # 合併發票參數
    order_params.update(inv_params)

    try:
        # 產生綠界訂單所需參數
        final_order_params = ecpay_payment_sdk.create_order(order_params)

        # 產生 html 的 form 格式
        action_url = params['action_url']
        html = ecpay_payment_sdk.gen_html_post_form(action_url,
                                                    final_order_params)
        return html

    except Exception as error:
        print('An exception happened: ' + str(error))


# ReturnURL: 綠界 Server 端回傳 (POST)
# @csrf.exempt
@ec_pay_sdk_bp.route('/receive_result', methods=['POST'])
def end_return():
    # result = request.form['RtnMsg']
    # tid = request.form['CustomField1']
    # trade_detail = sql.Transaction.query.filter_by(tid=tid).first()
    # trade_detail.status = '交易成功 sever post'
    # db.session.add(trade_detail)
    # db.session.commit()
    print('--end_return-- OK')
    return '1|OK'


# OrderResultURL: 綠界 Client 端 (POST)
# @csrf.exempt
# @ec_pay_sdk_bp.route('/trad_result', methods=['GET', 'POST'])
# def end_page():

#     if request.method == 'GET':
#         return redirect(url_for('index'))

#     if request.method == 'POST':
#         check_mac_value = Params.get_mac_value(request.form)

#         if request.form['CheckMacValue'] != check_mac_value:
#             return '請聯繫管理員'

#         # 接收 ECpay 刷卡回傳資訊
#         result = request.form['RtnMsg']
#         tid = request.form['CustomField1']
#         trade_detail = sql.Transaction.query.filter_by(tid=tid).first()

#         # 取得交易使用者資訊
#         uid = trade_detail.uid

#         trade_client_detail = {
#             'name': trade_detail.trade_name,
#             'phone': trade_detail.trade_phone,
#             'county': trade_detail.trade_county,
#             'district': trade_detail.trade_district,
#             'zipcode': trade_detail.trade_zipcode,
#             'trade_address': trade_detail.trade_address
#         }

#         # 判斷成功
#         if result == 'Succeeded':
#             trade_detail.status = '待處理'
#             commit_list = []

#             # 移除 AddToCar (狀態：Y 修改成 N)
#             carts = sql.AddToCar.query.filter_by(uid=uid, state='Y')
#             for cart in carts:
#                 price = cart.product.price
#                 quan = cart.quantity
#                 cart.state = 'N'
#                 # 新增 Transaction_detail 訂單細項資料
#                 Td = sql.Transaction_detail(tid, cart.product.pid, quan, price)
#                 commit_list.append(Td)
#                 commit_list.append(cart)

#             db.session.add_all(commit_list)
#             db.session.commit()

#             # 讀取訂單細項資料
#             trade_detail_items = sql.Transaction_detail.query.filter_by(
#                 tid=tid)

#             return render_template('/payment/trade_success.html',
#                                    shopping_list=trade_detail_items,
#                                    total=trade_detail.total_value)

#         # 判斷失敗
#         else:
#             carts = sql.AddToCar.query.filter_by(uid=uid, state='Y')
#             trade_detail = sql.Transaction.query.filter_by(tid=tid).first()

#             return render_template('/payment/trade_fail.html',
#                                    shopping_list=carts,
#                                    total=trade_detail.total_value,
#                                    trade_client_detail=trade_client_detail)