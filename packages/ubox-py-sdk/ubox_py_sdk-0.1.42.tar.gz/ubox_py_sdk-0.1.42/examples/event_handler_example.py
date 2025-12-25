#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件自动处理功能使用示例

展示如何使用UBox SDK的事件自动处理功能，包括：
- 批量加载事件自动处理规则
- 启动预设事件自动处理
- 添加自定义事件处理规则
- 同步处理事件
- 清除事件处理规则
"""
import time

from ubox_py_sdk import UBox, OSType, RunMode
from config import get_ubox_config, get_device_config


def main():
    """主函数：演示事件自动处理功能"""
    try:
        # 从配置文件获取UBox配置
        ubox_config = get_ubox_config()
        device_config = get_device_config()
        
        print(f"使用配置: {ubox_config['mode']}")
        print(f"设备UDID: {device_config['default_udid']}")
        print(f"设备类型: {device_config['default_os_type']}")
        
        with UBox(
                mode=RunMode(ubox_config['mode']),
                secret_id=ubox_config.get('secret_id'),
                secret_key=ubox_config.get('secret_key'),
                base_url=ubox_config.get('base_url')
        ) as ubox:
            # 初始化设备
            device = ubox.init_device(
                udid=device_config['default_udid'],
                os_type=OSType(device_config['default_os_type'])
            )

            if not device:
                print("设备初始化失败")
                return

            print("设备初始化成功，开始演示事件自动处理功能...")

            # 示例1: 批量加载事件自动处理规则
            print("\n=== 示例1: 批量加载事件自动处理规则 ===")
            default_rules = [
                # '^(完成|关闭|关闭应用|好|允许|始终允许|好的|确定|确认|安装|下次再说|知道了|同意)$',
                # r'^((?<!不)(忽略|允(\s){0,2}许|同(\s){0,2}意)|继续|清理|稍后|稍后处理|暂不|暂不设置|强制|下一步)$',
                # '^((?i)allow|Sure|SURE|accept|install|done|ok)$',
                # ('(建议.*清理)', '(取消|以后再说|下次再说)'),
                # ('(发送错误报告|截取您的屏幕|是否删除)', '取消'),
                # ('(隐私)', '同意并继续'),
                # ('(隐私)', '同意'),
                # ('(残留文件占用|网络延迟)', '取消'),
                # ('(更新|游戏模式)', '取消'),
                # ('(账号密码存储)', '取消'),
                # ('(出现在其他应用上)', '关闭'),
                # ('(申请获取以下权限)', '(允许|同意)'),
                # ('(获取此设备)', '(仅在使用该应用时允许|允许|同意)'),
                # ('(以下权限|暂不使用)', '^同[\s]{0,2}意'),
                # ('(立即体验|立即升级)', '稍后处理'),
                # ('(前往设置)', '暂不设置'),
                # ('(我知道了)', '我知道了'),
                # ('(去授权)', '去授权'),
                # ('(看看手机通讯录里谁在使用微信.*)', '是'),
                # ('(默认已允许以下所有权限|以下不提示|退出)', '确定'),
                # ('(仅充电|仅限充电|传输文件)', '取消'),
            ]

            # 示例1: 批量加载事件自动处理规则
            print("\n=== 示例1: 批量加载事件自动处理规则 ===")
            try:
                device.load_default_handler(default_rules)
                print("✓ 默认事件处理规则加载成功")
            except Exception as e:
                print(f"✗ 默认事件处理规则加载失败: {e}")

            # 示例2: 启动预设事件自动处理
            print("\n=== 示例2: 启动预设事件自动处理 ===")
            try:
                device.start_event_handler()
                print("✓ 预设事件自动处理启动成功")
            except Exception as e:
                print(f"✗ 预设事件自动处理启动失败: {e}")
            device.get_element("//*[@content-desc='none']")
            # device.start_task()
            # 安装app
            # print(f"启动安装app")
            # result = device.install_app(
            #     app_url="https://lab-paas-apk-1254257443.cos.ap-nanjing.myqcloud.com/paas-app/1754540001432_1049482942918688768.apk"
            # )
            # print(f"安装app: {result}")
            # 卸载app
            # result = device.uninstall_app(
            #     pkg="com.example.demo"
            # )
            # print(f"卸载app: {result}")
            # time.sleep(10)
            # 示例3: 添加自定义事件处理规则
            # print("\n=== 示例3: 添加自定义事件处理规则 ===")
            #
            # # 添加一个简单的规则：当出现"更新"按钮时，点击"稍后处理"
            # try:
            #     device.add_event_handler(
            #         match_element="更新",
            #         action_element="稍后处理"
            #     )
            #     print("✓ 自定义事件处理规则添加成功")
            # except Exception as e:
            #     print(f"✗ 自定义事件处理规则添加失败: {e}")
            #
            # # 添加另一个规则：当出现"权限"相关提示时，点击"允许"
            # try:
            #     device.add_event_handler(
            #         match_element="权限",
            #         action_element="允许"
            #     )
            #     print("✓ 权限相关事件处理规则添加成功")
            # except Exception as e:
            #     print(f"✗ 权限相关事件处理规则添加失败: {e}")



            # 示例5: 清除事件处理规则
            print("\n=== 示例5: 清除事件处理规则 ===")
            try:
                device.clear_event_handler()
                print("✓ 事件处理规则清除成功")
            except Exception as e:
                print(f"✗ 事件处理规则清除失败: {e}")

            print("\n=== 事件自动处理功能演示完成 ===")

    except Exception as e:
        print(f"演示过程中发生错误: {e}")


if __name__ == "__main__":
    print("UBox 事件自动处理功能演示")
    print("=" * 50)
    main()
