#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设备列表示例 - 展示如何使用新的模型类

此示例展示了如何使用PhonePlatform枚举和DeviceListRequest/DeviceListResponse模型
来获取设备列表。
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.ubox_py_sdk.client import UBox
from src.ubox_py_sdk.models import PhonePlatform
from src.ubox_py_sdk.exceptions import UBoxError
from config import get_ubox_config


def main():
    try:
        # 从配置文件获取UBox配置
        ubox_config = get_ubox_config()

        with UBox(
                secret_id=ubox_config.get('secret_id'),
                secret_key=ubox_config.get('secret_key'),
        ) as ubox:
            try:
                android_devices = ubox.device_list(
                    page_num=1,
                    page_size=10,
                    phone_platform=[PhonePlatform.ANDROID]
                )
                print(f"   找到 {android_devices.total} 台Android设备")
                for device in android_devices.list[:3]:  # 只显示前3台
                    print(f"   - {device.manufacturer} {device.modelKind} (udid: {device.udid})")
            except UBoxError as e:
                print(f"   获取Android设备失败: {e}")
    except Exception as e:
        print(f"演示过程中发生错误: {e}")


if __name__ == "__main__":
    exit(main())
