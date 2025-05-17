#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
云平台管理模块
"""

import os
import time
import json
import threading
import requests
from datetime import datetime

from src.utils.logger import get_logger

logger = get_logger('cloud_manager')


class CloudManager:
    """云平台管理类"""
    
    def __init__(self, config=None, device_id=None, simulation=False):
        """
        初始化云平台管理器
        
        Args:
            config (dict, optional): 云平台配置
            device_id (str, optional): 设备ID
            simulation (bool, optional): 是否使用模拟模式
        """
        self.config = config or {}
        self.device_id = device_id or 'UNKNOWN'
        self.simulation = simulation
        
        # 云平台配置
        self.server_url = self.config.get('server_url', 'https://api.smartfridge.example.com')
        self.api_key = self.config.get('api_key', '')
        self.report_interval = self.config.get('report_interval', 60)
        self.heartbeat_interval = self.config.get('heartbeat_interval', 30)
        self.data_sync_interval = self.config.get('data_sync_interval', 300)
        
        # OTA更新配置
        self.ota_config = self.config.get('ota_update', {})
        self.ota_enabled = self.ota_config.get('enabled', True)
        self.ota_check_interval = self.ota_config.get('check_interval', 3600)
        
        # 连接状态
        self.connected = False
        self.last_heartbeat_time = 0
        self.last_report_time = 0
        self.last_sync_time = 0
        self.last_ota_check_time = 0
        
        # 数据缓存
        self.status_cache = []
        self.transaction_cache = []
        self.error_cache = []
        self.warning_cache = []
        self.replenishment_cache = []
        self.max_cache_size = 1000
        
        # 线程控制
        self.running = False
        self.cloud_thread = None
        
        # 数据目录
        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 缓存文件
        self.cache_file = os.path.join(self.data_dir, f'cloud_cache_{self.device_id}.json')
        
        # 加载缓存
        self._load_cache()
        
        logger.info(f"云平台管理器初始化完成，{'模拟' if simulation else '实际'}模式")
    
    def _load_cache(self):
        """加载缓存数据"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                
                self.status_cache = cache.get('status_cache', [])
                self.transaction_cache = cache.get('transaction_cache', [])
                self.error_cache = cache.get('error_cache', [])
                self.warning_cache = cache.get('warning_cache', [])
                self.replenishment_cache = cache.get('replenishment_cache', [])
                
                logger.info(f"加载云平台缓存: {len(self.status_cache)} 状态, {len(self.transaction_cache)} 交易")
        except Exception as e:
            logger.error(f"加载云平台缓存失败: {str(e)}")
    
    def _save_cache(self):
        """保存缓存数据"""
        try:
            cache = {
                'status_cache': self.status_cache[-self.max_cache_size:] if len(self.status_cache) > self.max_cache_size else self.status_cache,
                'transaction_cache': self.transaction_cache[-self.max_cache_size:] if len(self.transaction_cache) > self.max_cache_size else self.transaction_cache,
                'error_cache': self.error_cache[-self.max_cache_size:] if len(self.error_cache) > self.max_cache_size else self.error_cache,
                'warning_cache': self.warning_cache[-self.max_cache_size:] if len(self.warning_cache) > self.max_cache_size else self.warning_cache,
                'replenishment_cache': self.replenishment_cache[-self.max_cache_size:] if len(self.replenishment_cache) > self.max_cache_size else self.replenishment_cache
            }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache, f, ensure_ascii=False)
            
            logger.debug("保存云平台缓存")
        except Exception as e:
            logger.error(f"保存云平台缓存失败: {str(e)}")
    
    def start(self):
        """启动云平台管理器"""
        if self.running:
            logger.warning("云平台管理器已经在运行")
            return
        
        self.running = True
        
        # 启动云平台线程
        self.cloud_thread = threading.Thread(target=self._cloud_monitor, daemon=True)
        self.cloud_thread.start()
        
        logger.info("云平台管理器启动完成")
    
    def stop(self):
        """停止云平台管理器"""
        if not self.running:
            logger.warning("云平台管理器已经停止")
            return
        
        self.running = False
        
        # 等待线程结束
        if self.cloud_thread and self.cloud_thread.is_alive():
            self.cloud_thread.join(timeout=2.0)
        
        # 保存缓存
        self._save_cache()
        
        # 断开连接
        if self.connected:
            self._send_request('/device/disconnect', {
                'device_id': self.device_id,
                'timestamp': time.time()
            })
            self.connected = False
        
        logger.info("云平台管理器停止完成")
    
    def connect(self):
        """连接到云平台"""
        if self.connected:
            logger.warning("已经连接到云平台")
            return True
        
        try:
            # 发送连接请求
            response = self._send_request('/device/connect', {
                'device_id': self.device_id,
                'timestamp': time.time(),
                'version': '1.0.0'
            })
            
            if response and response.get('status') == 'success':
                self.connected = True
                logger.info(f"成功连接到云平台: {self.server_url}")
                return True
            else:
                logger.error(f"连接云平台失败: {response}")
                return False
        except Exception as e:
            logger.error(f"连接云平台出错: {str(e)}")
            return False
    
    def report_status(self, status):
        """
        上报设备状态
        
        Args:
            status (dict): 设备状态
        
        Returns:
            bool: 是否上报成功
        """
        if not self.connected:
            # 缓存状态
            self._cache_status(status)
            logger.debug("未连接到云平台，缓存状态")
            return False
        
        try:
            # 添加设备ID和时间戳
            status_data = status.copy()
            status_data.update({
                'device_id': self.device_id,
                'timestamp': time.time()
            })
            
            # 发送状态
            response = self._send_request('/device/status', status_data)
            
            if response and response.get('status') == 'success':
                logger.info("成功上报设备状态")
                self.last_report_time = time.time()
                return True
            else:
                # 缓存状态
                self._cache_status(status)
                logger.warning(f"上报设备状态失败: {response}")
                return False
        except Exception as e:
            # 缓存状态
            self._cache_status(status)
            logger.error(f"上报设备状态出错: {str(e)}")
            return False
    
    def report_transaction(self, transaction):
        """
        上报交易记录
        
        Args:
            transaction (dict): 交易记录
        
        Returns:
            bool: 是否上报成功
        """
        if not self.connected:
            # 缓存交易
            self._cache_transaction(transaction)
            logger.debug("未连接到云平台，缓存交易")
            return False
        
        try:
            # 添加设备ID
            transaction_data = transaction.copy()
            transaction_data.update({
                'device_id': self.device_id,
                'report_time': time.time()
            })
            
            # 发送交易
            response = self._send_request('/device/transaction', transaction_data)
            
            if response and response.get('status') == 'success':
                logger.info(f"成功上报交易记录: {transaction.get('id')}")
                return True
            else:
                # 缓存交易
                self._cache_transaction(transaction)
                logger.warning(f"上报交易记录失败: {response}")
                return False
        except Exception as e:
            # 缓存交易
            self._cache_transaction(transaction)
            logger.error(f"上报交易记录出错: {str(e)}")
            return False
    
    def report_error(self, error):
        """
        上报错误
        
        Args:
            error (dict): 错误信息
        
        Returns:
            bool: 是否上报成功
        """
        if not self.connected:
            # 缓存错误
            self._cache_error(error)
            logger.debug("未连接到云平台，缓存错误")
            return False
        
        try:
            # 添加设备ID
            error_data = error.copy()
            error_data.update({
                'device_id': self.device_id,
                'report_time': time.time()
            })
            
            # 发送错误
            response = self._send_request('/device/error', error_data)
            
            if response and response.get('status') == 'success':
                logger.info(f"成功上报错误: {error.get('message')}")
                return True
            else:
                # 缓存错误
                self._cache_error(error)
                logger.warning(f"上报错误失败: {response}")
                return False
        except Exception as e:
            # 缓存错误
            self._cache_error(error)
            logger.error(f"上报错误出错: {str(e)}")
            return False
    
    def report_warning(self, warning):
        """
        上报警告
        
        Args:
            warning (dict): 警告信息
        
        Returns:
            bool: 是否上报成功
        """
        if not self.connected:
            # 缓存警告
            self._cache_warning(warning)
            logger.debug("未连接到云平台，缓存警告")
            return False
        
        try:
            # 添加设备ID
            warning_data = warning.copy()
            warning_data.update({
                'device_id': self.device_id,
                'report_time': time.time()
            })
            
            # 发送警告
            response = self._send_request('/device/warning', warning_data)
            
            if response and response.get('status') == 'success':
                logger.info(f"成功上报警告: {warning.get('message')}")
                return True
            else:
                # 缓存警告
                self._cache_warning(warning)
                logger.warning(f"上报警告失败: {response}")
                return False
        except Exception as e:
            # 缓存警告
            self._cache_warning(warning)
            logger.error(f"上报警告出错: {str(e)}")
            return False
    
    def report_replenishment_needs(self, replenishment_needs):
        """
        上报补货需求
        
        Args:
            replenishment_needs (dict): 补货需求
        
        Returns:
            bool: 是否上报成功
        """
        if not self.connected:
            # 缓存补货需求
            self._cache_replenishment(replenishment_needs)
            logger.debug("未连接到云平台，缓存补货需求")
            return False
        
        try:
            # 添加设备ID
            replenishment_data = replenishment_needs.copy()
            replenishment_data.update({
                'device_id': self.device_id,
                'report_time': time.time()
            })
            
            # 发送补货需求
            response = self._send_request('/device/replenishment', replenishment_data)
            
            if response and response.get('status') == 'success':
                logger.info(f"成功上报补货需求: {len(replenishment_needs.get('products', []))} 种商品")
                return True
            else:
                # 缓存补货需求
                self._cache_replenishment(replenishment_needs)
                logger.warning(f"上报补货需求失败: {response}")
                return False
        except Exception as e:
            # 缓存补货需求
            self._cache_replenishment(replenishment_needs)
            logger.error(f"上报补货需求出错: {str(e)}")
            return False
    
    def get_config_update(self):
        """
        获取配置更新
        
        Returns:
            dict: 配置更新
        """
        if not self.connected:
            logger.debug("未连接到云平台，无法获取配置更新")
            return None
        
        try:
            # 发送请求
            response = self._send_request('/device/config', {
                'device_id': self.device_id,
                'timestamp': time.time()
            })
            
            if response and response.get('status') == 'success':
                config_update = response.get('data', {})
                if config_update:
                    logger.info(f"获取配置更新: {config_update}")
                return config_update
            else:
                logger.warning(f"获取配置更新失败: {response}")
                return None
        except Exception as e:
            logger.error(f"获取配置更新出错: {str(e)}")
            return None
    
    def check_ota_update(self):
        """
        检查OTA更新
        
        Returns:
            dict: OTA更新信息
        """
        if not self.connected or not self.ota_enabled:
            logger.debug("未连接到云平台或OTA未启用，无法检查更新")
            return None
        
        try:
            # 发送请求
            response = self._send_request('/device/ota/check', {
                'device_id': self.device_id,
                'version': '1.0.0',  # 当前版本
                'timestamp': time.time()
            })
            
            if response and response.get('status') == 'success':
                update_info = response.get('data', {})
                if update_info and update_info.get('has_update', False):
                    logger.info(f"发现OTA更新: {update_info.get('version')}")
                    return update_info
                return None
            else:
                logger.warning(f"检查OTA更新失败: {response}")
                return None
        except Exception as e:
            logger.error(f"检查OTA更新出错: {str(e)}")
            return None
    
    def download_ota_update(self, update_info):
        """
        下载OTA更新
        
        Args:
            update_info (dict): 更新信息
        
        Returns:
            bool: 是否下载成功
        """
        if not self.connected or not self.ota_enabled:
            logger.debug("未连接到云平台或OTA未启用，无法下载更新")
            return False
        
        try:
            # 获取下载URL
            download_url = update_info.get('download_url')
            if not download_url:
                logger.warning("更新信息中没有下载URL")
                return False
            
            # 下载文件
            response = requests.get(download_url, timeout=300)
            response.raise_for_status()
            
            # 保存文件
            update_file = os.path.join(self.data_dir, f"ota_update_{update_info.get('version')}.bin")
            with open(update_file, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"成功下载OTA更新: {update_file}")
            return True
        except Exception as e:
            logger.error(f"下载OTA更新出错: {str(e)}")
            return False
    
    def apply_ota_update(self, update_info):
        """
        应用OTA更新
        
        Args:
            update_info (dict): 更新信息
        
        Returns:
            bool: 是否应用成功
        """
        if not self.connected or not self.ota_enabled:
            logger.debug("未连接到云平台或OTA未启用，无法应用更新")
            return False
        
        try:
            # 获取更新文件
            update_file = os.path.join(self.data_dir, f"ota_update_{update_info.get('version')}.bin")
            if not os.path.exists(update_file):
                logger.warning(f"更新文件不存在: {update_file}")
                return False
            
            # TODO: 实现实际的OTA更新应用逻辑
            
            # 模拟应用更新
            logger.info(f"模拟应用OTA更新: {update_info.get('version')}")
            time.sleep(5)
            
            # 上报更新结果
            self._send_request('/device/ota/result', {
                'device_id': self.device_id,
                'version': update_info.get('version'),
                'success': True,
                'timestamp': time.time()
            })
            
            return True
        except Exception as e:
            logger.error(f"应用OTA更新出错: {str(e)}")
            
            # 上报更新失败
            self._send_request('/device/ota/result', {
                'device_id': self.device_id,
                'version': update_info.get('version'),
                'success': False,
                'error': str(e),
                'timestamp': time.time()
            })
            
            return False
    
    def _send_request(self, endpoint, data):
        """
        发送请求到云平台
        
        Args:
            endpoint (str): API端点
            data (dict): 请求数据
        
        Returns:
            dict: 响应数据
        """
        if self.simulation:
            # 模拟响应
            return {
                'status': 'success',
                'timestamp': time.time(),
                'data': {}
            }
        
        # 实际请求
        try:
            url = f"{self.server_url}{endpoint}"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f"Bearer {self.api_key}",
                'User-Agent': f"SmartVendingFridge/{self.device_id}"
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=10)
            response.raise_for_status()
            
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"请求云平台失败: {str(e)}")
            return None
    
    def _send_heartbeat(self):
        """发送心跳"""
        try:
            response = self._send_request('/device/heartbeat', {
                'device_id': self.device_id,
                'timestamp': time.time()
            })
            
            if response and response.get('status') == 'success':
                self.last_heartbeat_time = time.time()
                self.connected = True
                return True
            else:
                logger.warning(f"发送心跳失败: {response}")
                self.connected = False
                return False
        except Exception as e:
            logger.error(f"发送心跳出错: {str(e)}")
            self.connected = False
            return False
    
    def _cache_status(self, status):
        """缓存状态"""
        status_copy = status.copy()
        status_copy['timestamp'] = time.time()
        
        self.status_cache.append(status_copy)
        
        # 限制缓存大小
        if len(self.status_cache) > self.max_cache_size:
            self.status_cache = self.status_cache[-self.max_cache_size:]
    
    def _cache_transaction(self, transaction):
        """缓存交易"""
        transaction_copy = transaction.copy()
        transaction_copy['cache_time'] = time.time()
        
        self.transaction_cache.append(transaction_copy)
        
        # 限制缓存大小
        if len(self.transaction_cache) > self.max_cache_size:
            self.transaction_cache = self.transaction_cache[-self.max_cache_size:]
    
    def _cache_error(self, error):
        """缓存错误"""
        error_copy = error.copy()
        error_copy['cache_time'] = time.time()
        
        self.error_cache.append(error_copy)
        
        # 限制缓存大小
        if len(self.error_cache) > self.max_cache_size:
            self.error_cache = self.error_cache[-self.max_cache_size:]
    
    def _cache_warning(self, warning):
        """缓存警告"""
        warning_copy = warning.copy()
        warning_copy['cache_time'] = time.time()
        
        self.warning_cache.append(warning_copy)
        
        # 限制缓存大小
        if len(self.warning_cache) > self.max_cache_size:
            self.warning_cache = self.warning_cache[-self.max_cache_size:]
    
    def _cache_replenishment(self, replenishment):
        """缓存补货需求"""
        replenishment_copy = replenishment.copy()
        replenishment_copy['cache_time'] = time.time()
        
        self.replenishment_cache.append(replenishment_copy)
        
        # 限制缓存大小
        if len(self.replenishment_cache) > self.max_cache_size:
            self.replenishment_cache = self.replenishment_cache[-self.max_cache_size:]
    
    def _send_cached_data(self):
        """发送缓存数据"""
        # 发送缓存的状态
        if self.status_cache:
            try:
                # 只发送最新的状态
                latest_status = self.status_cache[-1]
                response = self._send_request('/device/status', {
                    'device_id': self.device_id,
                    'timestamp': time.time(),
                    'status': latest_status
                })
                
                if response and response.get('status') == 'success':
                    logger.info(f"成功发送缓存状态: {len(self.status_cache)} 条")
                    self.status_cache = []
            except Exception as e:
                logger.error(f"发送缓存状态出错: {str(e)}")
        
        # 发送缓存的交易
        if self.transaction_cache:
            try:
                # 尝试发送所有缓存的交易
                transactions_to_send = self.transaction_cache.copy()
                response = self._send_request('/device/transactions_batch', {
                    'device_id': self.device_id,
                    'timestamp': time.time(),
                    'transactions': transactions_to_send
                })
                
                if response and response.get('status') == 'success':
                    logger.info(f"成功发送缓存交易: {len(transactions_to_send)} 条")
                    self.transaction_cache = []
            except Exception as e:
                logger.error(f"发送缓存交易出错: {str(e)}")
        
        # 发送缓存的错误
        if self.error_cache:
            try:
                # 尝试发送所有缓存的错误
                errors_to_send = self.error_cache.copy()
                response = self._send_request('/device/errors_batch', {
                    'device_id': self.device_id,
                    'timestamp': time.time(),
                    'errors': errors_to_send
                })
                
                if response and response.get('status') == 'success':
                    logger.info(f"成功发送缓存错误: {len(errors_to_send)} 条")
                    self.error_cache = []
            except Exception as e:
                logger.error(f"发送缓存错误出错: {str(e)}")
        
        # 发送缓存的警告
        if self.warning_cache:
            try:
                # 尝试发送所有缓存的警告
                warnings_to_send = self.warning_cache.copy()
                response = self._send_request('/device/warnings_batch', {
                    'device_id': self.device_id,
                    'timestamp': time.time(),
                    'warnings': warnings_to_send
                })
                
                if response and response.get('status') == 'success':
                    logger.info(f"成功发送缓存警告: {len(warnings_to_send)} 条")
                    self.warning_cache = []
            except Exception as e:
                logger.error(f"发送缓存警告出错: {str(e)}")
        
        # 发送缓存的补货需求
        if self.replenishment_cache:
            try:
                # 尝试发送所有缓存的补货需求
                replenishments_to_send = self.replenishment_cache.copy()
                response = self._send_request('/device/replenishments_batch', {
                    'device_id': self.device_id,
                    'timestamp': time.time(),
                    'replenishments': replenishments_to_send
                })
                
                if response and response.get('status') == 'success':
                    logger.info(f"成功发送缓存补货需求: {len(replenishments_to_send)} 条")
                    self.replenishment_cache = []
            except Exception as e:
                logger.error(f"发送缓存补货需求出错: {str(e)}")
    
    def _cloud_monitor(self):
        """云平台监控线程"""
        logger.info("启动云平台监控线程")
        
        # 连接到云平台
        if not self.connected:
            self.connect()
        
        while self.running:
            try:
                current_time = time.time()
                
                # 发送心跳
                if current_time - self.last_heartbeat_time > self.heartbeat_interval:
                    self._send_heartbeat()
                
                # 如果连接正常，发送缓存数据
                if self.connected:
                    # 发送缓存数据
                    if current_time - self.last_sync_time > self.data_sync_interval:
                        self._send_cached_data()
                        self.last_sync_time = current_time
                    
                    # 检查配置更新
                    if current_time - self.last_report_time > self.report_interval * 10:
                        self.get_config_update()
                    
                    # 检查OTA更新
                    if self.ota_enabled and current_time - self.last_ota_check_time > self.ota_check_interval:
                        update_info = self.check_ota_update()
                        if update_info:
                            if self.download_ota_update(update_info):
                                self.apply_ota_update(update_info)
                        self.last_ota_check_time = current_time
                
                # 保存缓存（每小时）
                if int(current_time) % 3600 < 1:
                    self._save_cache()
                
                # 休眠一段时间
                time.sleep(1.0)
            except Exception as e:
                logger.error(f"云平台监控线程出错: {str(e)}")
                time.sleep(5.0)  # 出错后等待较长时间再重试