#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
智能售卖柜主程序
"""

import os
import sys
import logging
import argparse
from datetime import datetime

# 添加项目根目录到系统路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.config_manager import ConfigManager
from src.utils.logger import setup_logger
from src.vision.product_recognition import ProductRecognition
from src.payment.payment_manager import PaymentManager


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='智能售卖柜控制系统')
    parser.add_argument('--config', type=str, help='配置文件路径')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    args = parser.parse_args()
    
    # 设置日志
    log_level = logging.DEBUG if args.debug else logging.INFO
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f'smart_vending_fridge_{datetime.now().strftime("%Y-%m-%d")}.log')
    setup_logger(log_level, log_file)
    
    logging.info("智能售卖柜控制系统启动")
    
    try:
        # 初始化配置管理器
        config_manager = ConfigManager(args.config)
        logging.info("配置管理器初始化完成")
        
        # 初始化商品识别系统
        product_recognition = ProductRecognition(config_manager)
        logging.info("商品识别系统初始化完成")
        
        # 初始化支付管理器
        payment_manager = PaymentManager(config_manager)
        logging.info("支付管理器初始化完成")
        
        # 启动主控制器
        # main_controller = MainController(config_manager)
        # main_controller.start()
        # logging.info("主控制器启动完成")
        
        # 保持程序运行
        logging.info("系统运行中，按 Ctrl+C 退出...")
        while True:
            pass
    except KeyboardInterrupt:
        logging.info("接收到退出信号，系统正在关闭...")
        # if main_controller:
        #     main_controller.stop()
    except Exception as e:
        logging.error(f"系统运行异常: {str(e)}")
    finally:
        logging.info("智能售卖柜控制系统已关闭")


if __name__ == "__main__":
    main()