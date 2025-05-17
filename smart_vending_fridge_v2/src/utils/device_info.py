#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
设备信息模块
"""

import os
import uuid
import platform
import socket
import json
from datetime import datetime

class DeviceInfo:
    """设备信息类"""
    
    def __init__(self, config=None):
        """
        初始化设备信息
        
        Args:
            config (dict, optional): 设备配置
        """
        self.config = config or {}
        
        # 设备ID
        self.device_id = self._get_device_id()
        
        # 设备信息
        self.info = self._collect_device_info()
    
    def _get_device_id(self):
        """
        获取设备ID
        
        Returns:
            str: 设备ID
        """
        # 优先使用配置中的设备ID
        if self.config and 'device_id' in self.config:
            return self.config['device_id']
        
        # 尝试从设备信息文件中读取
        device_info_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'data',
            'device_info.json'
        )
        
        if os.path.exists(device_info_path):
            try:
                with open(device_info_path, 'r') as f:
                    device_info = json.load(f)
                    if 'device_id' in device_info:
                        return device_info['device_id']
            except Exception:
                pass
        
        # 生成新的设备ID
        device_id = f"SVF-{uuid.uuid4().hex[:8].upper()}"
        
        # 保存设备ID
        self._save_device_id(device_id, device_info_path)
        
        return device_id
    
    def _save_device_id(self, device_id, device_info_path):
        """
        保存设备ID
        
        Args:
            device_id (str): 设备ID
            device_info_path (str): 设备信息文件路径
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(device_info_path), exist_ok=True)
            
            # 读取现有信息（如果存在）
            device_info = {}
            if os.path.exists(device_info_path):
                with open(device_info_path, 'r') as f:
                    device_info = json.load(f)
            
            # 更新设备ID
            device_info['device_id'] = device_id
            
            # 保存信息
            with open(device_info_path, 'w') as f:
                json.dump(device_info, f, indent=2)
        except Exception:
            pass
    
    def _collect_device_info(self):
        """
        收集设备信息
        
        Returns:
            dict: 设备信息
        """
        info = {
            'device_id': self.device_id,
            'model': self.config.get('model', 'SmartFridge-Pro'),
            'version': self.config.get('version', '1.0.0'),
            'serial_number': self.config.get('serial_number', f"SN{uuid.uuid4().hex[:10].upper()}"),
            'manufacture_date': self.config.get('manufacture_date', datetime.now().strftime('%Y-%m-%d')),
            'system_info': {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'hostname': socket.gethostname()
            },
            'location': self.config.get('location', {
                'latitude': 0.0,
                'longitude': 0.0,
                'address': 'Unknown'
            })
        }
        
        return info
    
    def get_info(self):
        """
        获取设备信息
        
        Returns:
            dict: 设备信息
        """
        return self.info
    
    def update_location(self, latitude, longitude, address=None):
        """
        更新设备位置
        
        Args:
            latitude (float): 纬度
            longitude (float): 经度
            address (str, optional): 地址
        """
        self.info['location'] = {
            'latitude': latitude,
            'longitude': longitude,
            'address': address or self.info['location'].get('address', 'Unknown')
        }
    
    def to_dict(self):
        """
        转换为字典
        
        Returns:
            dict: 设备信息字典
        """
        return self.info