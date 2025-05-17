#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
智能冰柜系统主程序
"""

import os
import sys
import time
import logging
import threading
import argparse
from datetime import datetime

# 添加src目录到系统路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.utils.config_manager import ConfigManager
from src.utils.logger import setup_logger
from src.hardware.lock_control import LockControlSystem
from src.hardware.temperature_control import TemperatureControlSystem
from src.hardware.sensor_system import SensorSystem
from src.vision.product_recognition import ProductRecognitionSystem
from src.payment.payment_manager import PaymentManager
from src.cloud.cloud_manager import CloudManager
from src.replenishment.replenishment_algorithm import ReplenishmentAlgorithm
from src.advertising.ad_system import AdvertisingSystem
from src.utils.device_info import DeviceInfo


class SmartVendingFridge:
    """智能冰柜系统主类"""
    
    def __init__(self, config_path=None, simulation_mode=False):
        """
        初始化智能冰柜系统
        
        Args:
            config_path (str, optional): 配置文件路径
            simulation_mode (bool, optional): 是否使用模拟模式
        """
        # 初始化配置
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()
        
        # 设置日志
        log_level = self.config.get('system', {}).get('log_level', 'INFO')
        self.logger = setup_logger('smart_vending_fridge', level=getattr(logging, log_level))
        self.logger.info("初始化智能冰柜系统...")
        
        # 设备信息
        self.device_info = DeviceInfo(self.config.get('device', {}))
        self.device_id = self.device_info.device_id
        self.logger.info(f"设备ID: {self.device_id}")
        
        # 模拟模式设置
        self.simulation_mode = simulation_mode
        if simulation_mode:
            self.logger.info("系统运行在模拟模式")
        
        # 系统状态
        self.system_status = {
            'running': False,
            'door_status': 'closed',
            'temperature': 4.0,
            'last_maintenance': datetime.now().isoformat(),
            'errors': [],
            'warnings': []
        }
        
        # 当前交易
        self.current_transaction = None
        
        # 初始化子系统
        self._init_subsystems()
        
        # 线程控制
        self.running = False
        self.main_thread = None
        
        self.logger.info("智能冰柜系统初始化完成")
    
    def _init_subsystems(self):
        """初始化所有子系统"""
        try:
            # 硬件系统
            self.lock_system = LockControlSystem(
                self.config.get('hardware', {}).get('lock_control', {}),
                simulation=self.simulation_mode
            )
            
            self.temp_system = TemperatureControlSystem(
                self.config.get('hardware', {}).get('temperature_control', {}),
                simulation=self.simulation_mode
            )
            
            self.sensor_system = SensorSystem(
                self.config.get('hardware', {}).get('sensors', {}),
                simulation=self.simulation_mode
            )
            
            # 视觉识别系统
            self.vision_system = ProductRecognitionSystem(
                self.config.get('vision', {}),
                simulation=self.simulation_mode
            )
            
            # 支付系统
            self.payment_system = PaymentManager(
                self.config.get('payment', {}),
                simulation=self.simulation_mode
            )
            
            # 云端管理
            self.cloud_manager = CloudManager(
                self.config.get('cloud', {}),
                self.device_id,
                simulation=self.simulation_mode
            )
            
            # 智能补货算法
            self.replenishment_system = ReplenishmentAlgorithm(
                self.config.get('replenishment', {}),
                simulation=self.simulation_mode
            )
            
            # 广告系统
            self.ad_system = AdvertisingSystem(
                self.config.get('advertising', {}),
                simulation=self.simulation_mode
            )
            
            self.logger.info("所有子系统初始化完成")
        except Exception as e:
            self.logger.error(f"初始化子系统失败: {str(e)}")
            raise
    
    def start(self):
        """启动智能冰柜系统"""
        if self.running:
            self.logger.warning("系统已经在运行")
            return
        
        self.logger.info("启动智能冰柜系统...")
        
        try:
            # 启动各子系统
            self.lock_system.start()
            self.temp_system.start()
            self.sensor_system.start()
            self.vision_system.start()
            self.payment_system.start()
            self.cloud_manager.start()
            self.replenishment_system.start()
            self.ad_system.start()
            
            # 连接到云平台
            self.cloud_manager.connect()
            
            # 上报初始状态
            self._update_system_status()
            self.cloud_manager.report_status(self.system_status)
            
            # 启动主线程
            self.running = True
            self.system_status['running'] = True
            self.main_thread = threading.Thread(target=self._main_loop, daemon=True)
            self.main_thread.start()
            
            self.logger.info("智能冰柜系统启动完成")
        except Exception as e:
            self.logger.error(f"启动系统失败: {str(e)}")
            self.stop()
            raise
    
    def stop(self):
        """停止智能冰柜系统"""
        if not self.running:
            self.logger.warning("系统已经停止")
            return
        
        self.logger.info("停止智能冰柜系统...")
        
        # 停止主线程
        self.running = False
        self.system_status['running'] = False
        if self.main_thread and self.main_thread.is_alive():
            self.main_thread.join(timeout=5.0)
        
        # 停止各子系统
        self.ad_system.stop()
        self.replenishment_system.stop()
        self.cloud_manager.stop()
        self.payment_system.stop()
        self.vision_system.stop()
        self.sensor_system.stop()
        self.temp_system.stop()
        self.lock_system.stop()
        
        self.logger.info("智能冰柜系统已停止")
    
    def _main_loop(self):
        """系统主循环"""
        self.logger.info("进入系统主循环")
        
        while self.running:
            try:
                # 检查门锁状态
                self._check_door_status()
                
                # 检查温度状态
                self._check_temperature()
                
                # 检查传感器数据
                self._check_sensors()
                
                # 更新系统状态
                self._update_system_status()
                
                # 上报状态到云平台
                if time.time() % 60 < 1:  # 每分钟上报一次
                    self.cloud_manager.report_status(self.system_status)
                
                # 检查补货需求
                self._check_replenishment()
                
                # 更新广告内容
                self._update_advertisements()
                
                # 休眠一小段时间
                time.sleep(0.1)
            except Exception as e:
                self.logger.error(f"主循环执行出错: {str(e)}")
                time.sleep(1.0)  # 出错后等待较长时间再重试
    
    def _check_door_status(self):
        """检查门锁状态并处理开门/关门事件"""
        # 获取当前门锁状态
        current_door_status = self.lock_system.get_door_status()
        previous_door_status = self.system_status['door_status']
        
        # 状态变化检测
        if current_door_status != previous_door_status:
            self.logger.info(f"门状态变化: {previous_door_status} -> {current_door_status}")
            self.system_status['door_status'] = current_door_status
            
            # 处理开门事件
            if current_door_status == 'open' and previous_door_status == 'closed':
                self._handle_door_open()
            
            # 处理关门事件
            elif current_door_status == 'closed' and previous_door_status == 'open':
                self._handle_door_close()
    
    def _handle_door_open(self):
        """处理开门事件"""
        self.logger.info("处理开门事件")
        
        # 获取开门授权信息
        auth_info = self.lock_system.get_last_auth_info()
        user_id = auth_info.get('user_id', 'unknown')
        auth_method = auth_info.get('auth_method', 'unknown')
        
        # 拍摄开门前的商品状态快照
        before_products = self.vision_system.capture_inventory()
        
        # 创建新交易
        self.current_transaction = {
            'id': f"T{int(time.time())}",
            'user_id': user_id,
            'auth_method': auth_method,
            'start_time': time.time(),
            'before_products': before_products,
            'after_products': None,
            'products_taken': [],
            'total_amount': 0.0,
            'status': 'in_progress'
        }
        
        self.logger.info(f"创建新交易: {self.current_transaction['id']}")
        
        # 更新广告系统，显示个性化内容
        self.ad_system.show_personalized_content(user_id)
    
    def _handle_door_close(self):
        """处理关门事件"""
        self.logger.info("处理关门事件")
        
        # 如果没有进行中的交易，直接返回
        if not self.current_transaction or self.current_transaction['status'] != 'in_progress':
            self.logger.warning("关门时没有进行中的交易")
            return
        
        # 拍摄关门后的商品状态
        after_products = self.vision_system.capture_inventory()
        
        # 计算商品变化
        products_taken = self.vision_system.calculate_product_difference(
            self.current_transaction['before_products'], 
            after_products
        )
        
        # 计算总金额
        total_amount = sum(item['price'] * item['quantity'] for item in products_taken)
        
        # 更新交易信息
        self.current_transaction.update({
            'after_products': after_products,
            'products_taken': products_taken,
            'total_amount': total_amount,
            'end_time': time.time(),
            'status': 'pending'
        })
        
        # 如果有商品被取出，发起支付请求
        if products_taken and total_amount > 0:
            self.logger.info(f"商品已取出，总金额: {total_amount}元，发起支付请求")
            
            # 获取用户ID
            user_id = self.current_transaction['user_id']
            
            # 创建支付请求
            payment_request = self.payment_system.request_payment(
                self.current_transaction['id'],
                user_id,
                total_amount,
                f"智能冰柜购物 - {len(products_taken)}件商品"
            )
            
            self.current_transaction['payment_request'] = payment_request
            
            # 显示支付信息
            self.ad_system.show_payment_info(payment_request)
        else:
            self.logger.info("未检测到商品变化，取消交易")
            self.current_transaction = None
    
    def _check_temperature(self):
        """检查温度状态"""
        # 获取当前温度
        current_temp = self.temp_system.get_current_temperature()
        self.system_status['temperature'] = current_temp
        
        # 检查温度是否在正常范围内
        temp_range = self.config.get('hardware', {}).get('temperature_control', {}).get('range', {})
        min_temp = temp_range.get('min', 2.0)
        max_temp = temp_range.get('max', 8.0)
        
        if current_temp < min_temp:
            self._add_warning(f"温度过低: {current_temp}°C")
        elif current_temp > max_temp:
            self._add_warning(f"温度过高: {current_temp}°C")
    
    def _check_sensors(self):
        """检查传感器数据"""
        # 获取传感器数据
        sensor_data = self.sensor_system.get_all_sensor_data()
        
        # 更新系统状态
        self.system_status.update(sensor_data)
        
        # 检查异常情况
        if sensor_data.get('power_status', {}).get('power_outage', False):
            self._add_error("检测到电源中断")
        
        if sensor_data.get('security', {}).get('intrusion_detected', False):
            self._add_error("检测到入侵尝试")
    
    def _update_system_status(self):
        """更新系统状态"""
        # 更新时间戳
        self.system_status['timestamp'] = time.time()
        
        # 更新位置信息
        location = self.sensor_system.get_location()
        if location:
            self.system_status['location'] = location
        
        # 更新库存信息
        inventory = self.vision_system.get_current_inventory()
        self.system_status['inventory'] = inventory
        
        # 检查支付状态
        if self.current_transaction and self.current_transaction.get('status') == 'pending':
            payment_id = self.current_transaction.get('payment_request', {}).get('id')
            if payment_id:
                payment_status = self.payment_system.check_payment_status(payment_id)
                
                if payment_status.get('status') == 'completed':
                    self._finalize_transaction(payment_status)
    
    def _finalize_transaction(self, payment_status):
        """完成交易"""
        self.logger.info(f"交易 {self.current_transaction['id']} 支付完成")
        
        # 更新交易状态
        self.current_transaction['status'] = 'completed'
        self.current_transaction['payment_details'] = payment_status
        
        # 更新库存
        self._update_inventory(self.current_transaction['products_taken'])
        
        # 上报交易到云平台
        self.cloud_manager.report_transaction(self.current_transaction)
        
        # 更新补货算法数据
        self.replenishment_system.update_sales_data(self.current_transaction)
        
        # 显示交易完成信息
        self.ad_system.show_transaction_complete(self.current_transaction)
        
        # 清除当前交易
        self.current_transaction = None
    
    def _update_inventory(self, products_taken):
        """更新库存信息"""
        for product in products_taken:
            product_id = product['product_id']
            quantity = product['quantity']
            
            # 更新库存
            self.vision_system.update_inventory(product_id, -quantity)
    
    def _check_replenishment(self):
        """检查补货需求"""
        # 获取当前库存
        inventory = self.vision_system.get_current_inventory()
        
        # 检查补货需求
        replenishment_needs = self.replenishment_system.check_replenishment_needs(inventory)
        
        # 如果有补货需求，上报到云平台
        if replenishment_needs:
            self.cloud_manager.report_replenishment_needs(replenishment_needs)
    
    def _update_advertisements(self):
        """更新广告内容"""
        # 获取客流数据
        traffic_data = self.sensor_system.get_traffic_data()
        
        # 更新广告内容
        if traffic_data and traffic_data.get('updated', False):
            self.ad_system.update_content_based_on_traffic(traffic_data)
    
    def _add_error(self, error_message):
        """添加错误信息"""
        timestamp = time.time()
        error = {
            'message': error_message,
            'timestamp': timestamp,
            'resolved': False
        }
        
        # 检查是否已存在相同错误
        for existing_error in self.system_status['errors']:
            if existing_error['message'] == error_message and not existing_error['resolved']:
                return  # 已存在未解决的相同错误
        
        self.system_status['errors'].append(error)
        self.logger.error(error_message)
        
        # 上报错误到云平台
        self.cloud_manager.report_error(error)
    
    def _add_warning(self, warning_message):
        """添加警告信息"""
        timestamp = time.time()
        warning = {
            'message': warning_message,
            'timestamp': timestamp,
            'resolved': False
        }
        
        # 检查是否已存在相同警告
        for existing_warning in self.system_status['warnings']:
            if existing_warning['message'] == warning_message and not existing_warning['resolved']:
                return  # 已存在未解决的相同警告
        
        self.system_status['warnings'].append(warning)
        self.logger.warning(warning_message)
        
        # 上报警告到云平台
        self.cloud_manager.report_warning(warning)


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='智能冰柜系统')
    parser.add_argument('--config', type=str, help='配置文件路径')
    parser.add_argument('--simulation', action='store_true', help='使用模拟模式')
    return parser.parse_args()


if __name__ == "__main__":
    # 解析命令行参数
    args = parse_arguments()
    
    try:
        # 创建并启动智能冰柜系统
        fridge = SmartVendingFridge(config_path=args.config, simulation_mode=args.simulation)
        fridge.start()
        
        # 保持主线程运行
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n接收到终止信号，正在关闭系统...")
        finally:
            fridge.stop()
    except Exception as e:
        logging.critical(f"系统启动失败: {str(e)}")
        sys.exit(1)