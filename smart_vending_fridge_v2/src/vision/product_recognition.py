#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
商品识别模块 - 负责智能售卖柜的商品识别
"""

import os
import json
import logging
import random
import time
from ..utils.config_manager import ConfigManager

class ProductRecognition:
    """商品识别类，负责识别智能售卖柜中的商品"""
    
    def __init__(self, config_manager=None):
        """
        初始化商品识别系统
        
        Args:
            config_manager (ConfigManager, optional): 配置管理器实例
        """
        self.config_manager = config_manager or ConfigManager()
        
        # 获取视觉配置
        self.vision_config = self.config_manager.get_value('vision', {})
        self.camera_id = self.vision_config.get('camera_id', 0)
        self.model_path = self.vision_config.get('model_path', 'models/product_recognition_v2.onnx')
        self.confidence_threshold = self.vision_config.get('confidence_threshold', 0.7)
        self.capture_interval = self.vision_config.get('capture_interval', 0.5)
        
        # 商品数据库路径
        self.product_db_path = self.vision_config.get('product_database_path', 'data/products.json')
        self.product_db_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            self.product_db_path
        )
        
        # 加载商品数据库
        self.products = self._load_product_database()
        
        logging.info("商品识别系统初始化完成")
    
    def _load_product_database(self):
        """
        加载商品数据库
        
        Returns:
            dict: 商品数据库
        """
        try:
            if os.path.exists(self.product_db_path):
                with open(self.product_db_path, 'r', encoding='utf-8') as f:
                    products = json.load(f)
                logging.info(f"从 {self.product_db_path} 加载商品数据库")
                return products
        except Exception as e:
            logging.error(f"加载商品数据库失败: {str(e)}")
        
        # 使用配置中的商品作为默认数据库
        products = self.config_manager.get_value('products', {})
        logging.warning(f"使用配置中的商品数据作为默认数据库")
        return products
    
    def recognize_products(self):
        """
        识别商品
        
        Returns:
            list: 识别到的商品列表
        """
        logging.info("开始识别商品")
        
        # 模拟识别过程
        # 在实际应用中，这里应该调用计算机视觉模型进行商品识别
        time.sleep(1.5)  # 模拟识别耗时
        
        # 随机选择1-5个商品作为识别结果
        product_count = random.randint(1, 5)
        product_ids = list(self.products.keys())
        selected_product_ids = random.sample(product_ids, min(product_count, len(product_ids)))
        
        recognized_products = []
        for product_id in selected_product_ids:
            product = self.products[product_id]
            recognized_products.append({
                'product_id': product_id,
                'name': product.get('name', '未知商品'),
                'price': product.get('price', 0),
                'category': product.get('category', '未分类'),
                'confidence': round(random.uniform(self.confidence_threshold, 1.0), 2),
                'barcode': product.get('barcode', '')
            })
        
        logging.info(f"识别到 {len(recognized_products)} 件商品")
        return recognized_products
    
    def capture_image(self):
        """
        捕获图像
        
        Returns:
            bytes: 图像数据
        """
        # 模拟捕获图像
        # 在实际应用中，这里应该调用摄像头API捕获图像
        logging.info(f"从摄像头 {self.camera_id} 捕获图像")
        time.sleep(0.2)  # 模拟捕获耗时
        
        # 返回模拟的图像数据
        return b'MOCK_IMAGE_DATA'
    
    def detect_abnormal_behavior(self):
        """
        检测异常行为
        
        Returns:
            dict: 异常行为信息
        """
        # 模拟异常行为检测
        # 在实际应用中，这里应该调用计算机视觉模型进行异常行为检测
        
        # 随机模拟是否检测到异常行为
        is_abnormal = random.random() < 0.05  # 5%的概率检测到异常
        
        if is_abnormal:
            abnormal_types = ['遮挡摄像头', '放置异物', '偷窃行为', '尝试后放回']
            abnormal_type = random.choice(abnormal_types)
            
            logging.warning(f"检测到异常行为: {abnormal_type}")
            
            return {
                'is_abnormal': True,
                'type': abnormal_type,
                'confidence': round(random.uniform(0.7, 0.95), 2),
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
        
        return {
            'is_abnormal': False
        }