#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
温度控制模块
"""

import time
import threading
import random
import math
from datetime import datetime, timedelta

from src.utils.logger import get_logger

logger = get_logger('temperature_control')


class TemperatureControlSystem:
    """温度控制系统类"""
    
    def __init__(self, config=None, simulation=False):
        """
        初始化温度控制系统
        
        Args:
            config (dict, optional): 温度控制配置
            simulation (bool, optional): 是否使用模拟模式
        """
        self.config = config or {}
        self.simulation = simulation
        
        # 温度控制配置
        self.target_temperature = self.config.get('target_temperature', 4.0)
        self.min_temperature = self.config.get('range', {}).get('min', 2.0)
        self.max_temperature = self.config.get('range', {}).get('max', 5.0)
        self.cooling_technology = self.config.get('cooling_technology', 'semiconductor')
        self.power_saving_mode = self.config.get('power_saving_mode', True)
        self.defrost_interval = self.config.get('defrost_interval', 12)  # 小时
        
        # 温度状态
        self.current_temperature = self.target_temperature
        self.compressor_running = False
        self.defrost_mode = False
        self.last_defrost_time = datetime.now() - timedelta(hours=self.defrost_interval)  # 初始化为需要除霜
        
        # 模拟参数
        if simulation:
            self.ambient_temperature = 25.0  # 环境温度
            self.cooling_rate = 0.05  # 制冷速率
            self.heating_rate = 0.02  # 升温速率
            self.temperature_noise = 0.1  # 温度波动
        
        # 线程控制
        self.running = False
        self.control_thread = None
        
        logger.info(f"温度控制系统初始化完成，目标温度: {self.target_temperature}°C")
    
    def start(self):
        """启动温度控制系统"""
        if self.running:
            logger.warning("温度控制系统已经在运行")
            return
        
        self.running = True
        
        # 启动温度控制线程
        self.control_thread = threading.Thread(target=self._temperature_control_loop, daemon=True)
        self.control_thread.start()
        
        logger.info("温度控制系统启动完成")
    
    def stop(self):
        """停止温度控制系统"""
        if not self.running:
            logger.warning("温度控制系统已经停止")
            return
        
        self.running = False
        
        # 等待线程结束
        if self.control_thread and self.control_thread.is_alive():
            self.control_thread.join(timeout=2.0)
        
        logger.info("温度控制系统停止完成")
    
    def get_current_temperature(self):
        """
        获取当前温度
        
        Returns:
            float: 当前温度（摄氏度）
        """
        return self.current_temperature
    
    def set_target_temperature(self, temperature):
        """
        设置目标温度
        
        Args:
            temperature (float): 目标温度（摄氏度）
        
        Returns:
            bool: 是否设置成功
        """
        if temperature < 0 or temperature > 10:
            logger.warning(f"目标温度超出范围: {temperature}°C")
            return False
        
        self.target_temperature = temperature
        logger.info(f"设置目标温度: {temperature}°C")
        return True
    
    def get_status(self):
        """
        获取温度控制系统状态
        
        Returns:
            dict: 状态信息
        """
        return {
            'current_temperature': self.current_temperature,
            'target_temperature': self.target_temperature,
            'compressor_running': self.compressor_running,
            'defrost_mode': self.defrost_mode,
            'power_saving_mode': self.power_saving_mode,
            'last_defrost_time': self.last_defrost_time.isoformat()
        }
    
    def toggle_power_saving_mode(self):
        """
        切换节能模式
        
        Returns:
            bool: 节能模式状态
        """
        self.power_saving_mode = not self.power_saving_mode
        logger.info(f"{'启用' if self.power_saving_mode else '禁用'}节能模式")
        return self.power_saving_mode
    
    def start_defrost(self):
        """
        启动除霜
        
        Returns:
            bool: 是否启动成功
        """
        if self.defrost_mode:
            logger.warning("除霜已经在进行")
            return False
        
        self.defrost_mode = True
        self.compressor_running = False
        self.last_defrost_time = datetime.now()
        
        logger.info("启动除霜")
        return True
    
    def _temperature_control_loop(self):
        """温度控制循环"""
        logger.info("启动温度控制循环")
        
        defrost_timer = 0  # 除霜计时器（秒）
        
        while self.running:
            try:
                # 获取当前时间
                now = datetime.now()
                
                # 检查是否需要除霜
                hours_since_last_defrost = (now - self.last_defrost_time).total_seconds() / 3600
                if not self.defrost_mode and hours_since_last_defrost >= self.defrost_interval:
                    self.start_defrost()
                
                # 除霜模式处理
                if self.defrost_mode:
                    defrost_timer += 1
                    
                    # 除霜持续30分钟
                    if defrost_timer >= 1800:  # 30分钟 * 60秒
                        self.defrost_mode = False
                        defrost_timer = 0
                        logger.info("除霜完成")
                    
                    # 除霜期间温度上升
                    if self.simulation:
                        self.current_temperature += self.heating_rate * 2
                        if self.current_temperature > 8.0:
                            self.current_temperature = 8.0
                else:
                    # 正常温度控制
                    if self.simulation:
                        self._simulate_temperature_control()
                    else:
                        self._real_temperature_control()
                
                # 休眠一段时间
                time.sleep(1.0)
            except Exception as e:
                logger.error(f"温度控制循环出错: {str(e)}")
                time.sleep(5.0)  # 出错后等待较长时间再重试
    
    def _simulate_temperature_control(self):
        """模拟温度控制"""
        # 添加随机波动
        noise = (random.random() - 0.5) * self.temperature_noise
        
        # 根据压缩机状态更新温度
        if self.compressor_running:
            # 制冷
            self.current_temperature -= self.cooling_rate + noise
            
            # 达到目标温度下限时关闭压缩机
            if self.current_temperature <= self.target_temperature - 0.5:
                self.compressor_running = False
                logger.debug(f"关闭压缩机，当前温度: {self.current_temperature:.1f}°C")
        else:
            # 自然升温
            self.current_temperature += self.heating_rate + noise
            
            # 达到目标温度上限时开启压缩机
            if self.current_temperature >= self.target_temperature + 0.5:
                self.compressor_running = True
                logger.debug(f"开启压缩机，当前温度: {self.current_temperature:.1f}°C")
        
        # 节能模式下，减慢制冷速率
        if self.power_saving_mode and self.compressor_running:
            self.current_temperature -= self.cooling_rate * 0.2  # 额外的制冷效果减少
        
        # 确保温度在合理范围内
        self.current_temperature = max(min(self.current_temperature, 10.0), 0.0)
        
        # 记录异常温度
        if self.current_temperature < self.min_temperature:
            logger.warning(f"温度过低: {self.current_temperature:.1f}°C")
        elif self.current_temperature > self.max_temperature:
            logger.warning(f"温度过高: {self.current_temperature:.1f}°C")
    
    def _real_temperature_control(self):
        """实际温度控制"""
        # TODO: 实现实际硬件温度控制
        # 这里应该读取实际温度传感器数据，并控制制冷系统
        
        # 暂时使用模拟实现
        self._simulate_temperature_control()