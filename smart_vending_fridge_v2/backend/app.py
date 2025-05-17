#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
智能售卖柜后台管理系统 - Flask Web应用
"""

import os
import sys
import json
import logging
import random
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, redirect, url_for, session

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.utils.config_manager import ConfigManager
except ImportError:
    # 如果无法导入，创建一个简单的配置管理器
    class ConfigManager:
        def __init__(self, config_path=None):
            self.config = {}
            if config_path and os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
        
        def get_value(self, key_path, default=None):
            keys = key_path.split('.')
            value = self.config
            try:
                for key in keys:
                    value = value[key]
                return value
            except (KeyError, TypeError):
                return default
        
        def update_config(self, new_config):
            self.config.update(new_config)
            return True

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

# 初始化配置管理器
config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config', 'config.json')
config_manager = ConfigManager(config_path)

# 用户数据（实际应用中应使用数据库）
users = {
    'admin': {
        'password': 'admin123',
        'role': 'admin',
        'name': '管理员',
        'last_login': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    },
    'operator': {
        'password': 'operator123',
        'role': 'operator',
        'name': '操作员',
        'last_login': (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S')
    }
}

# 模拟数据库
def load_data(file_name):
    """加载数据"""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    file_path = os.path.join(data_dir, file_name)
    
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"加载数据失败: {str(e)}")
    
    return []

def save_data(file_name, data):
    """保存数据"""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    os.makedirs(data_dir, exist_ok=True)
    file_path = os.path.join(data_dir, file_name)
    
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logging.error(f"保存数据失败: {str(e)}")
        return False

# 登录验证装饰器
def login_required(func):
    """登录验证装饰器"""
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
            
            # 更新最后登录时间
            users[username]['last_login'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
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

@app.route('/monitoring')
@login_required
def monitoring():
    """实时监控页面"""
    return render_template('monitoring.html', username=session.get('username'), name=session.get('name'))

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

@app.route('/order_detail')
@login_required
def order_detail():
    """订单详情页面"""
    return render_template('order_detail.html', username=session.get('username'), name=session.get('name'))

@app.route('/statistics')
@login_required
def statistics():
    """统计分析页面"""
    return render_template('statistics.html', username=session.get('username'), name=session.get('name'))

@app.route('/users')
@login_required
def users_page():
    """用户管理页面"""
    if session.get('role') != 'admin':
        return redirect(url_for('index'))
    return render_template('users.html', username=session.get('username'), name=session.get('name'))

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
    # 从配置中获取设备信息
    device_info = config_manager.get_value('device', {})
    
    # 模拟多个设备
    devices = [
        {
            'device_id': device_info.get('device_id', 'SVF-00001'),
            'model': device_info.get('model', 'SmartFridge-Pro'),
            'version': device_info.get('version', '1.0.0'),
            'serial_number': device_info.get('serial_number', 'SN12345678'),
            'status': 'online',
            'temperature': 4.2,
            'location': device_info.get('location', {}).get('address', '北京市朝阳区某商场'),
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            'device_id': 'SVF-00002',
            'model': 'SmartFridge-Pro',
            'version': '1.0.0',
            'serial_number': 'SN12345679',
            'status': 'online',
            'temperature': 3.8,
            'location': '北京市海淀区某写字楼',
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            'device_id': 'SVF-00003',
            'model': 'SmartFridge-Lite',
            'version': '1.0.0',
            'serial_number': 'SN12345680',
            'status': 'offline',
            'temperature': None,
            'location': '上海市浦东新区某商场',
            'last_update': (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
        }
    ]
    
    return jsonify(devices)

@app.route('/api/products', methods=['GET', 'POST'])
@login_required
def api_products():
    """获取或更新商品列表"""
    if request.method == 'GET':
        # 从配置中获取商品信息
        products = config_manager.get_value('products', {})
        
        # 转换为列表格式
        product_list = []
        for product_id, product in products.items():
            product_list.append({
                'product_id': product_id,
                'name': product.get('name', '未知商品'),
                'price': product.get('price', 0),
                'category': product.get('category', '未分类'),
                'barcode': product.get('barcode', ''),
                'image_path': product.get('image_path', ''),
                'shelf_life': product.get('shelf_life', 0),
                'description': product.get('description', '')
            })
        
        return jsonify(product_list)
    
    elif request.method == 'POST':
        # 添加新商品
        if session.get('role') != 'admin':
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        data = request.json
        product_id = data.get('product_id')
        
        if not product_id:
            return jsonify({'success': False, 'message': '商品ID不能为空'}), 400
        
        # 获取当前商品配置
        products = config_manager.get_value('products', {})
        
        # 检查商品ID是否已存在
        if product_id in products:
            return jsonify({'success': False, 'message': '商品ID已存在'}), 400
        
        # 添加新商品
        products[product_id] = {
            'name': data.get('name', '未知商品'),
            'price': data.get('price', 0),
            'category': data.get('category', '未分类'),
            'barcode': data.get('barcode', ''),
            'image_path': data.get('image_path', ''),
            'shelf_life': data.get('shelf_life', 0),
            'description': data.get('description', '')
        }
        
        # 保存配置
        config_manager.update_config({'products': products})
        
        return jsonify({'success': True, 'message': '商品添加成功'})

@app.route('/api/products/<product_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_product(product_id):
    """获取、更新或删除单个商品"""
    # 获取当前商品配置
    products = config_manager.get_value('products', {})
    
    if request.method == 'GET':
        # 获取商品信息
        if product_id not in products:
            return jsonify({'success': False, 'message': '商品不存在'}), 404
        
        product = products[product_id]
        return jsonify({
            'product_id': product_id,
            'name': product.get('name', '未知商品'),
            'price': product.get('price', 0),
            'category': product.get('category', '未分类'),
            'barcode': product.get('barcode', ''),
            'image_path': product.get('image_path', ''),
            'shelf_life': product.get('shelf_life', 0),
            'description': product.get('description', '')
        })
    
    elif request.method == 'PUT':
        # 更新商品信息
        if session.get('role') != 'admin':
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        if product_id not in products:
            return jsonify({'success': False, 'message': '商品不存在'}), 404
        
        data = request.json
        
        # 更新商品信息
        products[product_id].update({
            'name': data.get('name', products[product_id].get('name')),
            'price': data.get('price', products[product_id].get('price')),
            'category': data.get('category', products[product_id].get('category')),
            'barcode': data.get('barcode', products[product_id].get('barcode')),
            'image_path': data.get('image_path', products[product_id].get('image_path')),
            'shelf_life': data.get('shelf_life', products[product_id].get('shelf_life')),
            'description': data.get('description', products[product_id].get('description', ''))
        })
        
        # 保存配置
        config_manager.update_config({'products': products})
        
        return jsonify({'success': True, 'message': '商品更新成功'})
    
    elif request.method == 'DELETE':
        # 删除商品
        if session.get('role') != 'admin':
            return jsonify({'success': False, 'message': '权限不足'}), 403
        
        if product_id not in products:
            return jsonify({'success': False, 'message': '商品不存在'}), 404
        
        # 删除商品
        del products[product_id]
        
        # 保存配置
        config_manager.update_config({'products': products})
        
        return jsonify({'success': True, 'message': '商品删除成功'})

@app.route('/api/orders', methods=['GET'])
@login_required
def api_orders():
    """获取订单列表"""
    # 加载交易记录
    orders = load_data('payment_records.json')
    
    # 如果没有记录，返回模拟数据
    if not orders:
        orders = [
            {
                'transaction_id': "T12345-0001",
                'user_id': 'user123',
                'auth_method': 'qr_code',
                'start_time': (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'completed',
                'products': [
                    {
                        'product_id': 'SKU001',
                        'name': '可口可乐',
                        'price': 3.50,
                        'category': '饮料'
                    },
                    {
                        'product_id': 'SKU003',
                        'name': '农夫山泉',
                        'price': 2.00,
                        'category': '饮料'
                    }
                ],
                'total_amount': 5.50,
                'payment_status': 'paid',
                'payment_method': 'wechat',
                'end_time': (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                'transaction_id': "T12345-0002",
                'user_id': 'user456',
                'auth_method': 'face_recognition',
                'start_time': (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'completed',
                'products': [
                    {
                        'product_id': 'SKU004',
                        'name': '三明治',
                        'price': 15.00,
                        'category': '食品'
                    }
                ],
                'total_amount': 15.00,
                'payment_status': 'paid',
                'payment_method': 'alipay',
                'end_time': (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
            }
        ]
    
    return jsonify(orders)

@app.route('/api/orders/<order_id>', methods=['GET'])
@login_required
def api_order_detail(order_id):
    """获取订单详情"""
    # 加载交易记录
    orders = load_data('payment_records.json')
    
    # 如果没有记录，使用模拟数据
    if not orders:
        orders = [
            {
                'transaction_id': "T12345-0001",
                'user_id': 'user123',
                'auth_method': 'qr_code',
                'start_time': (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'completed',
                'products': [
                    {
                        'product_id': 'SKU001',
                        'name': '可口可乐',
                        'price': 3.50,
                        'category': '饮料'
                    },
                    {
                        'product_id': 'SKU003',
                        'name': '农夫山泉',
                        'price': 2.00,
                        'category': '饮料'
                    }
                ],
                'total_amount': 5.50,
                'payment_status': 'paid',
                'payment_method': 'wechat',
                'end_time': (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S')
            },
            {
                'transaction_id': "T12345-0002",
                'user_id': 'user456',
                'auth_method': 'face_recognition',
                'start_time': (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'completed',
                'products': [
                    {
                        'product_id': 'SKU004',
                        'name': '三明治',
                        'price': 15.00,
                        'category': '食品'
                    }
                ],
                'total_amount': 15.00,
                'payment_status': 'paid',
                'payment_method': 'alipay',
                'end_time': (datetime.now() - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
            }
        ]
    
    # 查找指定订单
    order = next((o for o in orders if o['transaction_id'] == order_id), None)
    
    if not order:
        return jsonify({'error': '订单不存在'}), 404
    
    return jsonify(order)

@app.route('/api/orders/<order_id>/refund', methods=['POST'])
@login_required
def api_order_refund(order_id):
    """订单退款"""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    # 加载交易记录
    orders = load_data('payment_records.json')
    
    # 查找指定订单
    order = next((o for o in orders if o['transaction_id'] == order_id), None)
    
    if not order:
        return jsonify({'success': False, 'message': '订单不存在'}), 404
    
    # 检查订单状态
    if order['status'] != 'completed' or order['payment_status'] != 'paid':
        return jsonify({'success': False, 'message': '订单状态不允许退款'}), 400
    
    # 更新订单状态
    order['payment_status'] = 'refunded'
    order['refund_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 保存更新后的订单
    save_data('payment_records.json', orders)
    
    return jsonify({'success': True, 'message': '退款成功'})

@app.route('/api/orders/<order_id>/cancel', methods=['POST'])
@login_required
def api_order_cancel(order_id):
    """取消订单"""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    # 加载交易记录
    orders = load_data('payment_records.json')
    
    # 查找指定订单
    order = next((o for o in orders if o['transaction_id'] == order_id), None)
    
    if not order:
        return jsonify({'success': False, 'message': '订单不存在'}), 404
    
    # 检查订单状态
    if order['status'] == 'completed':
        return jsonify({'success': False, 'message': '已完成的订单不能取消'}), 400
    
    # 更新订单状态
    order['status'] = 'cancelled'
    order['cancel_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # 保存更新后的订单
    save_data('payment_records.json', orders)
    
    return jsonify({'success': True, 'message': '订单已取消'})

@app.route('/api/statistics', methods=['GET'])
@login_required
def api_statistics():
    """获取统计数据"""
    # 获取日期范围
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # 加载交易记录
    orders = load_data('payment_records.json')
    
    # 如果没有记录，返回模拟数据
    if not orders:
        # 生成过去30天的日期
        daily_sales = {}
        today = datetime.now()
        for i in range(30):
            date = today - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            
            # 随机生成销售数据
            count = random.randint(5, 15)
            amount = round(count * (random.uniform(5, 15)), 2)
            
            daily_sales[date_str] = {
                'count': count,
                'amount': amount
            }
        
        return jsonify({
            'total_sales': 25,
            'total_amount': 267.50,
            'total_products': 46,
            'payment_methods': {
                'wechat': 15,
                'alipay': 8,
                'unionpay': 2
            },
            'product_sales': {
                'SKU001': {
                    'name': '可口可乐',
                    'count': 12,
                    'amount': 42.00
                },
                'SKU002': {
                    'name': '百事可乐',
                    'count': 8,
                    'amount': 28.00
                },
                'SKU003': {
                    'name': '农夫山泉',
                    'count': 10,
                    'amount': 20.00
                },
                'SKU004': {
                    'name': '三明治',
                    'count': 7,
                    'amount': 105.00
                },
                'SKU005': {
                    'name': '酸奶',
                    'count': 9,
                    'amount': 49.50
                }
            },
            'daily_sales': daily_sales,
            'hourly_sales': {str(h): random.randint(0, 10) for h in range(24)},
            'category_distribution': {
                '饮料': 90.00,
                '食品': 105.00,
                '乳制品': 49.50,
                '零食': 23.00
            }
        })
    
    # 统计数据
    stats = {
        'total_sales': len(orders),
        'total_amount': sum(order.get('total_amount', 0) for order in orders),
        'total_products': sum(len(order.get('products', [])) for order in orders),
        'payment_methods': {},
        'product_sales': {},
        'daily_sales': {},
        'hourly_sales': {str(h): 0 for h in range(24)},
        'category_distribution': {}
    }
    
    # 统计支付方式
    for order in orders:
        payment_method = order.get('payment_method')
        if payment_method:
            stats['payment_methods'][payment_method] = stats['payment_methods'].get(payment_method, 0) + 1
    
    # 统计商品销售
    for order in orders:
        for product in order.get('products', []):
            product_id = product.get('product_id')
            if product_id:
                if product_id not in stats['product_sales']:
                    stats['product_sales'][product_id] = {
                        'name': product.get('name', '未知商品'),
                        'count': 0,
                        'amount': 0
                    }
                stats['product_sales'][product_id]['count'] += 1
                stats['product_sales'][product_id]['amount'] += product.get('price', 0)
                
                # 统计类别
                category = product.get('category', '未分类')
                stats['category_distribution'][category] = stats['category_distribution'].get(category, 0) + product.get('price', 0)
    
    # 统计日销售和小时销售
    for order in orders:
        start_time = order.get('start_time')
        if start_time:
            # 日期
            date = start_time.split(' ')[0]
            if date not in stats['daily_sales']:
                stats['daily_sales'][date] = {
                    'count': 0,
                    'amount': 0
                }
            stats['daily_sales'][date]['count'] += 1
            stats['daily_sales'][date]['amount'] += order.get('total_amount', 0)
            
            # 小时
            try:
                hour = start_time.split(' ')[1].split(':')[0]
                stats['hourly_sales'][hour] = stats['hourly_sales'].get(hour, 0) + 1
            except (IndexError, ValueError):
                pass
    
    return jsonify(stats)

@app.route('/api/monitoring/realtime', methods=['GET'])
@login_required
def api_monitoring_realtime():
    """获取实时监控数据"""
    # 模拟实时数据
    temperature = round(4.0 + random.uniform(-0.5, 0.5), 1)
    humidity = round(45.0 + random.uniform(-5, 5), 1)
    door_open = random.random() < 0.2  # 20%概率门是开的
    device_online = random.random() < 0.95  # 95%概率设备在线
    
    # 模拟最近交易
    recent_transactions = []
    for i in range(3):
        time_offset = random.randint(1, 60) * i  # 1-60分钟前，递增
        transaction_time = datetime.now() - timedelta(minutes=time_offset)
        
        # 随机商品
        products = []
        product_count = random.randint(1, 3)
        all_products = list(config_manager.get_value('products', {}).items())
        if all_products:
            selected_products = random.sample(all_products, min(product_count, len(all_products)))
            for product_id, product in selected_products:
                products.append({
                    'name': product.get('name', '未知商品'),
                    'price': product.get('price', 0)
                })
        
        # 计算总金额
        amount = sum(p['price'] for p in products)
        
        recent_transactions.append({
            'time': transaction_time.strftime('%H:%M:%S'),
            'products': products,
            'amount': amount
        })
    
    return jsonify({
        'temperature': temperature,
        'humidity': humidity,
        'door_open': door_open,
        'device_online': device_online,
        'recent_transactions': recent_transactions
    })

@app.route('/api/users', methods=['GET', 'POST'])
@login_required
def api_users():
    """获取或添加用户"""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    if request.method == 'GET':
        # 返回用户列表
        user_list = []
        for username, user_data in users.items():
            user_list.append({
                'username': username,
                'name': user_data.get('name', ''),
                'role': user_data.get('role', ''),
                'last_login': user_data.get('last_login', '')
            })
        return jsonify(user_list)
    
    elif request.method == 'POST':
        # 添加新用户
        data = request.json
        username = data.get('username')
        
        if not username:
            return jsonify({'success': False, 'message': '用户名不能为空'}), 400
        
        if username in users:
            return jsonify({'success': False, 'message': '用户名已存在'}), 400
        
        # 添加用户
        users[username] = {
            'password': data.get('password', '123456'),
            'name': data.get('name', username),
            'role': data.get('role', 'operator'),
            'last_login': ''
        }
        
        return jsonify({'success': True, 'message': '用户添加成功'})

@app.route('/api/users/<username>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_user(username):
    """获取、更新或删除单个用户"""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    if username not in users:
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    
    if request.method == 'GET':
        # 获取用户信息
        user_data = users[username]
        return jsonify({
            'username': username,
            'name': user_data.get('name', ''),
            'role': user_data.get('role', ''),
            'last_login': user_data.get('last_login', '')
        })
    
    elif request.method == 'PUT':
        # 更新用户信息
        data = request.json
        
        # 不允许修改admin用户的角色
        if username == 'admin' and data.get('role') != 'admin':
            return jsonify({'success': False, 'message': '不能修改admin用户的角色'}), 400
        
        # 更新用户信息
        if 'name' in data:
            users[username]['name'] = data['name']
        
        if 'role' in data:
            users[username]['role'] = data['role']
        
        if 'password' in data and data['password']:
            users[username]['password'] = data['password']
        
        return jsonify({'success': True, 'message': '用户更新成功'})
    
    elif request.method == 'DELETE':
        # 不允许删除admin用户
        if username == 'admin':
            return jsonify({'success': False, 'message': '不能删除admin用户'}), 400
        
        # 删除用户
        del users[username]
        
        return jsonify({'success': True, 'message': '用户删除成功'})

@app.route('/api/settings', methods=['GET', 'POST'])
@login_required
def api_settings():
    """获取或更新系统设置"""
    if session.get('role') != 'admin':
        return jsonify({'success': False, 'message': '权限不足'}), 403
    
    if request.method == 'GET':
        # 获取系统设置
        settings = {
            'device': config_manager.get_value('device', {}),
            'hardware': config_manager.get_value('hardware', {}),
            'vision': config_manager.get_value('vision', {}),
            'payment': config_manager.get_value('payment', {}),
            'cloud': config_manager.get_value('cloud', {}),
            'system': config_manager.get_value('system', {})
        }
        
        return jsonify(settings)
    
    elif request.method == 'POST':
        # 更新系统设置
        data = request.json
        
        # 更新配置
        config_manager.update_config(data)
        
        return jsonify({'success': True, 'message': '系统设置更新成功'})

# 启动应用
if __name__ == '__main__':
    # 确保在正确的目录中
    current_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(current_dir, 'templates')
    static_dir = os.path.join(current_dir, 'static')
    
    # 创建必要的目录
    os.makedirs(templates_dir, exist_ok=True)
    os.makedirs(static_dir, exist_ok=True)
    os.makedirs(os.path.join(static_dir, 'js'), exist_ok=True)
    os.makedirs(os.path.join(static_dir, 'css'), exist_ok=True)
    
    # 启动应用
    app.run(host='0.0.0.0', port=5000, debug=True)