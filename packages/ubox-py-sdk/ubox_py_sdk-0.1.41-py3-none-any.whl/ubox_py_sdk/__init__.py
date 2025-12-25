"""
优测Python UBox

提供与优测设备通信的Python接口。
支持调试模式和执行模式两种运行方式。
"""

from .client import UBox, operation_timer
from .device import Device
from .device_operations import LogcatTask
from .handler import EventHandler
from .models import OSType, RunMode, DeviceButton, DriverType, PhonePlatform
from .jwt_util import JWTUtil

__version__ = "0.1.38"

# 核心类
__all__ = [
    # 主要类
    "UBox",  # 主客户端类
    "Device",  # 设备类

    # 枚举类型
    "OSType",  # 操作系统类型 (ANDROID, IOS, HM)
    "RunMode",  # 运行模式 (DEBUG, EXECUTE)
    "DeviceButton",  # 按键操作
    "DriverType",  # 面向用户的驱动类型参数

    "PhonePlatform",  # 设备列表指定设备类型时使用

    "operation_timer",
    "EventHandler",
    "LogcatTask",
]
