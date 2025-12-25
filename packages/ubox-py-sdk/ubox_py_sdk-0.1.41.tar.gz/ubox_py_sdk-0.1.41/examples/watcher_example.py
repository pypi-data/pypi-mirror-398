#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Watcher功能使用示例

展示如何使用新的watcher功能，类似于u2的watcher能力
"""
import time

from examples.config import get_ubox_config, get_device_config
from ubox_py_sdk import UBox, OSType, operation_timer, DriverType, RunMode

# 从配置文件获取UBox配置
ubox_config = get_ubox_config()
device_config = get_device_config()


def handle_common_event(device, xml_element, smart_click):
    """处理通用事件的回调函数"""
    smart_click("已知悉该应用存在风险")
    smart_click("授权本次安装")
    return True


def handle_vivo_event(device, xml_element, smart_click):
    """处理vivo手机事件的回调函数"""
    smart_click("已了解应用的风险检测")
    smart_click("继续安装")
    return True


def auto_input(device, xml_element, smart_click):
    """自动输入的回调函数"""
    print("Event occurred: auto_input")
    # 模拟输入密码
    device.input_text("mqq@2005")
    # 使用智能点击方法
    smart_click("安装")
    smart_click("继续")
    # 等待4秒
    import time
    time.sleep(4)
    # 点击指定坐标
    device.click_pos([0.521, 0.946])
    return True


def auto_press(device, xml_element, smart_click):
    """自动按键的回调函数"""
    print("Event occurred: auto_press")
    # 点击指定坐标
    device.click_pos([0.521, 0.946])
    return True


def demo_watcher_usage():
    """演示watcher功能的使用"""
    print("=== Watcher功能演示 ===")
    print("新功能：支持智能点击，类似find_optimal_element的智能匹配")
    print("在call函数中可以使用smart_click(text)进行智能文本匹配和点击")
    print("新功能：支持一个watcher多个条件，使用链式调用")
    print("例如：watcher('允许').when('允许').when('允许访问一次').click()")
    print()

    try:
        with UBox(
                mode=ubox_config.get("mode", RunMode.NORMAL),
                base_url=ubox_config.get("base_url", ''),
                secret_id=ubox_config.get('secret_id'),
                secret_key=ubox_config.get('secret_key'),
                env=ubox_config.get('env'),
        ) as ubox:
            # 初始化设备
            device = ubox.init_device(
                udid=device_config['default_udid'],
                os_type=OSType(device_config['default_os_type']),
                auth_code=device_config.get('auth_code', None),
            )
            print(f"设备初始化成功: {device.udid}")

            # 获取设备信息
            device_info = device.device_info()
            if device_info:
                print(f"设备型号: {device_info.get('model', 'Unknown')}")

            # 配置watcher
            print("\n配置watcher...")

            # 重置所有watcher配置
            event_handler = device.handler
            event_handler.reset()
            # 配置各种watcher
            # event_handler.watcher("wsq1").when("已知悉该应用存在风险").call(handle_common_event)
            # event_handler.watcher("wsq2").when("已了解应用的风险检测").call(handle_vivo_event)
            # event_handler.watcher("wsq3").when('//*[@resource-id="com.oplus.appdetail:id/et_login_passwd_edit"]').call(
            #     auto_input)
            # event_handler.watcher("wsq4").when(
            #     '//*[@resource-id="com.coloros.safecenter:id/et_login_passwd_edit"]').call(auto_input)
            #
            # # 配置一些额外的watcher来处理常见的弹窗
            # event_handler.watcher("安装权限").when("安装权限").call(handle_common_event)
            # event_handler.watcher("风险检测").when("风险检测").call(handle_vivo_event)
            #
            # # 配置点击类型的watcher（支持多个条件）
            # event_handler.watcher("始终允许").when("始终允许").click()
            # event_handler.watcher("允许").when("允许").when("允许访问一次").click()
            # event_handler.watcher("升级").when('//*[@content-desc="关闭弹窗"]').click()
            #
            # # OPPO手机继续安装
            # event_handler.watcher("oppo安装").when(
            #     '//*[@resource-id="com.android.packageinstaller:id/confirm_bottom_button_layout"]').click()
            #
            # # 特殊处理
            # if device_info and device_info.get("productName") in ["MT2110_CH", "RMX3357"]:
            #     event_handler.watcher("一加安装").when(
            #         '//*[@resource-id="com.android.packageinstaller:id/install_confirm_panel"]').call(auto_press)
            #
            # # 小米手机继续安装
            # event_handler.watcher("继续安装").when("继续安装").click()
            # event_handler.watcher("同意").when("同意").click()
            # event_handler.watcher("同意并继续").when("同意并继续").click()
            #
            # # 微视相关
            # event_handler.watcher("微视更新弹窗").when("//*[@resource-id='com.tencent.weishi:id/rfh']").click()
            # event_handler.watcher("我知道了").when("我知道了").click()
            #
            # # 其他通用处理
            # event_handler.watcher("暂不").when("暂不").click()
            # event_handler.watcher("关闭").when("关闭").click()
            # event_handler.watcher("完成").when("完成").click()
            # event_handler.watcher("确定").when("确定").click()
            # event_handler.watcher("稍后").when("稍后").click()
            # event_handler.watcher("安装").when("安装").click()
            event_handler.watcher("授权本次安装").with_match_mode("strict").when("授权本次安装").click()

            print(f"已配置 {len(event_handler.watchers)} 个watcher")

            # 显示watcher状态
            status = event_handler.get_watcher_status()
            print(f"监控状态: {'运行中' if status['running'] else '已停止'}")
            print(f"监控间隔: {status['monitor_interval']}秒")

            # 开始后台监控
            print("\n开始后台监控...")
            event_handler.start(2.0)  # 每2秒检查一次

            # 再次显示状态
            status = event_handler.get_watcher_status()
            print(f"监控状态: {'运行中' if status['running'] else '已停止'}")

            # # 安装app
            # with operation_timer("安装app"):
            #     result = device.install_app(
            #         app_url="https://lab-paas-apk-1254257443.cos.ap-nanjing.myqcloud.com/paas-app/1754540001432_1049482942918688768.apk"
            #     )
            #     print(f"安装app: {result}")
            # try:
            #     while True:
            #         time.sleep(1)
            # except KeyboardInterrupt:
            #     print("\n收到停止信号")
            #
            # # 卸载app
            # with operation_timer("卸载app"):
            #     result = device.uninstall_app(
            #         pkg="com.example.demo"
            #     )
            #     print(f"卸载app: {result}")
            time.sleep(5)
            # 停止监控
            event_handler.stop()
            print("监控已停止")

    except Exception as e:
        print(f"❌ 示例执行失败: {e}")


if __name__ == "__main__":
    demo_watcher_usage()
