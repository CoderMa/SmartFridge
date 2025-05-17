#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
传感器系统模块 - 负责智能售卖柜的各种传感器数据采集
"""

import logging
import time
import random
from datetime import datetime

from ..utils.config_manager import ConfigManager


class SensorSystem:
    """传感器系统类，负责管理智能售卖柜的各种传感器"""
    
    def __init__(self, config_manager=None):
        """
        初始化传感器系统
        
        Args:
            config_manager (ConfigManager, optional): 配置管理器实例
        """
        self.config_manager = config_manager or ConfigManager()
        
        # 获取传感器配置
        self.sensors_config = self.config_manager.get_value('hardware.sensors', {})
        
        # 传感器状态
        self.sensor_status = {
            'temperature': 4.0,  # 默认温度（摄氏度）
            'humidity': 45.0,    # 默认湿度（%）
            'door': {
                'is_open': False,
                'last_change': datetime.now()
            },
            'motion': {
                'detected': False,
                'last_detected': None
            },
            'power': {
                'voltage': 220.0,
                'current': 1.5,
                'power_consumption': 330.0  # 瓦特
            },
            'last_update': datetime.now()
        }
        
        logging.info("传感器系统初始化完成")
    
    def get_temperature(self):
        """
        获取温度传感器数据
        
        Returns:
            float: 当前温度（摄氏度）
        """
        if not self.sensors_config.get('temperature_sensor', {}).get('enabled', True):
            logging.warning("温度传感器未启用")
            return None
        
        # 模拟温度传感器数据
        # 在实际应用中，这里应该从硬件接口获取实际温度
        target_temp = self.config_manager.get_value('hardware.temperature_control.target_temperature', 4.0)
        temp_range = self.config_manager.get_value('hardware.temperature_control.range', {'min': 2.0, 'max': 5.0})
        
        # 模拟温度波动
        self.sensor_status['temperature'] = round(
            target_temp + random.uniform(-0.5, 0.5), 1)
        
        # 确保温度在合理范围内
        self.sensor_status['temperature'] = max(
            temp_range.get('min', 2.0),
            min(self.sensor_status['temperature'], temp_range.get('max', 5.0))
        )
        
        return self.sensor_status['temperature']
    
    def get_humidity(self):
        """
        获取湿度传感器数据
        
        Returns:
            float: 当前湿度（%）
        """
        if not self.sensors_config.get('humidity_sensor', {}).get('enabled', True):
            logging.warning("湿度传感器未启用")
            return None
        
        # 模拟湿度传感器数据
        # 在实际应用中，这里应该从硬件接口获取实际湿度
        self.sensor_status['humidity'] = round(
            self.sensor_status['humidity'] + random.uniform(-1.0, 1.0), 1)
        
        # 确保湿度在合理范围内
        self.sensor_status['humidity'] = max(
            30.0, min(self.sensor_status['humidity'], 70.0))
        
        return self.sensor_status['humidity']
    
    def get_door_sensor_status(self):
        """
        获取门传感器状态
        
        Returns:
            dict: 门传感器状态
        """
        if not self.sensors_config.get('door_sensor', {}).get('enabled', True):
            logging.warning("门传感器未启用")
            return {'is_open': False, 'last_change': None}
        
        # 在实际应用中，这里应该从硬件接口获取门的实际状态
        # 这里仅返回模拟状态
        return self.sensor_status['door']
    
    def set_door_sensor_status(self, is_open):
        """
        设置门传感器状态（用于模拟或测试）
        
        Args:
            is_open (bool): 门是否打开
        """
        if self.sensor_status['door']['is_open'] != is_open:
            self.sensor_status['door']['is_open'] = is_open
            self.sensor_status['door']['last_change'] = datetime.now()
            logging.info(f"门状态变更为: {'打开' if is_open else '关闭'}")
    
    def get_motion_sensor_status(self):
        """
        获取运动传感器状态
        
        Returns:
            dict: 运动传感器状态
        """
        if not self.sensors_config.get('motion_sensor', {}).get('enabled', True):
            logging.warning("运动传感器未启用")
            return {'detected': False, 'last_detected': None}
        
        # 在实际应用中，这里应该从硬件接口获取运动传感器的实际状态
        # 这里随机模拟有时检测到运动
        if random.random() < 0.1:  # 10%的概率检测到运动
            self.sensor_status['motion']['detected'] = True
            self.sensor_status['motion']['last_detected'] = datetime.now()
        else:
            self.sensor_status['motion']['detected'] = False
        
        return self.sensor_status['motion']
    
    def get_power_status(self):
        """
        获取电源状态
        
        Returns:
            dict: 电源状态
        """
        if not self.sensors_config.get('power_monitor', {}).get('enabled', True):
            logging.warning("电源监控未启用")
            return None
        
        # 模拟电源状态
        # 在实际应用中，这里应该从硬件接口获取实际电源状态
        self.sensor_status['power']['voltage'] = round(220.0 + random.uniform(-5.0, 5.0), 1)
        self.sensor_status['power']['current'] = round(1.5 + random.uniform(-0.2, 0.2), 2)
        self.sensor_status['power']['power_consumption'] = round(
            self.sensor_status['power']['voltage'] * self.sensor_status['power']['current'], 1)
        
        return self.sensor_status['power']
    
    def get_all_sensor_data(self):
        """
        获取所有传感器数据
        
        Returns:
            dict: 所有传感器数据
        """
        # 更新所有传感器数据
        self.get_temperature()
        self.get_humidity()
        self.get_door_sensor_status()
        self.get_motion_sensor_status()
        self.get_power_status()
        
        self.sensor_status['last_update'] = datetime.now()
        
        return self.sensor_status