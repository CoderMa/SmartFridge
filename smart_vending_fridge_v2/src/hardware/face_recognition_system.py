#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
人脸识别模块
"""

import os
import time
import threading
import random
import cv2
import numpy as np
from datetime import datetime

from src.utils.logger import get_logger

logger = get_logger('face_recognition')

# 尝试导入人脸识别库
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
    logger.info("成功导入face_recognition库")
except ImportError:
    logger.warning("face_recognition库导入失败，将使用模拟人脸识别")
    FACE_RECOGNITION_AVAILABLE = False


class FaceRecognitionSystem:
    """人脸识别系统类"""
    
    def __init__(self, camera_id=0, scan_interval=0.5, model_type='hog', simulation=False):
        """
        初始化人脸识别系统
        
        Args:
            camera_id (int): 摄像头ID
            scan_interval (float): 扫描间隔（秒）
            model_type (str): 人脸检测模型类型，'hog'（CPU）或'cnn'（GPU）
            simulation (bool): 是否使用模拟模式
        """
        self.camera_id = camera_id
        self.scan_interval = scan_interval
        self.model_type = model_type
        self.simulation = simulation or not FACE_RECOGNITION_AVAILABLE
        
        # 人脸数据库
        self.known_face_encodings = []
        self.known_face_names = []
        
        # 扫描状态
        self.last_face_result = None
        self.last_face_time = 0
        
        # 线程控制
        self.running = False
        self.scan_thread = None
        self.camera = None
        
        # 加载人脸数据库
        self._load_face_database()
        
        logger.info(f"人脸识别系统初始化完成，{'模拟' if self.simulation else '实际'}模式")
    
    def _load_face_database(self):
        """加载人脸数据库"""
        if self.simulation:
            # 模拟数据
            self.known_face_names = ["user1001", "user2002", "user3003", "user4004", "user5005"]
            logger.info(f"加载模拟人脸数据库: {len(self.known_face_names)} 个用户")
            return
        
        if not FACE_RECOGNITION_AVAILABLE:
            logger.warning("face_recognition库不可用，无法加载实际人脸数据库")
            return
        
        try:
            # 人脸数据库目录
            face_db_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                'data', 'faces'
            )
            
            if not os.path.exists(face_db_dir):
                logger.warning(f"人脸数据库目录不存在: {face_db_dir}")
                os.makedirs(face_db_dir, exist_ok=True)
                return
            
            # 遍历目录加载人脸图像
            for filename in os.listdir(face_db_dir):
                if filename.endswith(('.jpg', '.jpeg', '.png')):
                    # 文件名格式: user_id.jpg
                    user_id = os.path.splitext(filename)[0]
                    image_path = os.path.join(face_db_dir, filename)
                    
                    # 加载图像并编码
                    face_image = face_recognition.load_image_file(image_path)
                    face_encodings = face_recognition.face_encodings(face_image)
                    
                    if face_encodings:
                        self.known_face_encodings.append(face_encodings[0])
                        self.known_face_names.append(user_id)
                        logger.debug(f"加载用户人脸: {user_id}")
            
            logger.info(f"加载人脸数据库完成: {len(self.known_face_names)} 个用户")
        except Exception as e:
            logger.error(f"加载人脸数据库失败: {str(e)}")
    
    def start(self):
        """启动人脸识别系统"""
        if self.running:
            logger.warning("人脸识别系统已经在运行")
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
            
            logger.info("人脸识别系统启动完成")
        except Exception as e:
            logger.error(f"启动人脸识别系统失败: {str(e)}")
            self.stop()
    
    def stop(self):
        """停止人脸识别系统"""
        self.running = False
        
        # 等待线程结束
        if self.scan_thread and self.scan_thread.is_alive():
            self.scan_thread.join(timeout=2.0)
        
        # 释放摄像头
        if self.camera:
            self.camera.release()
            self.camera = None
        
        logger.info("人脸识别系统停止完成")
    
    def detect_face(self):
        """
        检查是否有人脸识别结果
        
        Returns:
            dict: 识别结果
        """
        result = {
            'detected': False,
            'user_id': None,
            'confidence': 0.0,
            'timestamp': time.time()
        }
        
        # 如果有最近的识别结果且未过期（3秒内有效）
        if (self.last_face_result and 
            time.time() - self.last_face_time < 3.0):
            result['detected'] = True
            result['user_id'] = self.last_face_result['user_id']
            result['confidence'] = self.last_face_result['confidence']
            
            # 使用后清除结果，避免重复使用
            self.last_face_result = None
        
        return result
    
    def _scan_loop(self):
        """扫描循环线程"""
        logger.info("启动人脸识别扫描循环")
        
        if self.simulation:
            self._simulate_face_recognition()
        else:
            self._real_face_recognition()
    
    def _real_face_recognition(self):
        """实际人脸识别循环"""
        if not FACE_RECOGNITION_AVAILABLE:
            logger.error("face_recognition库不可用，无法进行实际人脸识别")
            self.simulation = True
            self._simulate_face_recognition()
            return
        
        while self.running:
            try:
                # 捕获一帧图像
                ret, frame = self.camera.read()
                if not ret:
                    logger.warning("无法从摄像头读取图像")
                    time.sleep(1.0)
                    continue
                
                # 缩小图像以加快处理速度
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                rgb_small_frame = small_frame[:, :, ::-1]  # BGR转RGB
                
                # 检测人脸位置
                face_locations = face_recognition.face_locations(rgb_small_frame, model=self.model_type)
                
                if face_locations:
                    # 编码检测到的人脸
                    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
                    
                    for face_encoding in face_encodings:
                        # 与已知人脸比较
                        matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                        face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                        
                        if len(face_distances) > 0:
                            best_match_index = np.argmin(face_distances)
                            confidence = 1.0 - face_distances[best_match_index]
                            
                            # 如果匹配度足够高
                            if matches[best_match_index] and confidence > 0.6:
                                user_id = self.known_face_names[best_match_index]
                                logger.info(f"识别到用户: {user_id}, 置信度: {confidence:.2f}")
                                
                                # 保存识别结果
                                self.last_face_result = {
                                    'user_id': user_id,
                                    'confidence': confidence
                                }
                                self.last_face_time = time.time()
                                
                                # 在图像上标记人脸
                                for (top, right, bottom, left) in face_locations:
                                    # 放大回原始尺寸
                                    top *= 4
                                    right *= 4
                                    bottom *= 4
                                    left *= 4
                                    
                                    # 绘制人脸框
                                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                                    
                                    # 绘制用户ID
                                    cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 255, 0), cv2.FILLED)
                                    cv2.putText(frame, user_id, (left + 6, bottom - 6), 
                                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 1)
                
                # 显示处理后的图像（调试用）
                # cv2.imshow("Face Recognition", frame)
                # cv2.waitKey(1)
                
                # 休眠一段时间
                time.sleep(self.scan_interval)
            except Exception as e:
                logger.error(f"人脸识别出错: {str(e)}")
                time.sleep(1.0)  # 出错后等待较长时间再重试
    
    def _simulate_face_recognition(self):
        """模拟人脸识别"""
        logger.info("使用模拟人脸识别模式")
        
        while self.running:
            try:
                # 随机模拟识别到人脸
                if random.random() < 0.05:  # 5%的概率识别到人脸
                    # 随机选择一个用户ID
                    user_id = random.choice(self.known_face_names)
                    confidence = random.uniform(0.7, 0.95)
                    
                    logger.info(f"模拟识别到用户: {user_id}, 置信度: {confidence:.2f}")
                    
                    # 保存识别结果
                    self.last_face_result = {
                        'user_id': user_id,
                        'confidence': confidence
                    }
                    self.last_face_time = time.time()
                
                # 休眠一段时间
                time.sleep(self.scan_interval)
            except Exception as e:
                logger.error(f"模拟人脸识别出错: {str(e)}")
                time.sleep(1.0)  # 出错后等待较长时间再重试