#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
智能补货算法模块
"""

import os
import time
import json
import threading
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from src.utils.logger import get_logger

logger = get_logger('replenishment_algorithm')


class ReplenishmentAlgorithm:
    """智能补货算法类"""
    
    def __init__(self, config=None, simulation=False):
        """
        初始化智能补货算法
        
        Args:
            config (dict, optional): 配置字典
            simulation (bool, optional): 是否使用模拟模式
        """
        self.config = config or {}
        self.simulation = simulation
        
        # 补货配置
        self.algorithm = self.config.get('algorithm', 'predictive')  # simple, predictive, ml
        self.threshold = self.config.get('threshold', 0.2)  # 库存阈值
        self.prediction_window = self.config.get('prediction_window', 24)  # 预测窗口（小时）
        self.data_history_days = self.config.get('data_history_days', 30)  # 历史数据天数
        self.auto_order = self.config.get('auto_order', False)  # 自动下单
        
        # 销售数据
        self.sales_data = {}
        self.sales_history = []
        
        # 补货建议
        self.replenishment_suggestions = {}
        
        # 数据文件
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
        self.sales_data_file = os.path.join(self.data_dir, 'sales_data.json')
        
        # 线程控制
        self.running = False
        self.replenishment_thread = None
        
        # 加载历史销售数据
        self._load_sales_data()
        
        logger.info(f"智能补货算法初始化完成，使用{self.algorithm}算法")
    
    def _load_sales_data(self):
        """加载历史销售数据"""
        try:
            if os.path.exists(self.sales_data_file):
                with open(self.sales_data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.sales_data = data.get('product_sales', {})
                    self.sales_history = data.get('sales_history', [])
                
                logger.info(f"加载历史销售数据: {len(self.sales_data)} 种商品, {len(self.sales_history)} 条记录")
            else:
                self.sales_data = {}
                self.sales_history = []
                logger.info("未找到历史销售数据，使用空数据")
        except Exception as e:
            logger.error(f"加载历史销售数据失败: {str(e)}")
            self.sales_data = {}
            self.sales_history = []
    
    def _save_sales_data(self):
        """保存销售数据"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.sales_data_file), exist_ok=True)
            
            # 限制历史记录数量
            max_history = 10000  # 最多保留10000条历史记录
            if len(self.sales_history) > max_history:
                self.sales_history = self.sales_history[-max_history:]
            
            data = {
                'product_sales': self.sales_data,
                'sales_history': self.sales_history,
                'last_update': time.time()
            }
            
            with open(self.sales_data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.debug("保存销售数据")
        except Exception as e:
            logger.error(f"保存销售数据失败: {str(e)}")
    
    def start(self):
        """启动智能补货算法"""
        if self.running:
            logger.warning("智能补货算法已经在运行")
            return
        
        self.running = True
        
        # 启动补货线程
        self.replenishment_thread = threading.Thread(target=self._replenishment_loop, daemon=True)
        self.replenishment_thread.start()
        
        logger.info("智能补货算法启动完成")
    
    def stop(self):
        """停止智能补货算法"""
        if not self.running:
            logger.warning("智能补货算法已经停止")
            return
        
        self.running = False
        
        # 等待线程结束
        if self.replenishment_thread and self.replenishment_thread.is_alive():
            self.replenishment_thread.join(timeout=2.0)
        
        # 保存销售数据
        self._save_sales_data()
        
        logger.info("智能补货算法停止完成")
    
    def update_sales_data(self, transaction):
        """
        更新销售数据
        
        Args:
            transaction (dict): 交易数据
        """
        if transaction.get('status') != 'completed':
            return
        
        products_taken = transaction.get('products_taken', [])
        transaction_time = transaction.get('end_time', time.time())
        
        # 更新销售历史
        for product in products_taken:
            product_id = product.get('product_id')
            quantity = product.get('quantity', 0)
            price = product.get('price', 0.0)
            
            if quantity <= 0:
                continue
            
            # 添加到销售历史
            self.sales_history.append({
                'product_id': product_id,
                'quantity': quantity,
                'price': price,
                'amount': quantity * price,
                'timestamp': transaction_time
            })
            
            # 更新商品销售数据
            if product_id not in self.sales_data:
                self.sales_data[product_id] = {
                    'total_sales': 0,
                    'total_quantity': 0,
                    'last_sale': None,
                    'hourly_sales': [0] * 24,  # 按小时统计
                    'daily_sales': [0] * 7,    # 按星期几统计
                    'sales_trend': []          # 销售趋势
                }
            
            # 更新总销量
            self.sales_data[product_id]['total_sales'] += quantity * price
            self.sales_data[product_id]['total_quantity'] += quantity
            self.sales_data[product_id]['last_sale'] = transaction_time
            
            # 更新按小时统计
            hour = datetime.fromtimestamp(transaction_time).hour
            self.sales_data[product_id]['hourly_sales'][hour] += quantity
            
            # 更新按星期几统计
            weekday = datetime.fromtimestamp(transaction_time).weekday()
            self.sales_data[product_id]['daily_sales'][weekday] += quantity
            
            # 更新销售趋势
            self.sales_data[product_id]['sales_trend'].append({
                'timestamp': transaction_time,
                'quantity': quantity
            })
            
            # 限制趋势数据量
            max_trend = 100
            if len(self.sales_data[product_id]['sales_trend']) > max_trend:
                self.sales_data[product_id]['sales_trend'] = self.sales_data[product_id]['sales_trend'][-max_trend:]
        
        # 定期保存销售数据
        if len(self.sales_history) % 10 == 0:  # 每10笔交易保存一次
            self._save_sales_data()
    
    def check_replenishment_needs(self, inventory):
        """
        检查补货需求
        
        Args:
            inventory (dict): 当前库存
        
        Returns:
            dict: 补货需求
        """
        if not inventory:
            return None
        
        replenishment_needs = {
            'timestamp': time.time(),
            'products': []
        }
        
        # 获取商品数据库
        from src.utils.config_manager import ConfigManager
        config_manager = ConfigManager()
        product_database = config_manager.get_config().get('products', {})
        
        # 检查每种商品
        for product_id, product_info in product_database.items():
            # 获取当前库存
            current_stock = inventory.get(product_id, {}).get('quantity', 0)
            
            # 获取预测销量
            predicted_sales = self._predict_sales(product_id)
            
            # 计算补货阈值
            max_stock = 10  # 最大库存量
            threshold_quantity = max_stock * self.threshold
            
            # 如果当前库存低于阈值且预测销量大于0，需要补货
            if current_stock <= threshold_quantity and predicted_sales > 0:
                # 计算补货数量
                replenishment_quantity = max_stock - current_stock
                
                if replenishment_quantity > 0:
                    replenishment_needs['products'].append({
                        'product_id': product_id,
                        'name': product_info.get('name', 'Unknown'),
                        'current_stock': current_stock,
                        'predicted_sales': predicted_sales,
                        'replenishment_quantity': replenishment_quantity,
                        'priority': self._calculate_priority(product_id, current_stock, predicted_sales)
                    })
        
        # 按优先级排序
        replenishment_needs['products'].sort(key=lambda x: x['priority'], reverse=True)
        
        # 如果有补货需求，更新补货建议
        if replenishment_needs['products']:
            self.replenishment_suggestions = replenishment_needs
            logger.info(f"发现补货需求: {len(replenishment_needs['products'])} 种商品")
        
        return replenishment_needs if replenishment_needs['products'] else None
    
    def _predict_sales(self, product_id):
        """
        预测销量
        
        Args:
            product_id (str): 商品ID
        
        Returns:
            float: 预测销量
        """
        if self.algorithm == 'simple':
            return self._simple_prediction(product_id)
        elif self.algorithm == 'predictive':
            return self._predictive_analysis(product_id)
        elif self.algorithm == 'ml':
            return self._ml_prediction(product_id)
        else:
            return self._simple_prediction(product_id)
    
    def _simple_prediction(self, product_id):
        """
        简单预测算法
        
        Args:
            product_id (str): 商品ID
        
        Returns:
            float: 预测销量
        """
        # 如果没有销售数据，返回默认值
        if product_id not in self.sales_data:
            return 1.0
        
        # 计算平均日销量
        total_quantity = self.sales_data[product_id]['total_quantity']
        
        # 获取最早和最晚的销售记录
        sales_records = [record for record in self.sales_history if record['product_id'] == product_id]
        if not sales_records:
            return 1.0
        
        earliest_sale = min(record['timestamp'] for record in sales_records)
        latest_sale = max(record['timestamp'] for record in sales_records)
        
        # 计算销售天数
        days = (latest_sale - earliest_sale) / (24 * 3600) + 1
        days = max(days, 1)  # 至少1天
        
        # 计算平均日销量
        avg_daily_sales = total_quantity / days
        
        # 预测窗口内的销量
        predicted_sales = avg_daily_sales * (self.prediction_window / 24)
        
        return predicted_sales
    
    def _predictive_analysis(self, product_id):
        """
        预测性分析算法
        
        Args:
            product_id (str): 商品ID
        
        Returns:
            float: 预测销量
        """
        # 如果没有销售数据，返回默认值
        if product_id not in self.sales_data:
            return 1.0
        
        # 获取销售记录
        sales_records = [record for record in self.sales_history if record['product_id'] == product_id]
        if not sales_records:
            return 1.0
        
        # 获取当前时间
        now = datetime.now()
        
        # 计算当前小时和星期几
        current_hour = now.hour
        current_weekday = now.weekday()
        
        # 获取小时和星期几的销售数据
        hourly_sales = self.sales_data[product_id]['hourly_sales']
        daily_sales = self.sales_data[product_id]['daily_sales']
        
        # 计算小时权重和星期几权重
        total_hourly = sum(hourly_sales)
        total_daily = sum(daily_sales)
        
        if total_hourly == 0:
            hourly_weight = 1.0
        else:
            hourly_weight = hourly_sales[current_hour] / total_hourly
        
        if total_daily == 0:
            daily_weight = 1.0
        else:
            daily_weight = daily_sales[current_weekday] / total_daily
        
        # 计算基础预测
        base_prediction = self._simple_prediction(product_id)
        
        # 应用权重
        weighted_prediction = base_prediction * (hourly_weight + daily_weight) / 2
        
        # 考虑趋势
        trend_factor = self._calculate_trend_factor(product_id)
        
        # 最终预测
        final_prediction = weighted_prediction * trend_factor
        
        return max(final_prediction, 0.1)  # 至少0.1
    
    def _ml_prediction(self, product_id):
        """
        机器学习预测算法
        
        Args:
            product_id (str): 商品ID
        
        Returns:
            float: 预测销量
        """
        # 简化实现，实际应该使用机器学习模型
        # 这里使用预测性分析算法的结果，并添加一些随机性
        base_prediction = self._predictive_analysis(product_id)
        
        # 添加随机因子（模拟ML的波动）
        import random
        random_factor = 0.8 + random.random() * 0.4  # 0.8-1.2
        
        return base_prediction * random_factor
    
    def _calculate_trend_factor(self, product_id):
        """
        计算趋势因子
        
        Args:
            product_id (str): 商品ID
        
        Returns:
            float: 趋势因子
        """
        # 获取销售趋势数据
        if product_id not in self.sales_data:
            return 1.0
        
        trend_data = self.sales_data[product_id]['sales_trend']
        if len(trend_data) < 2:
            return 1.0
        
        # 计算最近7天和前7天的销量
        now = time.time()
        recent_sales = sum(item['quantity'] for item in trend_data 
                          if now - item['timestamp'] <= 7 * 24 * 3600)
        
        older_sales = sum(item['quantity'] for item in trend_data 
                         if 7 * 24 * 3600 < now - item['timestamp'] <= 14 * 24 * 3600)
        
        # 计算趋势因子
        if older_sales == 0:
            trend_factor = 1.0
        else:
            trend_factor = recent_sales / older_sales
        
        # 限制趋势因子范围
        trend_factor = max(min(trend_factor, 2.0), 0.5)
        
        return trend_factor
    
    def _calculate_priority(self, product_id, current_stock, predicted_sales):
        """
        计算补货优先级
        
        Args:
            product_id (str): 商品ID
            current_stock (int): 当前库存
            predicted_sales (float): 预测销量
        
        Returns:
            float: 优先级分数
        """
        # 如果库存为0，最高优先级
        if current_stock == 0:
            return 100.0
        
        # 计算库存覆盖率
        coverage = current_stock / max(predicted_sales, 0.1)
        
        # 覆盖率越低，优先级越高
        priority = 1.0 / max(coverage, 0.01)
        
        # 考虑销售量
        if product_id in self.sales_data:
            total_quantity = self.sales_data[product_id]['total_quantity']
            sales_factor = min(total_quantity / 10.0, 2.0)  # 最多提升2倍
            priority *= sales_factor
        
        return min(priority, 100.0)  # 最高100分
    
    def get_replenishment_suggestions(self):
        """
        获取补货建议
        
        Returns:
            dict: 补货建议
        """
        return self.replenishment_suggestions
    
    def get_sales_analytics(self, product_id=None, days=7):
        """
        获取销售分析
        
        Args:
            product_id (str, optional): 商品ID，如果为None则返回所有商品
            days (int, optional): 分析天数
        
        Returns:
            dict: 销售分析
        """
        # 获取时间范围
        end_time = time.time()
        start_time = end_time - days * 24 * 3600
        
        # 筛选销售记录
        if product_id:
            records = [r for r in self.sales_history 
                      if r['product_id'] == product_id and start_time <= r['timestamp'] <= end_time]
        else:
            records = [r for r in self.sales_history 
                      if start_time <= r['timestamp'] <= end_time]
        
        # 按商品分组
        product_sales = {}
        for record in records:
            pid = record['product_id']
            if pid not in product_sales:
                product_sales[pid] = {
                    'total_quantity': 0,
                    'total_amount': 0.0,
                    'sales_by_day': {}
                }
            
            product_sales[pid]['total_quantity'] += record['quantity']
            product_sales[pid]['total_amount'] += record['amount']
            
            # 按天统计
            day = datetime.fromtimestamp(record['timestamp']).strftime('%Y-%m-%d')
            if day not in product_sales[pid]['sales_by_day']:
                product_sales[pid]['sales_by_day'][day] = {
                    'quantity': 0,
                    'amount': 0.0
                }
            
            product_sales[pid]['sales_by_day'][day]['quantity'] += record['quantity']
            product_sales[pid]['sales_by_day'][day]['amount'] += record['amount']
        
        # 计算总销量和总金额
        total_quantity = sum(p['total_quantity'] for p in product_sales.values())
        total_amount = sum(p['total_amount'] for p in product_sales.values())
        
        # 按天统计总销量
        sales_by_day = {}
        for pid, data in product_sales.items():
            for day, day_data in data['sales_by_day'].items():
                if day not in sales_by_day:
                    sales_by_day[day] = {
                        'quantity': 0,
                        'amount': 0.0
                    }
                
                sales_by_day[day]['quantity'] += day_data['quantity']
                sales_by_day[day]['amount'] += day_data['amount']
        
        return {
            'start_date': datetime.fromtimestamp(start_time).strftime('%Y-%m-%d'),
            'end_date': datetime.fromtimestamp(end_time).strftime('%Y-%m-%d'),
            'total_quantity': total_quantity,
            'total_amount': total_amount,
            'product_sales': product_sales,
            'sales_by_day': sales_by_day
        }
    
    def _replenishment_loop(self):
        """补货循环线程"""
        logger.info("启动补货循环线程")
        
        while self.running:
            try:
                # 每小时检查一次自动补货
                if self.auto_order and int(time.time()) % 3600 < 10:
                    self._check_auto_replenishment()
                
                # 休眠一段时间
                time.sleep(60.0)
            except Exception as e:
                logger.error(f"补货循环出错: {str(e)}")
                time.sleep(300.0)  # 出错后等待较长时间再重试
    
    def _check_auto_replenishment(self):
        """检查自动补货"""
        # 如果有补货建议，自动下单
        if self.replenishment_suggestions and self.replenishment_suggestions.get('products'):
            logger.info("执行自动补货")
            
            # TODO: 实现实际的自动下单逻辑
            
            # 模拟下单
            order = {
                'order_id': f"O{int(time.time())}",
                'timestamp': time.time(),
                'products': self.replenishment_suggestions['products'],
                'status': 'placed'
            }
            
            logger.info(f"自动下单成功: {order['order_id']}, {len(order['products'])} 种商品")
            
            # 清空补货建议
            self.replenishment_suggestions = {}