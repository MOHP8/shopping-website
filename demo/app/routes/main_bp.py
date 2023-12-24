from flask import Blueprint, render_template,request, jsonify ,g
from database import Database
import json
import base64

main_bp = Blueprint('main', __name__)
database = Database()


# 在應用程序首次啟動時緩存商品數據
@main_bp.before_app_request
def before_first_request():
    # 定義全局變數 all_products_cache 並使用 fetch_all_products_from_database 函數初始化它
    g.all_products_cache = fetch_all_products_from_database()

    # 獲取並緩存商品類別
    g.product_categories = get_all_categories()

def fetch_all_products_from_database():
    # 獲取所有商品數據的邏輯，使用 SQL 查詢選擇所有符合條件的商品
    # select_query = "SELECT * FROM Products WHERE State = 1"
    select_query = '''
        SELECT
        UUID,ProductID,ProductCategory,ProductName,Stock,Price,Image,ProductDate,UpdateDate,State
        FROM (
            SELECT 
                *,
                ROW_NUMBER() OVER (PARTITION BY ProductCategory ORDER BY ProductCategory) AS row_num
            FROM
                Products
            WHERE
                State = 1
        ) AS RankedProducts
        WHERE
            row_num <= 10;
    '''
    all_products = database.get_data_to_dict(select_query)

    # # 定義商品數據的列名，並將其轉換為字典形式
    # column_names = ['UUID', 'id', 'category', 'name', 'stock', 'price', 'image', 'product_date', 'update_date', 'State']
    # all_products = [dict(zip(column_names, product)) for product in products]

    return all_products

# 定義自定義的 JSONEncoder 類別，用於處理 bytes 或 bytearray 轉換為 utf-8 字符串
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (bytes, bytearray)):
            return obj.decode("utf-8")
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)

# 在 Blueprint 中設置全局 JSONEncoder 為自定義的 JSONEncoder 類別
main_bp.json_encoder = CustomJSONEncoder

def get_all_categories():
    select_query = "SELECT DISTINCT ProductCategory FROM Products"
    categories = database.get_data(select_query)
    categories = [category[0] for category in categories]
    return categories

@main_bp.route('/')
def home():
    # 從 g 對象獲取商品類別
    categories = g.product_categories

    # 返回首頁的 HTML 模板
    return render_template('index.html', categories=categories)


def search(keyword):
    # 先在全域變數中進行簡單的搜尋
    cached_result = list(simple_search_in_cache(keyword))
    if cached_result:
        print("cached", len(cached_result))
        for product in cached_result:
            if product["Image"]:
                product["Image"] = base64.b64encode(product["Image"]).decode("utf-8")
        # print(cached_result)
        return cached_result
    else:
        return  {'message': '沒有這個商品喔！'}

def simple_search_in_cache(keyword):
    # 在全域變數中進行簡單的搜尋
    all_products = g.all_products_cache
    result = [product for product in all_products if keyword.lower() in product['ProductName'].lower()]
    return result

def update_cache(keyword, result):
    # 更新全域變數緩存
    g.all_products_cache.extend(result)

@main_bp.route('/api/products')
def api_products():
    # 從請求參數中獲取分頁信息，默認為第1頁，每頁顯示4個商品
    page = request.args.get('page', 1, type=int)
    per_page = 8
    offset = (page - 1) * per_page

    # 從 g 對象獲取商品數據
    all_products = g.all_products_cache

    # 從請求參數中獲取選擇的分類
    selected_category = request.args.get('category', 'All', type=str)


    # 根據選擇的分類進行過濾
    if selected_category != 'All':
        filtered_products = [product for product in all_products if product['ProductCategory'] == selected_category]
    else:
        filtered_products = all_products

    keyword = request.args.get('keyword', '')
    # print("keyword", keyword)
    if keyword != 'None':
        search_result = search(keyword)
        # print('filter', len(search_result))

        # 檢查是否有提示信息
        if 'message' in search_result:
            return jsonify(message=search_result['message'])
        else:
            filtered_products = search_result

    # 切片取出指定分頁的商品
    print("offset", offset, offset+page)
    products_slice = filtered_products[offset:offset + per_page]
    print("products_slice", len(products_slice))
    # 將商品數據中的 image 欄位轉換為 base64 編碼的字符串
    for product in products_slice:
        if type(product["Image"]) == str:
            # print("I'm Here")
            # 將字符串轉換為 bytes
            product["Image"] = product["Image"].encode("utf-8")
        product["Image"] = base64.b64encode(product["Image"]).decode("utf-8")
    # print("slice", products_slice)
    # 將處理過的商品數據轉換為 JSON 格式的 response_data
    response_data = jsonify(all_products=products_slice)

    return response_data

@main_bp.route('/redemption')
def redemption():
    return render_template('redemption.html')

@main_bp.route('/response')
def response():
    return render_template('checkout_response.html')
