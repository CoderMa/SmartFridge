#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置管理模块
"""

import os
import json
import logging
from datetime import datetime

# 默认配置文件路径
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'config.json')

# 默认配置
DEFAULT_CONFIG = {
    'device': {
        'device_id': 'SVF-00001',
        'model': 'SmartFridge-Pro',
        'version': '1.0.0',
        'serial_number': 'SN12345678',
        'manufacture_date': datetime.now().strftime('%Y-%m-%d'),
        'location': {
            'latitude': 39.9042,
            'longitude': 116.4074,
            'address': '北京市朝阳区某商场'
        }
    },
    'hardware': {
        'lock_control': {
            'qr_code_enabled': True,
            'face_recognition_enabled': True,
            'lock_type': 'electronic',
            'auto_lock_timeout': 30,  # 自动锁定超时时间（秒）
            'security_level': 'high'  # 安全级别：low, medium, high
        },
        'temperature_control': {
            'target_temperature': 4.0,  # 目标温度（摄氏度）
            'range': {
                'min': 2.0,
                'max': 5.0
            },
            'cooling_technology': 'semiconductor',  # 半导体冷凝技术
            'power_saving_mode': True,
            'defrost_interval': 12  # 除霜间隔（小时）
        },
        'sensors': {
            'temperature_sensor': {
                'enabled': True,
                'sampling_interval': 60  # 采样间隔（秒）
            },
            'humidity_sensor': {
                'enabled': True,
                'sampling_interval': 300  # 采样间隔（秒）
            },
            'door_sensor': {
                'enabled': True,
                'sampling_interval': 1  # 采样间隔（秒）
            },
            'motion_sensor': {
                'enabled': True,
                'sampling_interval': 1  # 采样间隔（秒）
            },
            'gps': {
                'enabled': True,
                'sampling_interval': 3600  # 采样间隔（秒）
            },
            'power_monitor': {
                'enabled': True,
                'sampling_interval': 60  # 采样间隔（秒）
            }
        }
    },
    'vision': {
        'camera_id': 0,
        'model_path': 'models/product_recognition_v2.onnx',
        'confidence_threshold': 0.7,
        'capture_interval': 0.5,  # 捕获间隔（秒）
        'recognition_accuracy': 0.9,  # 识别准确率
        'product_database_path': 'data/products.json'
    },
    'payment': {
        'methods': ['wechat', 'alipay', 'unionpay', 'cash', 'digital_cny'],
        'api_keys': {
            'wechat': 'YOUR_WECHAT_API_KEY',
            'alipay': 'YOUR_ALIPAY_API_KEY',
            'unionpay': 'YOUR_UNIONPAY_API_KEY'
        },
        'payment_timeout': 300,  # 支付超时时间（秒）
        'auto_refund': True  # 自动退款（交易失败时）
    },
    'cloud': {
        'server_url': 'https://api.smartfridge.example.com',
        'api_key': 'YOUR_CLOUD_API_KEY',
        'report_interval': 60,  # 状态上报间隔（秒）
        'heartbeat_interval': 30,  # 心跳间隔（秒）
        'data_sync_interval': 300,  # 数据同步间隔（秒）
        'ota_update': {
            'enabled': True,
            'check_interval': 3600  # 检查更新间隔（秒）
        }
    },
    'replenishment': {
        'algorithm': 'predictive',  # 补货算法：simple, predictive, ml
        'threshold': 0.2,  # 库存阈值（低于此比例触发补货）
        'prediction_window': 24,  # 预测窗口（小时）
        'data_history_days': 30,  # 历史数据天数
        'auto_order': False  # 自动下单
    },
    'advertising': {
        'display_type': 'touch_screen',  # 显示类型：touch_screen, digital_signage
        'content_update_interval': 3600,  # 内容更新间隔（秒）
        'personalization': True,  # 个性化推荐
        'default_content_path': 'data/ads/default',
        'campaign_config_path': 'data/ads/campaigns.json'
    },
    'system': {
        'log_level': 'INFO',
        'log_retention_days': 30,
        'maintenance_interval': 30 * 24 * 3600,  # 维护间隔（秒）
        'auto_restart': {
            'enabled': True,
            'time': '03:00'  # 自动重启时间
        }
    },
    'products': {
        'SKU001': {
            'name': '可口可乐',
            'price': 3.50,
            'category': '饮料',
            'image_path': 'data/product_images/coke.jpg',
            'barcode': '6901234567890',
            'weight': 330,  # 克
            'dimensions': {
                'width': 6.5,  # 厘米
                'height': 12.0,
                'depth': 6.5
            },
            'shelf_life': 365,  # 天
            'storage_requirements': {
                'min_temp': 2,
                'max_temp': 8
            }
        },
        'SKU002': {
            'name': '百事可乐',
            'price': 3.50,
            'category': '饮料',
            'image_path': 'data/product_images/pepsi.jpg',
            'barcode': '6901234567891'
        },
        'SKU003': {
            'name': '农夫山泉',
            'price': 2.00,
            'category': '饮料',
            'image_path': 'data/product_images/water.jpg',
            'barcode': '6901234567892'
        },
        'SKU004': {
            'name': '三明治',
            'price': 15.00,
            'category': '食品',
            'image_path': 'data/product_images/sandwich.jpg',
            'barcode': '6901234567893',
            'shelf_life': 2  # 天
        },
        'SKU005': {
            'name': '酸奶',
            'price': 5.50,
            'category': '乳制品',
            'image_path': 'data/product_images/yogurt.jpg',
            'barcode': '6901234567894',
            'shelf_life': 7  # 天
        }
    }
}


class ConfigManager:
    """配置管理类"""
    
    def __init__(self, config_path=None):
        """
        初始化配置管理器
        
        Args:
            config_path (str, optional): 配置文件路径
        """
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self.config = self._load_config()
        
        # 确保配置文件存在
        self._ensure_config_file()
    
    def _load_config(self):
        """
        加载配置
        
        Returns:
            dict: 配置字典
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logging.info(f"从 {self.config_path} 加载配置")
                return config
        except Exception as e:
            logging.error(f"加载配置失败: {str(e)}")
        
        logging.warning(f"使用默认配置")
        return DEFAULT_CONFIG
    
    def _ensure_config_file(self):
        """确保配置文件存在"""
        if not os.path.exists(self.config_path):
            try:
                # 创建目录
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                
                # 写入默认配置
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=2)
                
                logging.info(f"创建默认配置文件: {self.config_path}")
            except Exception as e:
                logging.error(f"创建配置文件失败: {str(e)}")
    
    def get_config(self):
        """
        获取配置
        
        Returns:
            dict: 配置字典
        """
        return self.config
    
    def update_config(self, new_config):
        """
        更新配置
        
        Args:
            new_config (dict): 新配置
        
        Returns:
            bool: 是否更新成功
        """
        try:
            # 合并配置
            self._merge_config(self.config, new_config)
            
            # 保存配置
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            logging.info(f"更新配置文件: {self.config_path}")
            return True
        except Exception as e:
            logging.error(f"更新配置失败: {str(e)}")
            return False
    
    def _merge_config(self, target, source):
        """
        递归合并配置
        
        Args:
            target (dict): 目标配置
            source (dict): 源配置
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_config(target[key], value)
            else:
                target[key] = value
    
    def get_value(self, key_path, default=None):
        """
        获取配置值
        
        Args:
            key_path (str): 键路径，使用点号分隔，如 'hardware.sensors.temperature_sensor.enabled'
            default: 默认值
        
        Returns:
            配置值
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set_value(self, key_path, value):
        """
        设置配置值
        
        Args:
            key_path (str): 键路径，使用点号分隔
            value: 配置值
        
        Returns:
            bool: 是否设置成功
        """
        keys = key_path.split('.')
        target = self.config
        
        # 定位到最后一级的父节点
        for key in keys[:-1]:
            if key not in target or not isinstance(target[key], dict):
                target[key] = {}
            target = target[key]
        
        # 设置值
        try:
            target[keys[-1]] = value
            
            # 保存配置
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            
            logging.info(f"设置配置值: {key_path} = {value}")
            return True
        except Exception as e:
            logging.error(f"设置配置值失败: {str(e)}")
            return False