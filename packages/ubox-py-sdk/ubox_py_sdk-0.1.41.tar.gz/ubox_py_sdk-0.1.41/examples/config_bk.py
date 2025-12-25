#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
UBox SDK 本地调试配置文件

用于存储UBox SDK的配置信息，包括secret_id、secret_key等敏感信息。
***使用时请将文件名改为config.py***
"""

# UBox SDK 配置
UBOX_CONFIG = {
    # 正常模式配置（用于远程设备访问）
    "normal": {
        "secret_id": "your_secret_id_here",  # 替换为您的实际secret_id
        "secret_key": "your_secret_key_here",  # 替换为您的实际secret_key
        "env": "formal" # formal / test
    },

    # 本地模式配置（用于本地调试）
    "local": {
        "secret_id": None,  # 本地模式不需要secret_id
        "secret_key": None,  # 本地模式不需要secret_key
        "mode": "local",
        "base_url": "127.0.0.1:26000",  # 本地lab-agent地址
        "env": "formal"
    }
}

# 默认使用的配置
DEFAULT_CONFIG = "local"  # 可以改为 "normal" 或 "local"

# 设备配置
DEVICE_CONFIG = {
    "default_udid": "181QGEYK222E3",  # 默认设备UDID
    "default_os_type": "android",  # 默认操作系统类型
    # "auth_code": "auth_code"
}


def get_ubox_config(config_name: str = None) -> dict:
    """
    获取UBox配置

    Args:
        config_name: 配置名称，如果为None则使用默认配置

    Returns:
        dict: 配置字典
    """
    if config_name is None:
        config_name = DEFAULT_CONFIG

    if config_name not in UBOX_CONFIG:
        raise ValueError(f"不支持的配置名称: {config_name}")

    return UBOX_CONFIG[config_name].copy()


def get_device_config() -> dict:
    """
    获取设备配置

    Returns:
        dict: 设备配置字典
    """
    return DEVICE_CONFIG.copy()