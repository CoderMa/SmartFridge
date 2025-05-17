#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
广告投放系统模块
"""

import os
import time
import json
import threading
import random
from datetime import datetime

from src.utils.logger import get_logger

logger = get_logger('ad_system')


class AdvertisingSystem:
    """广告投放系统类"""
    
    def __init__(self, config=None, simulation=False):
        """
        初始化广告投放系统
        
        Args:
            config (dict, optional): 配置字典
            simulation (bool, optional): 是否使用模拟模式
        """
        self.config = config or {}
        self.simulation = simulation
        
        # 广告配置
        self.display_type = self.config.get('display_type', 'touch_screen')
        self.content_update_interval = self.config.get('content_update_interval', 3600)
        self.personalization = self.config.get('personalization', True)
        
        # 广告内容路径
        self.default_content_path = self.config.get('default_content_path', 'data/ads/default')
        self.campaign_config_path = self.config.get('campaign_config_path', 'data/ads/campaigns.json')
        
        # 确保路径是绝对路径
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.default_content_path = os.path.join(base_dir, self.default_content_path)
        self.campaign_config_path = os.path.join(base_dir, self.campaign_config_path)
        
        # 广告内容
        self.current_content = None
        self.campaigns = []
        self.user_preferences = {}
        
        # 线程控制
        self.running = False
        self.ad_thread = None
        
        # 加载广告活动
        self._load_campaigns()
        
        # 加载用户偏好
        self._load_user_preferences()
        
        logger.info(f"广告投放系统初始化完成，显示类型: {self.display_type}")
    
    def _load_campaigns(self):
        """加载广告活动"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.campaign_config_path), exist_ok=True)
            
            if os.path.exists(self.campaign_config_path):
                with open(self.campaign_config_path, 'r', encoding='utf-8') as f:
                    self.campaigns = json.load(f)
                logger.info(f"加载广告活动: {len(self.campaigns)} 个")
            else:
                # 创建默认广告活动
                self.campaigns = [
                    {
                        'id': 'default_campaign',
                        'name': '默认广告活动',
                        'start_time': time.time(),
                        'end_time': time.time() + 365 * 24 * 3600,  # 一年后结束
                        'priority': 1,
                        'target_audience': 'all',
                        'content': [
                            {
                                'type': 'image',
                                'path': 'data/ads/default/default_ad.jpg',
                                'duration': 10
                            },
                            {
                                'type': 'video',
                                'path': 'data/ads/default/default_video.mp4',
                                'duration': 30
                            }
                        ]
                    }
                ]
                
                # 保存默认广告活动
                with open(self.campaign_config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.campaigns, f, ensure_ascii=False, indent=2)
                
                logger.info("创建默认广告活动")
            
            # 确保默认广告内容目录存在
            os.makedirs(self.default_content_path, exist_ok=True)
            
            # 创建默认广告图片（如果不存在）
            default_image = os.path.join(self.default_content_path, 'default_ad.jpg')
            if not os.path.exists(default_image):
                self._create_default_ad_image(default_image)
        except Exception as e:
            logger.error(f"加载广告活动失败: {str(e)}")
            self.campaigns = []
    
    def _create_default_ad_image(self, path):
        """
        创建默认广告图片
        
        Args:
            path (str): 图片路径
        """
        try:
            # 尝试使用PIL创建默认图片
            from PIL import Image, ImageDraw, ImageFont
            
            # 创建一个彩色图像
            img = Image.new('RGB', (800, 600), color=(73, 109, 137))
            
            # 创建绘图对象
            d = ImageDraw.Draw(img)
            
            # 添加文字
            text = "智能冰柜 - 便捷购物体验"
            
            # 尝试加载字体
            try:
                font = ImageFont.truetype("arial.ttf", 36)
            except:
                font = ImageFont.load_default()
            
            # 计算文本位置
            text_width, text_height = d.textsize(text, font=font)
            position = ((800 - text_width) // 2, (600 - text_height) // 2)
            
            # 绘制文本
            d.text(position, text, fill=(255, 255, 255), font=font)
            
            # 保存图片
            img.save(path)
            
            logger.info(f"创建默认广告图片: {path}")
        except Exception as e:
            logger.error(f"创建默认广告图片失败: {str(e)}")
    
    def _load_user_preferences(self):
        """加载用户偏好"""
        try:
            user_prefs_path = os.path.join(os.path.dirname(self.campaign_config_path), 'user_preferences.json')
            
            if os.path.exists(user_prefs_path):
                with open(user_prefs_path, 'r', encoding='utf-8') as f:
                    self.user_preferences = json.load(f)
                logger.info(f"加载用户偏好: {len(self.user_preferences)} 个用户")
            else:
                self.user_preferences = {}
        except Exception as e:
            logger.error(f"加载用户偏好失败: {str(e)}")
            self.user_preferences = {}
    
    def _save_user_preferences(self):
        """保存用户偏好"""
        try:
            user_prefs_path = os.path.join(os.path.dirname(self.campaign_config_path), 'user_preferences.json')
            
            # 确保目录存在
            os.makedirs(os.path.dirname(user_prefs_path), exist_ok=True)
            
            with open(user_prefs_path, 'w', encoding='utf-8') as f:
                json.dump(self.user_preferences, f, ensure_ascii=False, indent=2)
            
            logger.debug("保存用户偏好")
        except Exception as e:
            logger.error(f"保存用户偏好失败: {str(e)}")
    
    def start(self):
        """启动广告投放系统"""
        if self.running:
            logger.warning("广告投放系统已经在运行")
            return
        
        self.running = True
        
        # 启动广告线程
        self.ad_thread = threading.Thread(target=self._ad_loop, daemon=True)
        self.ad_thread.start()
        
        logger.info("广告投放系统启动完成")
    
    def stop(self):
        """停止广告投放系统"""
        if not self.running:
            logger.warning("广告投放系统已经停止")
            return
        
        self.running = False
        
        # 等待线程结束
        if self.ad_thread and self.ad_thread.is_alive():
            self.ad_thread.join(timeout=2.0)
        
        # 保存用户偏好
        self._save_user_preferences()
        
        logger.info("广告投放系统停止完成")
    
    def show_personalized_content(self, user_id):
        """
        显示个性化内容
        
        Args:
            user_id (str): 用户ID
        """
        if not self.personalization:
            self.show_default_content()
            return
        
        try:
            # 获取用户偏好
            user_prefs = self.user_preferences.get(user_id, {})
            
            # 如果没有用户偏好，使用默认内容
            if not user_prefs:
                self.show_default_content()
                return
            
            # 根据用户偏好选择广告
            preferred_categories = user_prefs.get('preferred_categories', [])
            
            # 筛选符合用户偏好的广告活动
            matching_campaigns = []
            for campaign in self.campaigns:
                # 检查活动是否有效
                if not self._is_campaign_active(campaign):
                    continue
                
                # 检查目标受众
                target_audience = campaign.get('target_audience', 'all')
                if target_audience != 'all' and user_id not in target_audience.split(','):
                    continue
                
                # 检查类别匹配
                campaign_categories = campaign.get('categories', [])
                if not campaign_categories or any(cat in preferred_categories for cat in campaign_categories):
                    matching_campaigns.append(campaign)
            
            # 如果没有匹配的活动，使用默认内容
            if not matching_campaigns:
                self.show_default_content()
                return
            
            # 按优先级排序
            matching_campaigns.sort(key=lambda c: c.get('priority', 0), reverse=True)
            
            # 选择最高优先级的活动
            selected_campaign = matching_campaigns[0]
            
            # 显示广告内容
            self._display_campaign_content(selected_campaign)
            
            logger.info(f"为用户 {user_id} 显示个性化广告: {selected_campaign.get('name')}")
        except Exception as e:
            logger.error(f"显示个性化内容失败: {str(e)}")
            self.show_default_content()
    
    def show_default_content(self):
        """显示默认内容"""
        try:
            # 查找默认广告活动
            default_campaign = None
            for campaign in self.campaigns:
                if campaign.get('id') == 'default_campaign':
                    default_campaign = campaign
                    break
            
            # 如果没有默认活动，使用第一个活动
            if not default_campaign and self.campaigns:
                default_campaign = self.campaigns[0]
            
            # 如果有活动，显示内容
            if default_campaign:
                self._display_campaign_content(default_campaign)
                logger.info(f"显示默认广告: {default_campaign.get('name')}")
            else:
                logger.warning("没有可用的广告活动")
        except Exception as e:
            logger.error(f"显示默认内容失败: {str(e)}")
    
    def show_payment_info(self, payment_request):
        """
        显示支付信息
        
        Args:
            payment_request (dict): 支付请求
        """
        try:
            # 获取支付信息
            payment_id = payment_request.get('id', '')
            amount = payment_request.get('amount', 0.0)
            payment_codes = payment_request.get('payment_codes', {})
            
            # 构建支付信息内容
            content = {
                'type': 'payment',
                'payment_id': payment_id,
                'amount': amount,
                'payment_codes': payment_codes,
                'timestamp': time.time()
            }
            
            # 显示支付信息
            self.current_content = content
            
            # 模拟显示
            if self.simulation:
                logger.info(f"显示支付信息: 支付ID {payment_id}, 金额 {amount}元")
                
                # 显示可用的支付方式
                for method, code in payment_codes.items():
                    logger.info(f"  - {method}: {code.get('instructions', '')}")
            else:
                # 实际显示逻辑
                # TODO: 实现实际显示逻辑
                pass
        except Exception as e:
            logger.error(f"显示支付信息失败: {str(e)}")
    
    def show_transaction_complete(self, transaction):
        """
        显示交易完成信息
        
        Args:
            transaction (dict): 交易信息
        """
        try:
            # 获取交易信息
            transaction_id = transaction.get('id', '')
            total_amount = transaction.get('total_amount', 0.0)
            products_taken = transaction.get('products_taken', [])
            
            # 构建交易完成内容
            content = {
                'type': 'transaction_complete',
                'transaction_id': transaction_id,
                'total_amount': total_amount,
                'products_count': len(products_taken),
                'timestamp': time.time()
            }
            
            # 显示交易完成信息
            self.current_content = content
            
            # 模拟显示
            if self.simulation:
                logger.info(f"显示交易完成信息: 交易ID {transaction_id}, 金额 {total_amount}元, {len(products_taken)}件商品")
                
                # 显示商品列表
                for product in products_taken:
                    name = product.get('name', 'Unknown')
                    quantity = product.get('quantity', 0)
                    price = product.get('price', 0.0)
                    logger.info(f"  - {name} x {quantity}: {price * quantity}元")
            else:
                # 实际显示逻辑
                # TODO: 实现实际显示逻辑
                pass
            
            # 3秒后恢复默认内容
            threading.Timer(3.0, self.show_default_content).start()
            
            # 更新用户偏好
            self._update_user_preferences(transaction)
        except Exception as e:
            logger.error(f"显示交易完成信息失败: {str(e)}")
    
    def update_content_based_on_traffic(self, traffic_data):
        """
        根据客流数据更新广告内容
        
        Args:
            traffic_data (dict): 客流数据
        """
        try:
            # 获取客流量
            count = traffic_data.get('count', 0)
            
            # 根据客流量选择广告活动
            if count > 10:  # 高客流
                target_audience = 'high_traffic'
            elif count > 5:  # 中客流
                target_audience = 'medium_traffic'
            else:  # 低客流
                target_audience = 'low_traffic'
            
            # 筛选符合客流量的广告活动
            matching_campaigns = []
            for campaign in self.campaigns:
                # 检查活动是否有效
                if not self._is_campaign_active(campaign):
                    continue
                
                # 检查目标受众
                campaign_audience = campaign.get('target_audience', 'all')
                if campaign_audience == 'all' or target_audience in campaign_audience.split(','):
                    matching_campaigns.append(campaign)
            
            # 如果没有匹配的活动，使用默认内容
            if not matching_campaigns:
                self.show_default_content()
                return
            
            # 按优先级排序
            matching_campaigns.sort(key=lambda c: c.get('priority', 0), reverse=True)
            
            # 选择最高优先级的活动
            selected_campaign = matching_campaigns[0]
            
            # 显示广告内容
            self._display_campaign_content(selected_campaign)
            
            logger.info(f"根据客流量({count})更新广告内容: {selected_campaign.get('name')}")
        except Exception as e:
            logger.error(f"根据客流数据更新广告内容失败: {str(e)}")
    
    def _is_campaign_active(self, campaign):
        """
        检查广告活动是否有效
        
        Args:
            campaign (dict): 广告活动
        
        Returns:
            bool: 是否有效
        """
        now = time.time()
        start_time = campaign.get('start_time', 0)
        end_time = campaign.get('end_time', float('inf'))
        
        return start_time <= now <= end_time
    
    def _display_campaign_content(self, campaign):
        """
        显示广告活动内容
        
        Args:
            campaign (dict): 广告活动
        """
        # 获取内容列表
        content_list = campaign.get('content', [])
        
        # 如果没有内容，返回
        if not content_list:
            logger.warning(f"广告活动 {campaign.get('name')} 没有内容")
            return
        
        # 随机选择一个内容
        content = random.choice(content_list)
        
        # 显示内容
        self.current_content = {
            'campaign_id': campaign.get('id'),
            'campaign_name': campaign.get('name'),
            'content': content,
            'timestamp': time.time()
        }
        
        # 模拟显示
        if self.simulation:
            content_type = content.get('type', 'unknown')
            content_path = content.get('path', '')
            logger.info(f"显示广告内容: {campaign.get('name')}, 类型: {content_type}, 路径: {content_path}")
        else:
            # 实际显示逻辑
            # TODO: 实现实际显示逻辑
            pass
    
    def _update_user_preferences(self, transaction):
        """
        更新用户偏好
        
        Args:
            transaction (dict): 交易信息
        """
        user_id = transaction.get('user_id')
        if not user_id or user_id == 'unknown':
            return
        
        products_taken = transaction.get('products_taken', [])
        if not products_taken:
            return
        
        # 获取用户偏好
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = {
                'preferred_categories': [],
                'purchase_history': [],
                'last_update': time.time()
            }
        
        user_prefs = self.user_preferences[user_id]
        
        # 更新购买历史
        purchase = {
            'timestamp': time.time(),
            'products': []
        }
        
        for product in products_taken:
            product_id = product.get('product_id')
            category = product.get('category', 'Unknown')
            
            purchase['products'].append({
                'product_id': product_id,
                'category': category,
                'quantity': product.get('quantity', 0)
            })
            
            # 更新偏好类别
            if category not in user_prefs['preferred_categories']:
                user_prefs['preferred_categories'].append(category)
        
        # 添加到购买历史
        user_prefs['purchase_history'].append(purchase)
        
        # 限制历史记录数量
        max_history = 20
        if len(user_prefs['purchase_history']) > max_history:
            user_prefs['purchase_history'] = user_prefs['purchase_history'][-max_history:]
        
        # 更新时间
        user_prefs['last_update'] = time.time()
        
        # 定期保存用户偏好
        if random.random() < 0.1:  # 10%的概率保存
            self._save_user_preferences()
    
    def _ad_loop(self):
        """广告循环线程"""
        logger.info("启动广告循环线程")
        
        last_update_time = 0
        
        while self.running:
            try:
                current_time = time.time()
                
                # 定期更新广告内容
                if current_time - last_update_time > self.content_update_interval:
                    self.show_default_content()
                    last_update_time = current_time
                
                # 休眠一段时间
                time.sleep(1.0)
            except Exception as e:
                logger.error(f"广告循环出错: {str(e)}")
                time.sleep(5.0)  # 出错后等待较长时间再重试