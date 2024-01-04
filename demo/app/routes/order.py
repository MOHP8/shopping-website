from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from database import Database
from werkzeug.security import generate_password_hash ,check_password_hash
from functools import wraps

order = Blueprint('order', __name__)
database = Database()

@order.route('/order_history')
def history():
    user_info = session.get('user_info')
    member_id = user_info['MemberID']
    print(member_id)
    # 訂單資訊
    check_query = "SELECT OrderID, OrderDate, TotalPrice, State FROM Orders WHERE MemberID = %s;"
    order_data = database.get_data(check_query,(member_id,))
    print(order_data)
    return render_template('order_history.html', order_data=order_data)
