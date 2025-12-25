#!/usr/bin/env python3
"""
优测UBox UBox 示例文件

展示三种不同的初始化模式：
1. 调试模式（自动占用设备）- 正常都使用调试模式
2. 调试模式（使用预获取的authCode）- 跳过占用流程
3. 执行模式 - 仅用于自动化脚本上传到平台执行

包含完整的功能演示和时间监控功能。
"""
import json
import re
import sys
import os
import time
import traceback
import uuid
from tkinter import Image

# import xmltodict
from lxml import etree

from examples.config import get_ubox_config, get_device_config
from ubox_py_sdk.device_operations import LogcatTask, FileTransferHandler
from ubox_py_sdk.handler import find_optimal_element, parse_xml, EventHandler

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ubox_py_sdk import UBox, RunMode, OSType, operation_timer
from ubox_py_sdk.models import DeviceButton, DriverType, PinchDirection

# 从配置文件获取UBox配置
ubox_config = get_ubox_config()
device_config = get_device_config()


# ==================== 功能演示函数 ====================
def demo_device_info(device):
    """设备信息相关功能演示"""
    print("\n--- 设备信息相关 ---")
    try:
        with operation_timer("获取设备信息"):
            device_info = device.device_info()
            if device_info:
                print(f"设备型号: {device_info.get('model', 'Unknown')}")
                display = device_info.get('display', {})
                print(f"屏幕分辨率: {display.get('width', 0)}x{display.get('height', 0)}")
            auth_info = device.get_auth_info()
            if auth_info:
                print(f"authCode: {auth_info.get('authCode', 'Unknown')}")
                print(f"udid: {auth_info.get('udid', 'Unknown')}")
    except Exception as e:
        print(f"设备信息获取失败: {e}")


def demo_ui_tree_info(device):
    print("\n--- ui_tree相关 ---")
    try:
        # with operation_timer("获取uitree-xml信息"):
        #     device.ios_open_url(
        #         "https://datong-picture-1258344701.cos.ap-guangzhou.myqcloud.com/scan/dist/index.html?dt_debugid=zhenxichen_17e59a&dt_appid=RUiWu5Po&a_appkey=00000VAFHI3U915P&i_appkey=0P0008DK283CA2PS&h_appkey=0HAR060G0XEC8X4W")
        with operation_timer("获取uitree-json信息"):
            json_xml_tree = device.get_uitree()
            print(f"json_xml_tree: {json_xml_tree}")
        with operation_timer("获取uitree-xml信息"):
            json_xml_tree = device.get_uitree(xml=True)
            print(f"json_xml_tree: {json_xml_tree[:50]}")
        # with operation_timer("find"):
        #     xml_tree = device.find_ui("//*[@text='打开URL']",timeout=10)
        #     print(f"xml_tree: {xml_tree}")
    except Exception as e:
        print(f"ui_tree获取失败: {e}\n{traceback.format_exc()}")


def demo_screenshot_recording(device):
    """截图录制相关功能演示"""
    print("\n--- 截图录制相关 ---")
    try:
        # 截图并下载
        with operation_timer("截图下载"):
            screenshot_result = device.screenshot(label="demo", img_path="./screenshots")
            print(f"截图下载: {screenshot_result}")

        # Base64截图
        with operation_timer("Base64截图"):
            base64_image = device.screenshot_base64()
            print(f"Base64截图长度: {len(base64_image)}")

        # 开始录制
        with operation_timer("开始录制"):
            res = device.record_start(video_path="./recordings/demo.mp4")
            print(f"录制开始: {res}")

        # 停止录制
        time.sleep(5)  # 等待2秒
        with operation_timer("停止录制"):
            record_result = device.record_stop()
            print(f"录制停止: {record_result}")

        # # 截图并裁剪
        # with operation_timer("截图并裁剪"):
        #     screenshot_result = device.screenshot(label="demo", img_path="./screenshots", crop=(0.42, 0.78, 0.58, 0.85))
        #     print(f"截图并裁剪: {screenshot_result}")
        #
        # # Base64截图并裁剪
        # with operation_timer("Base64截图并裁剪"):
        #     base64_image = device.screenshot_base64(crop=(452, 1874,  619, 2032))
        #     print(f"Base64截图并裁剪: {base64_image}")

    except Exception as e:
        print(f"截图录制失败: {e}")


def demo_click_operations(device):
    """点击操作相关功能演示"""
    print("\n--- 点击操作相关 ---")
    try:
        # 坐标点击
        with operation_timer("坐标点击"):
            success = device.click_pos([0.5, 0.5])
            print(f"坐标点击: {success}")
        # 坐标点击
        with operation_timer("坐标点击"):
            success = device.click_pos([724, 2063])
            print(f"坐标点击: {success}")
        #
        # # 双击
        # with operation_timer("双击操作"):
        #     success = device.click_pos([0.5, 0.9], times=2)
        #     print(f"双击: {success}")
        #
        # # 长按
        # with operation_timer("长按操作"):
        #     success = device.click_pos([0.9, 0.1], duration=2.0)
        #     print(f"长按: {success}")
        #
        # # 基于控件点击
        # with operation_timer("控件点击"):
        #     success = device.click(
        #         loc="//*[@content-desc='扫一扫']",
        #         by=DriverType.UI
        #     )
        #     print(f"控件点击: {success}")

        # # 基于图像匹配点击
        # with operation_timer("图像匹配点击"):
        #     success = device.click(
        #         loc="20250919121552_demo_cropped.jpg",
        #         by=DriverType.CV,
        #         timeout=10
        #     )
        #     print(f"图像匹配点击: {success}")

        # # 基于文字识别点击
        # with operation_timer("文字识别点击"):
        #     success = device.click(
        #         loc="登录",
        #         by=DriverType.OCR
        #     )
        #     print(f"文字识别点击: {success}")
        #
        # # 长按操作
        # with operation_timer("长按控件操作"):
        #     success = device.long_click(
        #         loc="//*[@content-desc='扫一扫']",
        #         by=DriverType.UI,
        #         duration=3.0
        #     )
        #     print(f"长按操作: {success}")

    except Exception as e:
        print(f"点击操作失败: {e}")


def demo_slide_operations(device):
    """滑动操作相关功能演示"""
    print("\n--- 滑动操作相关 ---")
    try:
        # 坐标滑动 - 使用绝对坐标
        with operation_timer("左右滑动"):
            success = device.slide_pos([0.1, 0.5], [0.9, 0.5], slide_duration=0.1)
            print(f"左右滑动: {success}")
        time.sleep(1)
        # 坐标滑动 - 使用绝对坐标
        with operation_timer("左右滑动"):
            success = device.slide_pos([0.9, 0.5], [0.1, 0.5], slide_duration=0.1)
            print(f"左右滑动: {success}")

        # with operation_timer("上下滑动"):
        #     success = device.slide_pos([0.5, 0.1], [0.5, 0.9], slide_duration=0.1)
        #     print(f"上下滑动: {success}")

        # # 坐标滑动 - 对角线滑动
        # with operation_timer("对角线滑动"):
        #     success = device.slide_pos([0.1, 0.1], [0.9, 0.9])
        #     print(f"对角线滑动: {success}")
        #
        # # 坐标滑动 - 带拖拽效果
        # with operation_timer("拖拽滑动"):
        #     success = device.slide_pos([0.5, 0.9], [0.5, 0.1], down_duration=0.5)
        #     print(f"拖拽滑动: {success}")

        # # 元素滑动 - 基于控件
        # with operation_timer("控件间滑动"):
        #     success = device.slide(
        #         loc_from="//XCUIElementTypeButton[@label='开始']",
        #         loc_to="//XCUIElementTypeButton[@label='结束']",
        #         by=DriverType.UI
        #     )
        #     print(f"控件间滑动: {success}")
        #
        # # 元素滑动 - 基于图像匹配
        # with operation_timer("图像间滑动"):
        #     success = device.slide(
        #         loc_from="start_image.png",
        #         loc_to="end_image.png",
        #         by=DriverType.CV
        #     )
        #     print(f"图像间滑动: {success}")
        #
        # # 元素滑动 - 基于文字识别
        # with operation_timer("文字间滑动"):
        #     success = device.slide(
        #         loc_from="登录",
        #         loc_to="注册",
        #         by=DriverType.OCR
        #     )
        #     print(f"文字间滑动: {success}")

    except Exception as e:
        print(f"滑动操作失败: {e}")


def demo_pinch_operations(device):
    """双指缩放相关功能演示"""
    print("\n--- 双指缩放相关 ---")
    try:
        # 水平放大：以屏幕中间的矩形区域为缩放区域，进行 1.5 倍放大
        with operation_timer("双指水平放大"):
            success = device.pinch(
                rect=[0.3, 0.3, 0.4, 0.4],              # 中间区域，相对坐标 [x, y, w, h]
                scale=1.5,                               # 放大 1.5 倍
                direction=PinchDirection.HORIZONTAL      # 水平方向
            )
            print(f"双指水平放大: {success}")

        time.sleep(1)

        # 垂直缩小：同一缩放区域内，进行 0.8 倍缩小
        with operation_timer("双指垂直缩小"):
            success = device.pinch(
                rect=[0.3, 0.3, 0.4, 0.4],
                scale=0.8,                               # 缩小到 0.8 倍
                direction=PinchDirection.VERTICAL        # 垂直方向
            )
            print(f"双指垂直缩小: {success}")

    except Exception as e:
        print(f"双指缩放操作失败: {e}")


def demo_text_input(device):
    """文本输入相关功能演示"""
    print("\n--- 文本输入相关 ---")
    try:
        with operation_timer("基本文本输入"):
            success = device.input_text("Hello World")
            print(f"基本文本输入: {success}")

        with operation_timer("带超时文本输入"):
            success = device.input_text("测试文本", timeout=60)
            print(f"带超时文本输入: {success}")

        with operation_timer("调整深度文本输入"):
            success = device.input_text("复杂文本", timeout=30, depth=15)
            print(f"调整深度文本输入: {success}")

    except Exception as e:
        print(f"文本输入失败: {e}")


def demo_key_operations(device):
    """按键操作相关功能演示"""
    print("\n--- 按键操作相关 ---")
    try:
        with operation_timer("返回键"):
            success = device.press(DeviceButton.BACK)
            print(f"返回键: {success}")

        with operation_timer("Home键"):
            success = device.press(DeviceButton.HOME)
            print(f"Home键: {success}")

        with operation_timer("音量上键"):
            success = device.press(DeviceButton.VOLUME_UP)
            print(f"音量上键: {success}")

        with operation_timer("音量下键"):
            success = device.press(DeviceButton.VOLUME_DOWN)
            print(f"音量下键: {success}")

    except Exception as e:
        print(f"按键操作失败: {e}")


def demo_app_management(device):
    """应用管理相关功能演示"""
    print("\n--- 应用管理相关 ---")
    try:
        with operation_timer("当前界面应用"):
            current_app = device.current_app()
            print(f"当前界面应用: {current_app}")
        
        # 获取当前Activity（仅Android和鸿蒙）
        if device.os_type in [OSType.ANDROID, OSType.HM]:
            with operation_timer("当前Activity"):
                current_activity = device.current_activity()
                print(f"当前Activity: {current_activity}")
        else:
            print("当前Activity: 此功能仅支持Android和鸿蒙设备")
        
        with operation_timer("当前运行中app list"):
            app_list_running = device.app_list_running()
            print(f"当前运行中app list: {app_list_running}")
        # if device.os_type == OSType.IOS:
        #     bundle_id = "com.apple.AppStore"
        # else:
        #     bundle_id = "com.wudaokou.hippo"
        #
        # with operation_timer("启动应用"):
        #     success = device.start_app(bundle_id)
        #     print(f"启动应用: {success}")
        #
        # if device.os_type in [OSType.ANDROID, OSType.HM]:
        #     with operation_timer("清除数据启动应用"):
        #         success = device.start_app(bundle_id, clear_data=True)
        #         print(f"清除数据启动: {success}")
        #
        # # 等待应用启动
        # time.sleep(2)
        #
        # # 测试停止应用
        # with operation_timer("停止应用"):
        #     success = device.stop_app(bundle_id)
        #     print(f"停止应用: {success}")

    except Exception as e:
        print(f"应用管理失败: {e}")


def demo_commands(device):
    """cmd命令相关功能演示"""
    print("\n--- cmd命令相关 ---")
    try:
        # with operation_timer("获取设备型号"):
        #     result = device.cmd_adb("getprop ro.product.model")
        #     print(f"设备型号: {result}")
        #
        # with operation_timer("获取当前activity"):
        #     result = device.cmd_adb("dumpsys activity activities | grep mResumedActivity")
        #     print(f"当前activity: {result}")
        #
        # with operation_timer("获取已安装包列表"):
        #     result = device.cmd_adb("pm list packages", timeout=30)
        #     print(f"已安装包数量: {len(str(result).split())}")
        #
        # with operation_timer("获取设备属性"):
        #     result = device.cmd_adb("getprop")
        #     print(f"设备属性数量: {len(str(result).split())}")

        with operation_timer("打开优测网页"):
            result = device.cmd_adb(
                "am start 'txdt00000vafhi3u915p://visual_debug?dt_debugid=zhenxichen_76edf6\&dt_appid=RUiWu5Po'")
            print(f"打开优测网页: {result}")

    except Exception as e:
        print(f"ADB命令失败: {e}")


def demo_init_driver(device):
    """初始化设备操作相关功能演示"""
    print("\n--- 初始化设备操作相关 ---")
    try:
        with operation_timer("初始化设备"):
            success = device.init_driver()
            print(f"初始化设备: {success}")
    except Exception as e:
        print(f"初始化设备操作失败: {e}")


def demo_advanced_features(device):
    """高级功能演示"""
    print("\n--- 高级功能 ---")
    try:
        # # 图像查找
        # with operation_timer("图像查找"):
        #     result = device.find_cv(
        #         tpl="template_image.png",
        #         threshold=0.8,
        #         timeout=30
        #     )
        #     print(f"图像查找: {result}")

        # OCR文字查找
        with operation_timer("OCR文字查找"):
            result = device.find_ocr(
                word="图库",
                timeout=30
            )
            print(f"OCR查找: {result}")

        # UI控件查找
        with operation_timer("UI控件查找"):
            result = device.find_ui(
                xpath="//*[@content-desc='扫一扫']",
                timeout=30
            )
            print(f"UI控件查找: {result}")

        # # 获取控件树
        # with operation_timer("获取控件树"):
        #     result = device.get_uitree(xml=False)
        #     print(f"控件树获取成功，节点数量: {len(str(result))}")

        # # 获取图像文本
        # with operation_timer("图像文本识别"):
        #     result = device.get_text("screenshot.png", iou_th=0.1)
        #     print(f"图像文本识别: {result}")

        # 剪贴板操作
        with operation_timer("设置剪贴板"):
            device.set_clipboard("测试文本")
            print(f"设置剪贴板成功")

        with operation_timer("获取剪贴板"):
            clipboard_text = device.get_clipboard()
            print(f"剪贴板内容: {clipboard_text}")

        # # 等待页面空闲
        # with operation_timer("等待页面空闲"):
        #     result = device.wait_for_idle(idle_time=1.0, timeout=10.0)
        #     print(f"页面空闲状态: {result}")

    except Exception as e:
        print(f"高级功能失败: {e}")


def demo_install_app_features(device):
    """安装卸载功能展示"""
    print("\n--- 安装卸载功能 ---")
    try:

        # default_rules = [
        #     '^(已知悉该应用存在风险｜仍然继续｜授权本次安装|同意)$',
        #     ('(仅充电|仅限充电|传输文件)', '取消'),
        # ]
        # device.load_default_handler(default_rules)
        # device.start_event_handler()
        # 安装app
        with operation_timer("安装app"):
            result = device.install_app(
                app_url="https://utest-upload-file-1254257443.cos.ap-guangzhou.myqcloud.com/user_upload_file_dir/2025-08-28/d365f9a1b2974c2cb75c38fda2750567/TencentVideo_V9.01.65.30262_20563.apk"
            )
            print(f"安装app: {result}")
        time.sleep(3)
        # 卸载app
        with operation_timer("卸载app"):
            result = device.uninstall_app(
                pkg="com.example.demo"
            )
            print(f"卸载app: {result}")

    except Exception as e:
        print(f"安装卸载功能失败: {e}")


def demo_file_transfer_features(device):
    """文件传输相关功能展示 - 包含所有涉及文件传输的功能"""
    print("\n--- 文件传输相关功能展示 ---")

    # 创建测试目录
    test_dir = "./file_transfer_test"
    os.makedirs(test_dir, exist_ok=True)

    try:
        # 1. 截图功能 - 涉及文件传输
        print("\n1. 截图功能测试")
        with operation_timer("截图"):
            screenshot_path = device.screenshot(
                label="test_screenshot",
                img_path=os.path.join(test_dir, "screenshot.png")
            )
            print(f"截图保存到: {screenshot_path}")

        # # 2. 录制功能 - 涉及文件传输
        # print("\n2. 录制功能测试")
        # with operation_timer("开始录制"):
        #     record_result = device.record_start(video_path=os.path.join(test_dir, "test_video.mp4"))
        #     print(f"开始录制: {record_result}")
        #
        # time.sleep(3)  # 录制3秒
        #
        # with operation_timer("停止录制"):
        #     stop_result = device.record_stop()
        #     print(f"停止录制: {stop_result}")
        #
        # # 3. CV点击功能 - 涉及模板图像文件传输
        # print("\n3. CV点击功能测试")
        # # 使用刚才的截图作为模板
        # if os.path.exists(screenshot_path):
        #     with operation_timer("CV点击"):
        #         click_result = device.click(
        #             loc=screenshot_path,
        #             by=DriverType.CV,  # CV类型
        #             timeout=10
        #         )
        #         print(f"CV点击结果: {click_result}")
        #
        # # 4. CV查找功能 - 涉及模板图像文件传输
        # print("\n4. CV查找功能测试")
        # if os.path.exists(screenshot_path):
        #     with operation_timer("CV查找"):
        #         find_result = device.find_cv(
        #             tpl=screenshot_path,
        #             timeout=10,
        #             threshold=0.8
        #         )
        #         print(f"CV查找结果: {find_result}")
        #
        # # 5. CV元素获取功能 - 涉及模板图像文件传输
        # print("\n5. CV元素获取功能测试")
        # if os.path.exists(screenshot_path):
        #     with operation_timer("CV元素获取"):
        #         element_result = device.get_element_cv(
        #             tpl=screenshot_path,
        #             timeout=10,
        #             threshold=0.8
        #         )
        #         print(f"CV元素获取结果: {element_result}")
        #
        # # 6. 性能测试功能 - 涉及文件传输
        # print("\n6. 性能测试功能")
        # with operation_timer("开始性能采集"):
        #     perf_start_result = device.perf_start(
        #         container_bundle_identifier="com.wudaokou.hippo",
        #         log_output_file=os.path.join(test_dir, "perf.log"),
        #         case_name="file_transfer_test"
        #     )
        #     print(f"开始性能采集: {perf_start_result}")
        #
        # time.sleep(3)  # 采集3秒
        #
        # with operation_timer("停止性能采集"):
        #     perf_stop_result = device.perf_stop(output_directory=test_dir)
        #     print(f"停止性能采集: {perf_stop_result}")

        # 7. Logcat日志采集功能 - 涉及文件传输
        print("\n7. Logcat日志采集功能")
        with operation_timer("开始Logcat采集"):
            logcat_task = device.logcat_start(
                file=os.path.join(test_dir, "logcat.log"),
                clear=True
            )
            print(f"开始Logcat采集，任务ID: {logcat_task.task_id}")

        time.sleep(3)  # 采集3秒

        with operation_timer("停止Logcat采集"):
            logcat_stop_result = logcat_task.stop()
            print(f"停止Logcat采集: {logcat_stop_result}")

        # 8. ANR监控功能 - 涉及文件传输
        print("\n8. ANR监控功能")
        with operation_timer("开始ANR监控"):
            anr_start_result = device.anr_start(
                package_name="com.wudaokou.hippo",
                collect_am_monitor=True
            )
            print(f"开始ANR监控: {anr_start_result}")

        time.sleep(3)  # 监控3秒

        with operation_timer("停止ANR监控"):
            anr_stop_result = device.anr_stop(output_directory=test_dir)
            print(f"停止ANR监控: {anr_stop_result}")
            if isinstance(anr_stop_result, dict):
                print(f"ANR监控结果包含文件: {list(anr_stop_result.keys())}")

        # 9. 应用安装功能 - 涉及APK文件传输（如果有APK文件）
        print("\n9. 应用安装功能测试")
        # 注意：这里需要实际的APK文件路径
        apk_path = "qqmusic_64_14.9.0.1_android_ra266691c_20250917222854_release.apk"
        if os.path.exists(apk_path):
            with operation_timer("本地应用安装"):
                install_result = device.local_install_app(
                    local_app_path=apk_path,
                    need_resign=False
                )
                print(f"应用安装结果: {install_result}")
        else:
            print("未找到APK文件，跳过应用安装测试")

    except Exception as e:
        print(f"涉及文件传输的功能测试失败: {e}")
        import traceback
        traceback.print_exc()


def demo_perf_features(device):
    """性能采集功能展示"""
    print("\n--- 性能采集功能 ---")
    try:

        # 开始采集
        with operation_timer("开始采集性能"):
            result = device.perf_start(
                container_bundle_identifier="com.tencent.qqlive",
            )
            print(f"开始采集性能: {result}")
        time.sleep(10)
        # 停止采集性能
        with operation_timer("停止采集性能"):
            result = device.perf_stop("./perf_output")
            print(f"停止采集性能: {result}")
        # 保存性能数据 可以使用停止直接保存
        # with operation_timer("保存性能数据"):
        #     result = device.perf_save_data(output_directory="./perf_output")
        #     print(f"保存性能数据: {result}")

    except Exception as e:
        print(f"性能采集功能失败: {e}")


def demo_logcat_features(device):
    """logcat日志采集功能展示"""
    print("\n--- logcat日志采集功能 ---")
    try:
        # 检查是否为Android或鸿蒙设备
        if device.os_type not in [OSType.ANDROID, OSType.HM]:
            print("logcat功能仅支持Android和鸿蒙设备")
            return

        # 启动logcat采集
        with operation_timer("启动logcat采集"):
            task: LogcatTask = device.logcat_start(
                file="./logcat_output/app_logs.txt",
                clear=True,
                # re_filter=".*python.*"  # 过滤包含python的日志
            )
            print(f"启动logcat采集成功，任务ID: {task.task_id}")
            print(f"任务信息: {task.get_info()}")
            print(f"用户指定保存路径: {task.file_path}")

        print("logcat采集已启动，等待5秒...")
        time.sleep(5)  # 采集5秒日志

        # 停止logcat采集
        with operation_timer("停止logcat采集"):
            stop_result = task.stop()
            print(f"停止logcat采集: {stop_result}")

        if stop_result:
            print(f"logcat日志已保存到: {task.file_path}")
        else:
            print("停止logcat采集失败")

        # # 演示多个logcat任务同时运行
        # print("\n--- 演示多个logcat任务同时运行 ---")
        #
        # # 启动多个不同过滤条件的logcat任务
        # tasks = []
        # task_configs = [
        #     {"file": "./logcat_output/python_logs.txt", "filter": ".*python.*"},
        #     {"file": "./logcat_output/error_logs.txt", "filter": ".*ERROR.*"},
        #     {"file": "./logcat_output/app_logs.txt", "filter": ".*MyApp.*"}
        # ]
        #
        # for i, config in enumerate(task_configs):
        #     with operation_timer(f"启动logcat任务{i + 1}"):
        #         task = device.logcat_start(
        #             file=config["file"],
        #             clear=True,
        #             re_filter=config["filter"]
        #         )
        #         tasks.append(task)
        #         print(f"任务{i + 1}启动成功，ID: {task.task_id}")
        #         print(f"任务{i + 1}保存路径: {task.file_path}")
        #
        # print(f"共启动{len(tasks)}个logcat任务，等待3秒...")
        # time.sleep(3)
        #
        # # 演示任务管理功能
        # print("\n--- 演示任务管理功能 ---")
        # running_tasks = device.logcat_list_tasks()
        # print(f"当前正在运行的任务数量: {len(running_tasks)}")
        # for task in running_tasks:
        #     print(f"  - 任务ID: {task.task_id}, 文件: {task.file_path}")
        #
        # # 方式1：逐个停止任务
        # print("\n--- 逐个停止任务 ---")
        # for i, task in enumerate(tasks):
        #     with operation_timer(f"停止logcat任务{i + 1}"):
        #         stop_result = task.stop()
        #         print(f"任务{i + 1}停止: {stop_result}")
        #         print(f"任务{i + 1}状态: {'运行中' if task.is_running() else '已停止'}")
        #         print(f"任务{i + 1}文件已保存到: {task.file_path}")
        #
        # # 方式2：一次性停止所有任务（演示）
        # print("\n--- 演示一次性停止所有任务 ---")
        # # 重新启动一些任务用于演示
        # demo_tasks = []
        # for i in range(2):
        #     task = device.logcat_start(f"./logcat_output/demo{i}.txt", re_filter=".*demo.*")
        #     demo_tasks.append(task)
        #     print(f"启动演示任务{i + 1}: {task.task_id}")
        #
        # time.sleep(1)

        # 使用全局停止功能
        with operation_timer("停止所有logcat任务"):
            stop_all_result = device.logcat_stop_all()
            print(f"停止所有任务: {stop_all_result}")

        # 验证所有任务都已停止
        final_tasks = device.logcat_list_tasks()
        print(f"停止后剩余任务数量: {len(final_tasks)}")

    except Exception as e:
        print(f"logcat日志采集功能失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")


def demo_anr_features(device):
    """ANR/Crash监控功能展示"""
    print("\n--- ANR/Crash监控功能 ---")
    try:
        # 检查是否为Android或鸿蒙设备
        if device.os_type not in [OSType.ANDROID, OSType.HM]:
            print("ANR监控功能仅支持Android和鸿蒙设备")
            return

        # 启动ANR监控（指定包名）
        with operation_timer("启动ANR/Crash监控"):
            success = device.anr_start(package_name="com.example.app")
            print(f"启动ANR监控: {success}")

        if success:
            print("ANR监控已启动，等待30秒...")
            time.sleep(30)  # 监控10秒

            # 停止ANR监控并下载文件
            with operation_timer("停止ANR/Crash监控"):
                result = device.anr_stop(output_directory="./anr_output")
                print(f"停止ANR监控: {result['success']}")

            if result['success']:
                print(f"监控结果:")
                print(f"  - 运行时间: {result['run_time']:.2f}秒")
                print(f"  - ANR次数: {result['anr_count']}")
                print(f"  - Crash次数: {result['crash_count']}")
                print(f"  - 截图数量: {len(result.get('screenshots', []))}")
                print(f"  - 上下文文件数量: {len(result.get('context_files', []))}")

                if result.get('screenshots'):
                    print(f"  - 截图文件: {result['screenshots']}")
                if result.get('logcat_file'):
                    print(f"  - Logcat文件: {result['logcat_file']}")
                if result.get('am_monitor_file'):
                    print(f"  - AM监控文件: {result['am_monitor_file']}")
            else:
                print("停止ANR监控失败")

    except Exception as e:
        print(f"ANR监控功能失败: {e}")
        import traceback
        print(f"错误详情: {traceback.format_exc()}")


def xml_to_json(device):
    with operation_timer("截图下载"):
        screenshot_result = device.screenshot(label="demo", img_path="./screenshots")
        print(f"截图下载: {screenshot_result}")
    with operation_timer("截图下载"):
        screenshot_result = device.get_uitree()
        with open("./xml.xml", "w") as f:
            f.write(screenshot_result)

    def parse_bounds(bounds):
        match = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds)
        if match:
            return [int(match.group(1)), int(match.group(2)), int(match.group(3)), int(match.group(4))]
        return [0, 0, 0, 0]

    # def parse_node(node):
    #     keep_keys = [
    #         "class", "bounds", "package", "activity", "text", "resource-id", "orientation",
    #         "hint", "textSize", "textColor", "background", "content-desc", "checked",
    #         "selected", "enabled", "focused", "focusable", "clickable"
    #     ]
    #     d = {}
    #     for k, v in node.attrib.items():
    #         if k in keep_keys:
    #             if k == "bounds":
    #                 d[k] = parse_bounds(v)
    #             else:
    #                 d[k] = v
    #
    #     children = [parse_node(child) for child in node if child.tag == "node"]
    #     if children:
    #         d["nodes"] = children
    #     return d

    def parse_node(node):
        d = dict(node.attrib)
        if "bounds" in d:
            d["bounds"] = parse_bounds(d["bounds"])
        children = [parse_node(child) for child in node if child.tag == "node"]
        if children:
            d["nodes"] = children
        return d

    # def parse_bounds(bounds):
    #     nums = list(map(int, re.findall(r'[\d\.]+', bounds)))
    #     if len(nums) == 4:
    #         # Node版是[x, y, width, height]
    #         return [nums[0], nums[1], nums[2] - nums[0], nums[3] - nums[1]]
    #     return [0, 0, 0, 0]

    # def adaptor(node):
    #     d = dict(node.attrib)
    #     if 'bounds' in d:
    #         d['bounds'] = parse_bounds(d['bounds'])
    #     # 保证包名字段存在
    #     d['package'] = d.get('package', None)
    #
    #     children = [adaptor(child) for child in node if child.tag == "node"]
    #     if children:
    #         d['nodes'] = children
    #     return d

    with open('./xml.xml', 'r', encoding='utf-8') as f:
        xml_content = f.read()
    # xml_tree = etree.fromstring(xml_content.encode('utf-8'))
    # json_result = parse_node(xml_tree)
    # json_result = xmltodict.parse(xml_content)

    # candidates = [child for child in xml_tree if
    #               child.tag == 'node' and child.attrib.get('package') != 'com.android.systemui']
    # if not candidates:
    #     raise RuntimeError('No valid node found')
    # matchedNode = candidates[-1]
    # data = adaptor(matchedNode)
    # with open("uitree.json", "w", encoding="utf-8") as f:
    #     json.dump(json_result, f, ensure_ascii=False, indent=2)
    # ui_json = json.dumps(json_result, indent=4, ensure_ascii=False)
    # with open('uitree.json', 'w', encoding='utf-8') as f:
    #     f.write(ui_json)


def handle_common_event(device, xml_element, smart_click):
    """处理通用事件的回调函数"""
    smart_click("已知悉该应用存在风险")
    time.sleep(2)
    smart_click("仍然继续")
    time.sleep(2)
    smart_click("授权本次安装")
    return True


def handle_vivo_event(device, xml_element, smart_click):
    """处理vivo手机事件的回调函数"""
    smart_click("已了解应用的风险检测")
    time.sleep(2)
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


def demo_local_install(device):
    with operation_timer("本地安装测试"):
        res = device.local_install_app(
            "/Users/xutianyi/Documents/lain_code/utest-script/TencentVideo_V9.01.65.30262_20563.apk")
        print(f"本地安装测试: {res}")


def comprehensive_demo(device):
    """完整功能演示 - 调用所有模块的演示函数"""
    print("\n=== 完整功能演示 ===")
    # 调用各个功能模块的演示函数
    # device.press(DeviceButton.HOME)
    # demo_ui_tree_info(device)  # ui相关
    demo_pinch_operations(device)  # 双指缩放相关
    # demo_device_info(device)  # 设备信息相关
    # demo_screenshot_recording(device)  # 截图录制相关
    # demo_click_operations(device)  # 点击操作相关
    # demo_slide_operations(device)  # 滑动操作相关
    # demo_init_driver(device)
    # demo_text_input(device)  # 文本输入相关
    # demo_key_operations(device)  # 按键操作相关
    # demo_app_management(device)  # 应用管理相关
    # demo_commands(device)  # ADB命令相关
    # demo_advanced_features(device)  # 高级功能
    # demo_install_app_features(device)  # 安装卸载
    # demo_local_install(device) # 本地包安装app
    # demo_file_transfer_features(device)  # 文件传输相关功能
    # demo_perf_features(device)  # 性能采集
    # demo_logcat_features(device)  # logcat日志采集
    # demo_anr_features(device)  # ANR/Crash监控
    # xml_to_json(device) # xml 转 json

    # 新增的元素获取功能演示
    # example_get_element_cv(device)  # CV模板匹配获取元素
    # example_get_element_ocr(device)  # OCR文字识别获取元素


# ==================== 三种初始化模式示例 ====================
def demo_debug_mode_auto_occupy():
    try:
        # 创建SDK实例（调试模式）
        ubox = UBox(
            # 使用时按这个注释写
            # secret_id="xxx",
            # secret_key="xxx",
            mode=ubox_config.get("mode", RunMode.NORMAL),
            base_url=ubox_config.get("base_url", ''),
            secret_id=ubox_config.get('secret_id'),
            secret_key=ubox_config.get('secret_key'),
            log_level="debug",
            log_to_file=True
        )

        print("\n正在初始化设备...")
        device = ubox.init_device(
            # 使用时按这个注释写
            # udid="your_device_udid_here",
            # os_type=OSType.ANDROID
            udid=device_config['default_udid'],
            os_type=OSType(device_config['default_os_type']),
            auth_code=device_config.get('auth_code', None),
            # force_proxy=True if ubox.mode == RunMode.NORMAL else False
        )
        print(f"设备初始化成功: {device.udid}")
        print(f"设备类型: {device.os_type.value}")
        print(f"Debug ID: {getattr(device, 'debugId', 'N/A')}")

        comprehensive_demo(device)
        print("\n" + "=" * 80)
        print("注意：设备会自动释放，无需手动操作")
        print("=" * 80)

    except Exception as e:
        print(f"❌ 示例执行失败: {e}\n{traceback.format_exc()}")

    finally:
        # 关闭客户端
        try:
            ubox.close()
            print("SDK已关闭")
        except:
            pass


# ==================== 上下文管理器使用示例 ====================
def demo_context_manager_usage():
    """上下文管理器使用示例 - 推荐的使用方式"""
    print("\n" + "=" * 80)
    print("上下文管理器使用示例")
    print("=" * 80)
    print("使用上下文管理器（with语句）是推荐的使用方式，可以自动管理资源")

    # 示例1：默认模式（自动占用设备）
    print("\n1. 默认模式（自动占用设备）示例：")
    try:
        with UBox(
                # 使用时按这个注释写
                # secret_id="xxx",
                # secret_key="xxx",
                secret_id=ubox_config.get('secret_id'),
                secret_key=ubox_config.get('secret_key'),
        ) as ubox:
            print(f"SDK创建成功，模式: {ubox.mode.value}")

            # 初始化设备
            device = ubox.init_device(
                # 使用时按这个注释写
                # udid="your_device_udid_here",
                # os_type=OSType.ANDROID
                udid=device_config['default_udid'],
                os_type=OSType(device_config['default_os_type']),
            )
            print(f"设备初始化成功: {device.udid}")

            # 执行一些操作
            with operation_timer("获取设备信息"):
                device_info = device.device_info()
                if device_info:
                    print(f"设备型号: {device_info.get('model', 'Unknown')}")

            with operation_timer("截图操作"):
                screenshot_result = device.screenshot("demo", "./screenshots")
                print(f"截图成功: {screenshot_result}")

            print("注意：使用with语句，无需手动调用ubox.close()")

    except Exception as e:
        print(f"❌ 示例执行失败: {e}")

    # 示例2：默认模式（使用预获取的authCode）
    print("\n2. 默认模式（使用预获取的authCode）示例：")
    try:
        with UBox(
                # 使用时按这个注释写
                # secret_id="xxx",
                # secret_key="xxx",
                secret_id=ubox_config.get('secret_id'),
                secret_key=ubox_config.get('secret_key'),
        ) as ubox:
            print(f"SDK创建成功，模式: {ubox.mode.value}")

            # 使用预获取的authCode初始化设备
            device = ubox.init_device(
                # 使用时按这个注释写
                # udid="your_device_udid_here",
                # os_type=OSType.ANDROID
                # auth_code="xxxd2c-8497-15556a0a62f0_20250822142144"
                udid=device_config['default_udid'],
                os_type=OSType(device_config['default_os_type']),
                auth_code=device_config.get('auth_code')
            )
            print(f"设备初始化成功: {device.udid}")

            # 执行一些操作
            with operation_timer("左右滑动"):
                success = device.slide_pos([0.1, 0.5], [0.9, 0.5])
                print(f"左右滑动: {success}")

            print("注意：使用with语句，无需手动调用ubox.close()")

    except Exception as e:
        print(f"❌ 示例执行失败: {e}")

    # 示例3：本地模式
    print("\n3. 本地模式：")
    try:
        with UBox(
                # 使用时按这个注释写
                mode=RunMode.LOCAL,
                # secret_id="your_secret_id_here",
                # secret_key="your_secret_key_here",
                secret_id=ubox_config.get('secret_id'),
                secret_key=ubox_config.get('secret_key'),
        ) as ubox:
            print(f"SDK创建成功，模式: {ubox.mode.value}")

            # 初始化设备
            device = ubox.init_device(
                # 使用时按这个注释写
                # udid="your_device_udid_here",
                # os_type=OSType.ANDROID
                udid=device_config['default_udid'],
                os_type=OSType(device_config['default_os_type'])
            )
            print(f"设备初始化成功: {device.udid}")

            # 执行一些操作
            with operation_timer("获取设备信息"):
                device_info = device.device_info()
                if device_info:
                    print(f"设备型号: {device_info.get('model', 'Unknown')}")

            print("注意：使用with语句，无需手动调用ubox.close()")

    except Exception as e:
        print(f"❌ 示例执行失败: {e}")

    print("\n" + "=" * 80)
    print("上下文管理器示例执行完成！")
    print("总结：使用with语句是推荐的方式，更安全、更简洁")
    print("=" * 80)


# ==================== 主函数 ====================
def main():
    print()
    print(f"使用配置: {ubox_config['mode']}")
    print(f"设备UDID: {device_config['default_udid']}")
    print(f"设备类型: {device_config['default_os_type']}")
    print(f"auto_code: {device_config.get('auth_code', '')}")
    print()
    # 运行上下文管理器示例（推荐）
    # demo_context_manager_usage()
    demo_debug_mode_auto_occupy()


def example_get_element_cv(device):
    """基于CV模板匹配获取元素示例"""
    print("\n=== 基于CV模板匹配获取元素示例 ===")

    try:
        # 基本用法：使用模板图片查找元素
        template_path = "img.png"  # 模板图片路径
        result = device.get_element_cv(
            tpl=template_path,
            timeout=20,
            threshold=0.8,
            to_gray=True,
        )

        if result and 'bounds' in result:
            bounds = result['bounds']
            print(f"找到元素，边界: {bounds}")
            print(f"中心点: ({(bounds[0] + bounds[2]) // 2}, {(bounds[1] + bounds[3]) // 2})")
        else:
            print("未找到匹配的元素")

        # 高级用法：使用更多参数
        advanced_result = device.get_element_cv(
            tpl=template_path,
            timeout=20,
            threshold=0.7,
            ratio_lv=25,  # 更大的缩放范围
            is_translucent=False,  # 非半透明图像
            to_gray=True,  # 转换为灰度图匹配
            crop_box=[0, 0, 1, 0.5],  # 只在屏幕上半部分查找
            time_interval=1.0  # 每秒查找一次
        )

        if advanced_result:
            print(f"高级查找结果: {advanced_result}")

    except Exception as e:
        print(f"CV元素查找失败: {e}")


def example_get_element_ocr(device):
    """基于OCR文字识别获取元素示例"""
    print("\n=== 基于OCR文字识别获取元素示例 ===")

    try:
        # 基本用法：查找指定文字
        result = device.get_element_ocr(
            word="扫一扫",
            timeout=10
        )

        if result and 'bounds' in result:
            bounds = result['bounds']
            print(f"找到文字'扫一扫'，边界: {bounds}")
            print(f"中心点: ({(bounds[0] + bounds[2]) // 2}, {(bounds[1] + bounds[3]) // 2})")
        else:
            print("未找到指定文字")

        # 高级用法：使用裁剪区域
        cropped_result = device.get_element_ocr(
            word="设置",
            crop_box=[0, 1, 0, 0.5],  # 只在屏幕下半部分查找（排除上半部分）
            timeout=20
        )

        if cropped_result:
            print(f"裁剪区域查找结果: {cropped_result}")

    except Exception as e:
        print(f"OCR元素查找失败: {e}")


if __name__ == "__main__":
    main()
