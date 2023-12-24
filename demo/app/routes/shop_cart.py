from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from database import Database
from werkzeug.security import generate_password_hash ,check_password_hash
from functools import wraps
import json
from uuid import uuid4

shop_cart = Blueprint('shop_cart', __name__)
database = Database()


# 登入過直接導向checkout Form 不然就去登入頁面
def login_checkout(route_func):
    @wraps(route_func)
    def decorated_route(*args, **kwargs):
        # print(session)
        if 'user_info' in session:
            return route_func(*args, **kwargs)
        else:
            return redirect(url_for('auth.login'))
    return decorated_route

@shop_cart.route('/add_to_cart', methods=['GET', 'POST'])
def add_to_cart():
    # 取得前端使用者輸入的產品數量
    data = request.json
    product_id = data.get('product_id')
    quantity = data.get('quantity')

   # 获取用户的购物车，如果不存在则创建一个
    user_cart = session.get('cart', {})

    # 更新购物车数据
    user_cart[product_id] = user_cart.get(product_id, 0) + quantity
    # print(user_cart)
    # # 将购物车数据存储在用户的会话中
    session['cart'] = user_cart
    # print(session)
    # print(f"adding_to_cart, {add_to_cart}")

    return jsonify({"cart_count": sum(user_cart.values())})

@shop_cart.route('/update_cart', methods=['GET'])
def update_cart():
    updated_cart = session.get('cart', {})
    # print(f"updated_cart, {updated_cart}")
    return jsonify({"cart_count": sum(updated_cart.values())})  # 返回購物車數量 JSON 數據


@shop_cart.route('/delete', methods=['GET'])
def delete_item():
    delete_id = request.args.get("delete_id")
    # print(delete_id)
    user_cart = session.get('cart', {})
    user_cart.pop(delete_id, None)
    session['cart'] = user_cart
    return redirect(url_for('shop_cart.checkout'))



@shop_cart.route('/checkout', methods=['GET'])
@login_checkout
def checkout():
    cart_details = []
    final_cart = {}
    user_cart = session.get('cart', {})
    # print(user_cart.items())
    # 取得購物車內相關資料
    for product_id, quantity in user_cart.items():
        select_query = "SELECT * FROM Products WHERE ProductID = %s "
        data = database.get_data(select_query,(product_id,))
        # print(f"data: {data}")

        # per_price = data[0][-2]
        per_product_detail = {
            "product_id": product_id,
            "product_name": data[0][3],
            "price": float(data[0][5]),
            "quantity": quantity,
            "subtotal": float(data[0][5]) * quantity
        }
        inventory = float(data[0][4])
        if inventory >= quantity:
            cart_details.append(per_product_detail)

        else:
            return "Out of Stock!"
    final_cart["cart_items"] = cart_details
    # print(cart_details)
    final_cart["total_amount"] = int(sum(item["subtotal"] for item in cart_details))

    user_info = session.get('user_info')
    member_id = user_info['MemberID']
    

    # 記錄訂單資訊訊息
    order_info = {'MemberId': member_id,'TotalPrice':final_cart['total_amount'],'cart_items':final_cart['cart_items']}
    session['order_info'] = order_info  # 將訂單信息儲存到會話中
    return render_template('checkout.html', final_cart=final_cart)

@shop_cart.route('/confirm_checkout')
def confirm_checkout():
    # # 取得訂單資訊
    # order_info = session.get('order_info')
    
    # uuid = str(uuid4())
    # order_info['UUID'] = uuid

    # # 更新庫存
    # for cart_item in order_info["cart_items"]:
    #     update_inv_query = "UPDATE Products SET stock = stock - %s WHERE ProductID = %s"
    #     database.update_data(update_inv_query, (cart_item['quantity'], cart_item['product_id']))
    
    # # 插入訂單
    # insert_order_query = "INSERT INTO Orders (UUID, MemberId, OrderDate, TotalPrice, State, Status) VALUES (%s, %s, NOW(), %s, 1, 1)"
    # database.insert_data(insert_order_query, (order_info['UUID'], order_info["MemberId"], order_info["TotalPrice"]))

    return render_template('checkout_response.html')
