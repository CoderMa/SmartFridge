#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
智能售卖柜后台管理系统 - Flask Web应用
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, redirect, url_for, session

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 创建Flask应用
app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')
app.secret_key = 'smart_vending_fridge_secret_key'

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 用户数据
users = {
    'admin': {
        'password': 'admin123',
        'role': 'admin',
        'name': '管理员'
    },
    'operator': {
        'password': 'operator123',
        'role': 'operator',
        'name': '操作员'
    }
}

# 登录验证装饰器
def login_required(func):
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

# 路由定义
@app.route('/')
@login_required
def index():
    """首页"""
    return render_template('index.html', username=session.get('username'), name=session.get('name'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username in users and users[username]['password'] == password:
            session['username'] = username
            session['role'] = users[username]['role']
            session['name'] = users[username]['name']
            return redirect(url_for('index'))
        
        return render_template('login.html', error='用户名或密码错误')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """退出登录"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/devices')
@login_required
def devices():
    """设备管理页面"""
    return render_template('devices.html', username=session.get('username'), name=session.get('name'))

@app.route('/products')
@login_required
def products():
    """商品管理页面"""
    return render_template('products.html', username=session.get('username'), name=session.get('name'))

@app.route('/orders')
@login_required
def orders():
    """订单管理页面"""
    return render_template('orders.html', username=session.get('username'), name=session.get('name'))

@app.route('/statistics')
@login_required
def statistics():
    """统计分析页面"""
    return render_template('statistics.html', username=session.get('username'), name=session.get('name'))

@app.route('/settings')
@login_required
def settings():
    """系统设置页面"""
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
    
    return render_template('settings.html', username=session.get('username'), name=session.get('name'))

# API接口
@app.route('/api/devices', methods=['GET'])
@login_required
def api_devices():
    """获取设备列表"""
    devices = [
        {
            'device_id': 'SVF-00001',
            'model': 'SmartFridge-Pro',
            'version': '1.0.0',
            'status': 'online',
            'temperature': 4.2,
            'location': '北京市朝阳区某商场'
        },
        {
            'device_id': 'SVF-00002',
            'model': 'SmartFridge-Pro',
            'status': 'online',
            'temperature': 3.8,
            'location': '北京市海淀区某写字楼'
        },
        {
            'device_id': 'SVF-00003',
            'model': 'SmartFridge-Lite',
            'status': 'offline',
            'temperature': None,
            'location': '上海市浦东新区某商场'
        }
    ]
    
    return jsonify(devices)

@app.route('/api/products', methods=['GET', 'POST'])
@login_required
def api_products():
    """获取或更新商品列表"""
    if request.method == 'GET':
        products = [
            {
                'product_id': 'SKU001',
                'name': '可口可乐',
                'price': 3.50,
                'category': '饮料'
            },
            {
                'product_id': 'SKU002',
                'name': '百事可乐',
                'price': 3.50,
                'category': '饮料'
            },
            {
                'product_id': 'SKU003',
                'name': '农夫山泉',
                'price': 2.00,
                'category': '饮料'
            },
            {
                'product_id': 'SKU004',
                'name': '三明治',
                'price': 15.00,
                'category': '食品'
            },
            {
                'product_id': 'SKU005',
                'name': '酸奶',
                'price': 5.50,
                'category': '乳制品'
            }
        ]
        
        return jsonify(products)
    
    elif request.method == 'POST':
        if session.get('role') != 'admin':
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        data = request.json
        return jsonify({'success': True, 'message': '商品信息更新成功'})

@app.route('/api/orders', methods=['GET'])
@login_required
def api_orders():
    """获取订单列表"""
    orders = [
        {
            'transaction_id': 'T1234567890',
            'user_id': 'user123',
            'status': 'completed',
            'products': [
                {'name': '可口可乐', 'price': 3.50},
                {'name': '农夫山泉', 'price': 2.00}
            ],
            'total_amount': 5.50,
            'payment_method': 'wechat'
        },
        {
            'transaction_id': 'T1234567891',
            'user_id': 'user456',
            'status': 'completed',
            'products': [
                {'name': '三明治', 'price': 15.00}
            ],
            'total_amount': 15.00,
            'payment_method': 'alipay'
        }
    ]
    
    return jsonify(orders)

@app.route('/api/statistics', methods=['GET'])
@login_required
def api_statistics():
    """获取统计数据"""
    stats = {
        'total_sales': 25,
        'total_amount': 267.50,
        'payment_methods': {
            'wechat': 15,
            'alipay': 8,
            'unionpay': 2
        },
        'product_sales': {
            'SKU001': {'name': '可口可乐', 'count': 12, 'amount': 42.00},
            'SKU002': {'name': '百事可乐', 'count': 8, 'amount': 28.00},
            'SKU003': {'name': '农夫山泉', 'count': 10, 'amount': 20.00},
            'SKU004': {'name': '三明治', 'count': 7, 'amount': 105.00},
            'SKU005': {'name': '酸奶', 'count': 9, 'amount': 49.50}
        }
    }
    
    return jsonify(stats)

# 启动应用
if __name__ == '__main__':
    # 确保在正确的目录中
    current_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(current_dir, 'templates')
    static_dir = os.path.join(current_dir, 'static')
    
    # 创建必要的目录
    os.makedirs(templates_dir, exist_ok=True)
    os.makedirs(static_dir, exist_ok=True)
    
    # 创建简单的登录页面
    login_html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>智能售卖柜后台管理系统 - 登录</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #f5f5f5; }
            .login-container { background-color: white; padding: 20px; border-radius: 5px; box-shadow: 0 0 10px rgba(0,0,0,0.1); width: 300px; }
            h1 { text-align: center; color: #333; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; }
            input[type="text"], input[type="password"] { width: 100%; padding: 8px; box-sizing: border-box; border: 1px solid #ddd; border-radius: 4px; }
            button { width: 100%; padding: 10px; background-color: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; }
            button:hover { background-color: #45a049; }
            .error { color: red; margin-bottom: 15px; }
        </style>
    </head>
    <body>
        <div class="login-container">
            <h1>智能售卖柜后台管理系统</h1>
            {% if error %}
            <div class="error">{{ error }}</div>
            {% endif %}
            <form method="post">
                <div class="form-group">
                    <label for="username">用户名</label>
                    <input type="text" id="username" name="username" required>
                </div>
                <div class="form-group">
                    <label for="password">密码</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <button type="submit">登录</button>
            </form>
        </div>
    </body>
    </html>
    '''
    
    # 创建简单的首页
    index_html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>智能售卖柜后台管理系统</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 0; }
            .header { background-color: #4CAF50; color: white; padding: 15px; display: flex; justify-content: space-between; align-items: center; }
            .user-info { display: flex; align-items: center; }
            .user-info span { margin-right: 15px; }
            .container { display: flex; height: calc(100vh - 60px); }
            .sidebar { width: 200px; background-color: #f1f1f1; padding: 20px; }
            .sidebar ul { list-style-type: none; padding: 0; }
            .sidebar li { margin-bottom: 10px; }
            .sidebar a { text-decoration: none; color: #333; display: block; padding: 10px; border-radius: 4px; }
            .sidebar a:hover { background-color: #ddd; }
            .sidebar a.active { background-color: #4CAF50; color: white; }
            .content { flex-grow: 1; padding: 20px; }
            h1 { margin-top: 0; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>智能售卖柜后台管理系统</h1>
            <div class="user-info">
                <span>欢迎，{{ name }}</span>
                <a href="/logout" style="color: white;">退出</a>
            </div>
        </div>
        <div class="container">
            <div class="sidebar">
                <ul>
                    <li><a href="/" class="active">首页</a></li>
                    <li><a href="/devices">设备管理</a></li>
                    <li><a href="/products">商品管理</a></li>
                    <li><a href="/orders">订单管理</a></li>
                    <li><a href="/statistics">统计分析</a></li>
                    {% if session.role == 'admin' %}
                    <li><a href="/settings">系统设置</a></li>
                    {% endif %}
                </ul>
            </div>
            <div class="content">
                <h1>欢迎使用智能售卖柜后台管理系统</h1>
                <p>请从左侧菜单选择功能。</p>
            </div>
        </div>
    </body>
    </html>
    '''
    
    # 使用之前定义的templates_dir
    os.makedirs(templates_dir, exist_ok=True)
    
    with open(os.path.join(templates_dir, 'login.html'), 'w', encoding='utf-8') as f:
        f.write(login_html)
    
    with open(os.path.join(templates_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_html)
    
    # 启动应用
    app.run(host='0.0.0.0', port=5000, debug=True)