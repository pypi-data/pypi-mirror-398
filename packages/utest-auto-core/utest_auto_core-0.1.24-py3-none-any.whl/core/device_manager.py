"""
设备管理模块

提供UBox设备管理功能，直接暴露UBox设备对象
"""

import logging
import os
import traceback
from typing import Dict, Optional, Any
from ubox_py_sdk import UBox, OSType
from .config_manager import DeviceConfig


logger = logging.getLogger(__name__)


class DeviceManager:
    """设备管理器 - 直接暴露UBox设备对象"""
    
    def __init__(self, ubox_config: Dict[str, Any]):
        """
        初始化设备管理器
        
        Args:
            ubox_config: UBox配置信息
        """
        self.ubox_config = ubox_config
        self.ubox: Optional[UBox] = None
        self.devices: Dict[str, Any] = {}
        
    def initialize_ubox(self, log_file_path: str = None) -> None:
        """
        初始化UBox连接
        
        Args:
            log_file_path: 日志文件路径，如果提供则UBox日志将输出到该文件
        """
        try:
            # 构建UBox初始化参数
            ubox_params = {
                'secret_id': self.ubox_config['secret_id'],
                'secret_key': self.ubox_config['secret_key'],
                'mode': self.ubox_config['mode'],
            }
            
            # 如果提供了日志文件路径，配置UBox日志输出
            if log_file_path:
                ubox_params['log_to_file'] = True
                ubox_params['log_file_path'] = log_file_path
                logger.info(f"UBox日志将输出到: {log_file_path}")

            self.ubox = UBox(**ubox_params)
            logger.info("UBox初始化成功")
        except Exception as e:
            logger.error(f"UBox初始化失败: {e}\n{traceback.format_exc()}")
            raise
    
    def get_device(self, device_config: DeviceConfig):
        """
        获取UBox设备对象（直接暴露，不封装）
        
        Args:
            device_config: 设备配置
            
        Returns:
            UBox设备对象
        """
        if not self.ubox:
            self.initialize_ubox()
        
        device_key = f"{device_config.udid}_{device_config.os_type.value}"
        
        if device_key in self.devices:
            return self.devices[device_key]
        
        try:

            # 初始化设备
            device = self.ubox.init_device(
                udid=device_config.udid,
                os_type=device_config.os_type,
                auth_code=device_config.auth_code,
            )

            if device:
                self.devices[device_key] = device
                logger.info(f"设备初始化成功: {device_config.udid} ({device_config.os_type.value})")
                return device
            else:
                raise Exception(f"设备初始化失败: {device_config.udid}")
                
        except Exception as e:
            logger.error(f"获取设备失败: {e}\n{traceback.format_exc()}")
            raise
    
    def release_device(self, device_config: DeviceConfig) -> None:
        """
        释放设备
        
        Args:
            device_config: 设备配置
        """
        device_key = f"{device_config.udid}_{device_config.os_type.value}"
        
        if device_key in self.devices:
            try:
                device = self.devices[device_key]
                device.release()
                logger.info(f"设备已释放: {device_config.udid}")
            except Exception as e:
                logger.error(f"释放设备失败: {e}\n{traceback.format_exc()}")
            finally:
                del self.devices[device_key]
    
    def release_all_devices(self) -> None:
        """释放所有设备"""
        for device_key in list(self.devices.keys()):
            try:
                device = self.devices[device_key]
                device.release()
                logger.info(f"设备已释放: {device_key}")
            except Exception as e:
                logger.error(f"释放设备失败 {device_key}: {e}\n{traceback.format_exc()}")
        
        self.devices.clear()
    
    def close(self) -> None:
        """关闭设备管理器"""
        self.release_all_devices()
        if self.ubox:
            try:
                # 先尝试关闭UBox连接
                if hasattr(self.ubox, 'close'):
                    self.ubox.close()
                elif hasattr(self.ubox, 'release'):
                    self.ubox.release()
                logger.info("UBox连接已关闭")
            except Exception as e:
                logger.error(f"关闭UBox连接失败: {e}\n{traceback.format_exc()}")
        
        # 清空设备字典
        self.devices.clear()
        self.ubox = None
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()
