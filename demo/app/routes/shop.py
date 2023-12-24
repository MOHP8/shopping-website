from flask import Blueprint, render_template, request
from database import Database
import json
import base64

shop = Blueprint('shop', __name__)
database = Database()


@shop.route('/product/<product_id>')
def product(product_id):
    # 使用参数构建查询语句
    select_query = "SELECT * FROM Products WHERE productID = %s AND State = 1"
    # 获取单个产品的数据
    product_data = database.get_data(select_query, (product_id,))
    # print(product_data)
    if not product_data:
        # 如果找不到对应产品，可以根据需要处理这种情况，比如重定向到一个错误页面
        return render_template('product_not_found.html')

    # 使用列名构建字典
    column_names = ['UUID', 'id', 'category', 'name', 'stock', 'price', 'image', 'product_date', 'update_date',
                    'state']
    product = dict(zip(column_names, product_data[0]))

    # 将图片数据转换为 base64 编码
    if product["image"]:
        image_base64 = base64.b64encode(product["image"]).decode("utf-8")
        product["image_base64"] = image_base64
    else:
        product["image_base64"] = None

    return render_template('product.html', product=product)
