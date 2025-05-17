#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
二维码扫描模块
"""

import os
import time
import threading
import random
import cv2
import numpy as np
from datetime import datetime

from src.utils.logger import get_logger

logger = get_logger('qr_scanner')

# 尝试导入pyzbar库
try:
    from pyzbar.pyzbar import decode
    PYZBAR_AVAILABLE = True
    logger.info("成功导入pyzbar库")
except ImportError:
    logger.warning("pyzbar库导入失败，将使用模拟二维码扫描")
    PYZBAR_AVAILABLE = False


class QRScanner:
    """二维码扫描器类"""
    
    def __init__(self, camera_id=0, scan_interval=0.5, simulation=False):
        """
        初始化二维码扫描器
        
        Args:
            camera_id (int): 摄像头ID
            scan_interval (float): 扫描间隔（秒）
            simulation (bool): 是否使用模拟模式
        """
        self.camera_id = camera_id
        self.scan_interval = scan_interval
        self.simulation = simulation or not PYZBAR_AVAILABLE
        
        # 扫描状态
        self.last_scan_result = None
        self.last_scan_time = 0
        
        # 线程控制
        self.running = False
        self.scan_thread = None
        self.camera = None
        
        logger.info(f"二维码扫描器初始化完成，{'模拟' if self.simulation else '实际'}模式")
    
    def start(self):
        """启动扫描器"""
        if self.running:
            logger.warning("二维码扫描器已经在运行")
            return
        
        try:
            # 如果不是模拟模式，打开摄像头
            if not self.simulation:
                self.camera = cv2.VideoCapture(self.camera_id)
                if not self.camera.isOpened():
                    logger.error(f"无法打开摄像头 {self.camera_id}，切换到模拟模式")
                    self.simulation = True
                else:
                    # 设置摄像头参数
                    self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            # 启动扫描线程
            self.running = True
            self.scan_thread = threading.Thread(target=self._scan_loop, daemon=True)
            self.scan_thread.start()
            
            logger.info("二维码扫描器启动完成")
        except Exception as e:
            logger.error(f"启动二维码扫描器失败: {str(e)}")
            self.stop()
    
    def stop(self):
        """停止扫描器"""
        self.running = False
        
        # 等待线程结束
        if self.scan_thread and self.scan_thread.is_alive():
            self.scan_thread.join(timeout=2.0)
        
        # 释放摄像头
        if self.camera:
            self.camera.release()
            self.camera = None
        
        logger.info("二维码扫描器停止完成")
    
    def check_scan(self):
        """
        检查是否有新的扫描结果
        
        Returns:
            dict: 扫描结果
        """
        result = {
            'detected': False,
            'data': None,
            'timestamp': time.time()
        }
        
        # 如果有最近的扫描结果且未过期（3秒内有效）
        if (self.last_scan_result and 
            time.time() - self.last_scan_time < 3.0):
            result['detected'] = True
            result['data'] = self.last_scan_result
            
            # 使用后清除结果，避免重复使用
            self.last_scan_result = None
        
        return result
    
    def _scan_loop(self):
        """扫描循环线程"""
        logger.info("启动二维码扫描循环")
        
        if self.simulation:
            self._simulate_scan()
        else:
            self._real_scan()
    
    def _real_scan(self):
        """实际扫描循环"""
        while self.running:
            try:
                # 捕获一帧图像
                ret, frame = self.camera.read()
                if not ret:
                    logger.warning("无法从摄像头读取图像")
                    time.sleep(1.0)
                    continue
                
                # 解码二维码
                decoded_objects = decode(frame)
                for obj in decoded_objects:
                    # 获取二维码数据
                    qr_data = obj.data.decode('utf-8')
                    logger.info(f"扫描到二维码: {qr_data}")
                    
                    # 保存扫描结果
                    self.last_scan_result = qr_data
                    self.last_scan_time = time.time()
                    
                    # 在图像上标记二维码位置
                    points = obj.polygon
                    if len(points) > 4:
                        hull = cv2.convexHull(np.array([point for point in points]))
                        cv2.polylines(frame, [hull], True, (0, 255, 0), 2)
                    else:
                        for j in range(4):
                            cv2.line(frame, points[j], points[(j+1) % 4], (0, 255, 0), 2)
                
                # 显示处理后的图像（调试用）
                # cv2.imshow("QR Scanner", frame)
                # cv2.waitKey(1)
                
                # 休眠一段时间
                time.sleep(self.scan_interval)
            except Exception as e:
                logger.error(f"二维码扫描出错: {str(e)}")
                time.sleep(1.0)  # 出错后等待较长时间再重试
    
    def _simulate_scan(self):
        """模拟扫描循环"""
        logger.info("使用模拟二维码扫描模式")
        
        # 预定义的用户ID列表
        user_ids = ["user1001", "user2002", "user3003", "user4004", "user5005"]
        
        while self.running:
            try:
                # 随机模拟扫描到二维码
                if random.random() < 0.05:  # 5%的概率扫描到二维码
                    # 随机选择一个用户ID
                    user_id = random.choice(user_ids)
                    timestamp = int(time.time())
                    signature = "SIMULATED"
                    
                    # 生成二维码数据
                    qr_data = f"USER:{user_id}:{timestamp}:{signature}"
                    
                    logger.info(f"模拟扫描到二维码: {qr_data}")
                    
                    # 保存扫描结果
                    self.last_scan_result = qr_data
                    self.last_scan_time = time.time()
                
                # 休眠一段时间
                time.sleep(self.scan_interval)
            except Exception as e:
                logger.error(f"模拟二维码扫描出错: {str(e)}")
                time.sleep(1.0)  # 出错后等待较长时间再重试