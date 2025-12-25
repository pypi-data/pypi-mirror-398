"""
优测 UBox 设备管理模块

提供设备连接、管理和操作功能。
使用组合模式，通过持有sdk引用来调用client中的方法。
"""
import os
import threading
import time
import re
from typing import Dict, Any, TYPE_CHECKING, Union, Optional, List, Tuple
from .common_util import crop_base64_image, crop_image_save

from .exceptions import UBoxDeviceError
from .handler import EventHandler
from .models import *
from .logger import get_logger
from .device_operations import (
    ScreenshotOperation,
    ScreenshotBase64Operation,
    RecordStartOperation,
    RecordStopOperation,
    CmdAdbOperation,
    DeviceInfoOperation,
    ClickPosOperation,
    SlidePosOperation,
    ClickOperation,
    InputTextOperation,
    PressOperation,
    SlideOperation,
    InstallAppOperation,
    UninstallAppOperation,
    StartAppOperation,
    StopAppOperation,
    FindCVOperation,
    FindOCROperation,
    FindUIOperation,
    FindOperation,
    MultiFindOperation,
    GetUITreeOperation,
    GetElementOperation,
    GetElementsOperation,
    GetTextOperation,
    SetClipboardOperation,
    GetClipboardOperation,
    SetHttpGlobalProxyOperation,
    GetHttpGlobalProxyOperation,
    ClearHttpGlobalProxyOperation,
    GetFilePathInfoOperation,
    WaitForIdleOperation,
    LoadDefaultHandlerOperation,
    StartEventHandlerOperation,
    AddEventHandlerOperation,
    SyncEventHandlerOperation,
    ClearEventHandlerOperation, ScreenSizeOperation,
    CreateRemoteDirOperation,
    IOSOpenUrlHelper,
    CurrentAppOperation,
    CurrentActivityOperation,
    ClearSafariOperation,
    AppListRunningOperation, LocalInstallAppOperation, CleanDeviceDirOperation,
    PerfStartOperation,
    PerfStopOperation,
    PerfSaveDataOperation,
    LogcatStartOperation,
    LogcatTask,
    ANRStartOperation,
    ANRStopOperation,
    GetElementCVOperation,
    GetElementOCROperation,
    InitDriverOperation,
    PinchOperation
)

if TYPE_CHECKING:
    from .client import UBox

try:
    from haitest.utils.event import StopEvent
except ImportError:
    # 如果 haitest 不可用，定义一个简单的替代类
    class StopEvent:
        def stop(self):
            pass

logger = get_logger(__name__)


class Device:
    """设备对象。

    通过 `UBox.init_device()` 获取实例。封装对单个设备的各类操作。

    支持两种运行模式：
    1. 正常模式：优先尝试直接连接，如果无法连接则回退到代理访问，支持设备占用、释放和续期
    2. 本地模式：直接连接本地地址，无需设备占用和续期，用于本地调试
    """

    # 类型注解声明
    handler: 'EventHandler'

    def __init__(self, ubox: 'UBox', udid: str, os_type: OSType, client_addr: str, auth_code: str,
                 debug_id: Optional[str],
                 mode: RunMode, use_proxy: bool = False) -> None:
        """
        初始化设备对象
        
        Args:
            ubox: UBox实例的引用
            udid: 设备唯一标识
            os_type: 设备操作系统类型
            client_addr: 设备的实际访问地址
            auth_code: 设备的认证码，用于后续请求
            debug_id: 调试模式的debugId，用于续期和释放
            mode: 运行模式
            use_proxy: 是否使用代理访问
        """
        self._ubox = ubox  # 持有sdk引用，用于调用client中的方法
        self.udid = udid
        self.os_type = os_type
        self.client_addr = client_addr  # 设备的实际访问地址
        self.authCode = auth_code  # 设备的认证码，用于后续请求
        self.debugId = debug_id  # 调试模式的debugId，用于续期和释放
        self.mode = mode  # 运行模式：RunMode.NORMAL 或 RunMode.LOCAL
        self.use_proxy = use_proxy  # 是否使用代理访问
        self.handler: EventHandler = EventHandler(self)
        self.d_screen_size = None
        # 录制相关
        self.video_path = None
        self.client_video_path = None

        # 性能测试输出
        self.perf_case_name = None

        # logcat任务管理
        self._logcat_tasks: Dict[str, 'LogcatTask'] = {}  # 注册的logcat任务

        # 正常模式：启动定时续期任务（仅当通过占用获取到debugId时）
        self._renewal_thread = None
        self._stop_renewal = False

        # 异步自动关弹窗
        self._event_thread = None
        self._stop_event = False

        if self.mode == RunMode.NORMAL and self.debugId:
            self._start_renewal_task()
        elif self.mode == RunMode.NORMAL and not self.debugId and self.authCode:
            logger.info(f"正常模式使用提供的authCode，跳过续期任务")
        elif self.mode == RunMode.LOCAL:
            logger.info(f"本地模式，跳过续期任务")

    def _stop_all_task(self):
        """停止所有异步任务"""
        self._stop_renewal_task()
        # self._stop_event_task()

    # def _start_event_task(self):
    #     def event_worker():
    #         """异步监控工作线程"""
    #         while not self._stop_event:
    #             # 获取一个没有的元素 触发弹窗关闭
    #             self.get_element("//*[@content-desc='*$*none']")
    #             time.sleep(2)
    #         logger.info(f"设备 {self.udid} 异步关弹窗任务已停止")
    #
    #     self._event_thread = threading.Thread(target=event_worker, daemon=True)
    #     self._event_thread.start()
    #     logger.info(f"设备 {self.udid} 异步监控任务已启动")
    #
    # def _stop_event_task(self):
    #     """停止异步监控任务"""
    #     if self._event_thread:
    #         self._stop_event = True
    #         # 等待线程停止，但设置超时避免无限等待
    #         if self._event_thread.is_alive():
    #             self._event_thread.join(timeout=5)
    #             if self._event_thread.is_alive():
    #                 logger.warning(f"设备 {self.udid} 异步监控任务停止超时")
    #         self._event_thread = None
    #         logger.info(f"设备 {self.udid} 异步监控任务已停止")

    def _start_renewal_task(self):
        """启动定时续期任务，每120秒调用一次续期接口"""

        def renewal_worker():
            while not self._stop_renewal:
                try:
                    # 调用续期接口 - 通过sdk引用调用client中的方法
                    renewal_payload = {
                        "debugId": self.debugId,
                        "serialNumber": self.udid,
                        "projectId": self._ubox.project_uuid,
                        "zone": "zone_dalian"  # 这里可能需要从配置中获取
                    }

                    # 通过sdk引用调用make_request方法
                    self._ubox.make_request('POST', '/cloudphone/expire', data=renewal_payload,
                                            base_url=self._ubox._paas_base_url)
                    logger.debug(f"设备 {self.udid} 续期成功")

                except Exception as e:
                    logger.warning(f"设备 {self.udid} 续期失败: {e}")
                # 等待2分钟
                time.sleep(120)

        self._renewal_thread = threading.Thread(target=renewal_worker, daemon=True)
        self._renewal_thread.start()
        logger.info(f"设备 {self.udid} 定时续期任务已启动")

    def _stop_renewal_task(self):
        """停止定时续期任务"""
        if self._renewal_thread:
            self._stop_renewal = True
            self._renewal_thread.join(timeout=5)
            self._renewal_thread = None
            logger.info(f"设备 {self.udid} 定时续期任务已停止")

    def release(self):
        """释放该设备"""
        try:
            # 停止定时续期任务
            self._stop_all_task()
            try:
                # 清理临时文件目录
                self.clean_remote_device_dir()
            except Exception as e:
                logger.warning(f"设备 {self.udid} 清理临时文件目录失败: {e}")
            if self.debugId:
                try:
                    stop_debug_payload = {"debugId": self.debugId}
                    self._ubox.make_request('PUT', '/cloudphone/debug', data=stop_debug_payload,
                                            params={'authCode': self.authCode},
                                            base_url=self._ubox.paas_base_url)
                    logger.info(f"正常模式设备 {self.udid} debug已停止")
                except Exception as e:
                    logger.warning(f"停止设备 {self.udid} debug失败: {e}")
            elif self.authCode and not self.debugId:
                logger.info(f"正常模式使用提供的authCode，无需停止debug")
            else:
                logger.info(f"本地模式设备 {self.udid}，无需释放")
        finally:
            # 从 UBox 的设备列表中移除自己
            if hasattr(self._ubox, '_devices') and self.udid in self._ubox._devices:
                del self._ubox._devices[self.udid]

    def close(self):
        # 关闭前尝试释放设备（若已初始化）
        try:
            self.release()
        except Exception:
            # 忽略释放失败，继续关闭连接
            pass
        finally:
            # 确保停止续期任务
            self._stop_all_task()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            self.release()
        except Exception:
            pass
        return False

    def device_info(self, trace_id: Optional[str] = None) -> dict:
        """
        获取该设备的信息。
        
        Returns:
            dict: 设备信息字典，包含设备的所有信息
            
        Note:
            - Android设备返回体包含完整的硬件信息
            - iOS设备返回体包含基本信息和scale等iOS特有字段
            
        Returns Examples:
            Android设备返回体示例:
            {
                "display": {
                    "width": 1440,
                    "height": 3200,
                    "rotation": 0
                },
                "density": {
                    "density": 480,
                    "dpx": 480,
                    "dpy": 1066
                },
                "os_version": "13",
                "os_sdk": 33,
                "driver": "utest-agent-1.0.24",
                "manufacturer": "meizu",
                "model": "MEIZU 18",
                "cpu": {
                    "cores": 7,
                    "hardware": ""
                },
                "arch": "arm64-v8a",
                "memory": {
                    "total": 7377784,
                    "free": 315732,
                    "available": 2620104,
                    "around": "7 GB"
                },
                "storage": {
                    "total": 114392375296,
                    "available": 21983236096
                },
                "screen_on": 1
            }
            
            iOS设备返回体示例:
            {
                "display": {
                    "width": 750,
                    "height": 1334,
                    "scale": 2.0
                },
                "name": "iphone8 632f",
                "uuid": "632fe89f827e6284e81f3856cdffc5f88c199583",
                "model": "iPhone10,1",
                "version": 0,
                "cpu": {
                    "cores": "0"
                },
                "memory": {
                    "total": 0
                },
                "screen_on": -1
            }
        """
        operation = DeviceInfoOperation(self)
        return operation.execute(trace_id=trace_id)

    def screen_size(self, trace_id: Optional[str] = None) -> List[int]:
        """获取屏幕分辨率.

        Args:
            无
        Returns:
            list: 设备屏幕的物理分辨率

        """
        operation = ScreenSizeOperation(self)
        return operation.execute(trace_id=trace_id)

    def get_auth_info(self) -> Dict[str, Any]:
        """
        获取设备的认证信息

        Returns:
            Dict包含认证信息：authCode、debugId、client_addr
        """
        return {
            'udid': self.udid,
            'authCode': self.authCode,
            'debugId': self.debugId,
            'client_addr': self.client_addr,
        }

    def cmd_adb(self, cmd: Union[str, list], timeout: int = 10, trace_id: Optional[str] = None) -> Union[
        tuple[str, int], str]:
        """
        执行 ADB 命令

        Args:
            cmd: 要执行的 ADB 命令，例如 "ls", "ps", "getprop" 等
            timeout: int 执行命令的超时时间

        Returns:
            Union[tuple[str, int], str]:
                - 安卓设备返回 (output, exit_code) 元组
                - 鸿蒙设备返回 output 字符串
        """
        operation = CmdAdbOperation(self)
        return operation.execute(cmd=cmd, timeout=timeout, trace_id=trace_id)

    def get_element_cv(
            self,
            tpl: str,
            img: Optional[str] = None,
            timeout: int = 30,
            threshold: float = 0.8,
            pos: Union[tuple, list] = None,
            pos_weight: float = 0.05,
            ratio_lv: int = 21,
            crop_box: Union[tuple, list] = None,
            is_translucent: bool = False,
            to_gray: bool = False,
            tpl_l: Optional[str] = None,
            deviation: Union[tuple, list] = None,
            time_interval: float = 0.5,
            trace_id: Optional[str] = None,
            **kwargs
    ) -> Dict[str, Any]:
        """基于多尺寸模板匹配的图像查找

        Args:
            tpl (str): 待匹配查找的目标图像路径
            img (str): 在该图上进行查找，为None时则获取当前设备画面
            timeout (int): 查找超时时间
            threshold (float): 匹配阈值
            pos (tuple or list): 目标图像的坐标，以辅助定位图像位置
            pos_weight (float): 坐标辅助定位的权重
            ratio_lv (int): 缩放范围，数值越大则进行更大尺寸范围的匹配查找
            crop_box (list or tuple): 屏蔽范围或者保留范围，均为百分比
                - 保留范围: 保留矩形范围的<左上角顶点>坐标和<右下角>坐标，示例 [[0.3, 0.3], [0.7, 0.7]]
                - 屏蔽范围: [0, 1, 0, 0.3] 屏蔽x轴 0-1, y轴0-0.3的部分
            is_translucent (bool): 目标图像是否为半透明，为True则会进行图像预处理
            to_gray (bool): 是否将图像转换为灰度图
            tpl_l (str): 备选的尺寸更大的目标图像路径，以辅助定位
            deviation (tuple or list): 偏差，目标及备选目标间的偏差
            time_interval (float): 循环查找的时间间隔，默认为0.5s
            trace_id: 追踪ID，用于日志跟踪
            **kwargs: 其他参数

        Returns:
            dict: {
                'bounds': [88, 953, 900, 997],
            }
        """
        operation = GetElementCVOperation(self)
        return operation.execute(
            tpl=tpl,
            img=img,
            timeout=timeout,
            threshold=threshold,
            pos=pos,
            pos_weight=pos_weight,
            ratio_lv=ratio_lv,
            crop_box=crop_box,
            is_translucent=is_translucent,
            to_gray=to_gray,
            tpl_l=tpl_l,
            deviation=deviation,
            time_interval=time_interval,
            trace_id=trace_id,
            **kwargs
        )

    def get_element_ocr(
            self,
            word: str,
            crop_box: Union[tuple, list] = None,
            timeout: int = 30,
            time_interval: float = 0.5,
            trace_id: Optional[str] = None,
            **kwargs
    ) -> Dict[str, Any]:
        """基于OCR文字识别的查找

        Args:
            word (str): 待查找文字
            crop_box (list or tuple): 屏蔽范围或者保留范围，均为百分比
                - 保留范围: 保留矩形范围的<左上角顶点>坐标和<右下角>坐标，示例 [[0.3, 0.3], [0.7, 0.7]]
                - 屏蔽范围: [0, 1, 0, 0.3] 屏蔽x轴 0-1, y轴0-0.3的部分
            timeout (int): 查找超时时间
            time_interval (float): 循环查找的时间间隔，默认为0.5s
            trace_id: 追踪ID，用于日志跟踪
            **kwargs: 其他参数（可能包含left_word, right_word等辅助定位参数）

        Returns:
            dict: {
                'bounds': [88, 953, 900, 997],
            }

        """
        operation = GetElementOCROperation(self)
        return operation.execute(
            word=word,
            crop_box=crop_box,
            timeout=timeout,
            time_interval=time_interval,
            trace_id=trace_id,
            **kwargs
        )

    def record_start(self, video_path: str = '', trace_id: Optional[str] = None) -> bool:
        """开始录制屏幕

        Args:
            video_path: str 录屏的输出文件路径
        Returns:
            bool: 开启录制是否成功
            
        Raises:
            UBoxDeviceError: 录制启动失败时抛出异常
        """
        self.video_path = os.path.abspath(video_path)
        operation = RecordStartOperation(self)
        return operation.execute(trace_id=trace_id)

    def record_stop(self, trace_id: Optional[str] = None) -> bool:
        """停止录制屏幕

        Args:
            
        Returns:
            bool: 结束录制是否成功
            
        Raises:
            UBoxDeviceError: 停止录制失败时抛出异常
        """
        operation = RecordStopOperation(self)
        return operation.execute(trace_id=trace_id)

    def screenshot(self, label: str, img_path: str,
                   crop: Tuple[Union[int, float], Union[int, float], Union[int, float], Union[int, float]] = None,
                   trace_id: Optional[str] = None) -> str:
        """对设备当前画面进行截图

        Args:
            label: str 截图文件名
            img_path: str 文件路径
            crop: Tuple[Union[int, float], Union[int, float], Union[int, float], Union[int, float]]
               (left, upper, right, lower) 裁剪功能，如果指定了则返回裁剪后的路径
               - 如果所有元素都在0~1之间，视为比例 (0.1, 0.1, 0.9, 0.9)
               - 否则视为像素坐标(100, 50, 400, 300)
            trace_id: str
            
        Returns:
            str: "/tmp/xx.jpg" 图片路径
        Example:
            device.screenshot("demo", "./screenshots")
        Raises:
            UBoxDeviceError: 截图失败时抛出异常
        """
        operation = ScreenshotOperation(self)
        local_img_path = operation.execute(img_path=img_path, label=label, trace_id=trace_id)
        if crop and local_img_path:
            return crop_image_save(local_img_path, crop)
        return local_img_path

    def screenshot_base64(self,
                          crop: Tuple[
                              Union[int, float], Union[int, float], Union[int, float], Union[int, float]] = None,
                          trace_id: Optional[str] = None) -> str:
        """对设备当前画面进行截图，返回base64编码的图片数据

        Args:
            crop: Tuple[Union[int, float], Union[int, float], Union[int, float], Union[int, float]]
               (left, upper, right, lower)裁剪功能，如果指定了则返回裁剪后的base64
               - 如果所有元素都在0~1之间，视为比例 (0.1, 0.1, 0.9, 0.9)
               - 否则视为像素坐标(100, 50, 400, 300)
            trace_id: str
        Returns:
            str: 图片base64编码字符串
        Raises:
            UBoxDeviceError: 截图失败时抛出异常
        """
        operation = ScreenshotBase64Operation(self)
        img_base64_str = operation.execute(trace_id=trace_id)
        if crop and img_base64_str:
            return crop_base64_image(img_base64_str, crop)
        return img_base64_str

    def click_pos(self, pos: Union[list, tuple], duration: Union[int, float] = 0.05, times: int = 1,
                  trace_id: Optional[str] = None) -> bool:
        """基于相对坐标进行点击操作

        Args:
            pos: 相对坐标，取值区间 [0, 1.0)，左闭右开，不含1，可以传0.99
            duration: 点击持续时间，默认为 0.05 秒
            times: 点击次数，默认为 1 次，传入 2 可实现双击效果

        Returns:
            bool: 点击是否成功

        Raises:
            UBoxValidationError: 参数验证失败时抛出异常
            UBoxDeviceError: 操作失败时抛出异常
        """
        operation = ClickPosOperation(self)
        return operation.execute(pos=pos, duration=duration, times=times, trace_id=trace_id)

    def slide_pos(self, pos_from: Union[list, tuple], pos_to: Union[list, tuple] = None,
                  down_duration: Union[int, float] = 0, slide_duration: Union[int, float] = 0.3,
                  trace_id: Optional[str] = None) -> bool:
        """基于相对坐标执行滑动操作

        Args:
            pos_from: 滑动起始坐标，取值区间 [0, 1.0)，左闭右开，不含1，可以传0.99，格式为 [x, y]
            pos_to: 滑动结束坐标，取值区间 [0, 1.0)，左闭右开，不含1，可以传0.99，格式为 [x, y]
            down_duration: 起始位置按下时长（秒），以实现拖拽功能，默认为 0
            slide_duration (int or float): 滑动时间(Android)
            trace_id: 追踪id
        Returns:
            bool: 滑动是否成功

        Raises:
            UBoxValidationError: 参数验证失败时抛出异常
            UBoxDeviceError: 操作失败时抛出异常

        Note:
            - 坐标值使用相对坐标系统，[0, 0] 表示屏幕左上角，[0.99, 0.99] 表示接近屏幕右下角
            - 相对坐标取值范围是 [0, 1.0)，左闭右开，不含1，如需点击屏幕边缘可使用0.99
            - 通过设置 down_duration 可以实现拖拽效果

        Examples:
            # 从屏幕中心滑动到右上角
            device.slide_pos([0.5, 0.5], [0.9, 0.1])
            
            # 从屏幕中心滑动到右下角（使用0.99接近边缘）
            device.slide_pos([0.5, 0.5], [0.99, 0.99])
            
            # 从屏幕底部向上滑动，带拖拽效果
            device.slide_pos([0.5, 0.9], [0.5, 0.1], down_duration=0.5)
        """
        operation = SlidePosOperation(self)
        return operation.execute(
            pos_from=pos_from, pos_to=pos_to,
            down_duration=down_duration, slide_duration=slide_duration, trace_id=trace_id
        )

    def click(self, loc, by=DriverType.UI, offset: Union[list, tuple] = None, crop_box: Union[list, tuple] = None,
              timeout: int = 30, duration: float = 0.05, times: int = 1, trace_id: Optional[str] = None,
              **kwargs) -> bool:
        """基于多种定位方式执行点击操作

        Args:
            loc: 待点击的元素，具体形式需符合基于的点击类型
                - 当by=3(CV)时，loc为模板图像路径
                - 当by=1(UI)时，loc为UI元素选择器
                - 当by=2(OCR)时，loc为要识别的文字
                - 当by=0(POS)时，loc为坐标位置
            by: 查找类型，默认为 1 (UI)
                - 1: 原生控件 (UI)
                - 3: 图像匹配 (CV) - loc参数为模板图像路径
                - 2: 文字识别 (OCR)
                - 0: 坐标 (POS)
                - 5: GA Unity
                - 6: GA UE
            offset: 偏移，元素定位位置加上偏移为实际操作位置
            crop_box (list or tuple): 需要屏蔽或者保留的的区域
            timeout: 定位元素的超时时间，默认为 30 秒
            duration: 点击的按压时长，以实现长按，默认为 0.05 秒
            times: 点击次数，以实现双击等效果，默认为 1 次
            trace_id: 追踪ID
            **kwargs: 基于不同的查找类型，其他需要的参数
                - 当by=3(CV)时，支持以下参数：
                    - img: 背景图像路径（可选）
                    - tpl_l: 大尺寸模板图像路径（可选）
                    - threshold: 匹配阈值，默认0.8
                    - pos: 目标坐标，用于辅助定位
                    - pos_weight: 坐标辅助定位权重，默认0.05
                    - ratio_lv: 缩放范围，默认21
                    - is_translucent: 是否半透明，默认False
                    - to_gray: 是否转灰度，默认False
                    - deviation: 偏差参数
                    - time_interval: 循环查找间隔，默认0.5秒

        Returns:
            bool: 操作是否成功

        Raises:
            UBoxValidationError: 参数验证失败时抛出异常
            UBoxDeviceError: 操作失败时抛出异常
        """
        operation = ClickOperation(self)
        return operation.execute(
            loc=loc, by=by, offset=offset, crop_box=crop_box, timeout=timeout,
            duration=duration, times=times, trace_id=trace_id, **kwargs
        )

    def long_click(self, loc, by=1, offset: Union[list, tuple] = None, timeout: int = 30,
                   duration: Union[int, float] = 1, crop_box: Union[list, tuple] = None,
                   trace_id: Optional[str] = None, **kwargs) -> bool:
        """执行长按操作

        Args:
            loc: 待操作的元素，具体形式需符合基于的操作类型
            by: 查找类型，默认为 1 (UI)
            offset: 偏移，元素定位位置加上偏移为实际操作位置
            timeout: 定位元素的超时时间，默认为 30 秒
            duration: 点击的按压时长，默认为 1 秒
            crop_box (list or tuple): 需要屏蔽或者保留的的区域
            trace_id: 追踪ID
            **kwargs: 基于不同的查找类型，其他需要的参数

        Returns:
            bool: 操作是否成功

        Raises:
            UBoxValidationError: 参数验证失败时抛出异常
            UBoxDeviceError: 操作失败时抛出异常
        """
        operation = ClickOperation(self)
        return operation.execute(
            loc=loc, by=by, offset=offset, crop_box=crop_box, timeout=timeout,
            duration=duration, trace_id=trace_id, **kwargs
        )

    def input_text(self, text: str, timeout: int = 30, depth: int = 10, trace_id: Optional[str] = None) -> bool:
        """向设备输入文本内容

        Args:
            text: 待输入的文本
            timeout: 超时时间，默认为 30 秒
            depth: source tree 的最大深度值，默认为 10

        Returns:
            bool: 输入是否成功

        Raises:
            UBoxValidationError: 参数验证失败时抛出异常
            UBoxDeviceError: 操作失败时抛出异常
        """
        operation = InputTextOperation(self)
        return operation.execute(text=text, timeout=timeout, depth=depth, trace_id=trace_id)

    def press(self, name: DeviceButton, trace_id: Optional[str] = None) -> bool:
        """执行设备功能键操作

        Args:
            name: 设备按键类型，使用 DeviceButton 枚举值

        Returns:
            bool: 操作是否成功

        Raises:
            UBoxValidationError: 参数验证失败时抛出异常
            UBoxDeviceError: 操作失败时抛出异常
        """
        operation = PressOperation(self)
        return operation.execute(name=name, trace_id=trace_id)

    def slide(self, loc_from, loc_to=None, by=1,
              timeout: int = 120, down_duration: Union[int, float] = 0, slide_duration: Union[int, float] = 0.3,
              trace_id: Optional[str] = None, **kwargs) -> bool:
        """基于多种定位方式执行滑动操作

        Args:
            loc_from: 滑动起始元素位置
            loc_to: 滑动结束元素位置，为 None 时则根据 loc_shift 滑动
            by: 查找类型，默认为 1 (UI)
            timeout: 定位元素的超时时间，默认为 120 秒
            down_duration: 起始位置按下时长（秒），以实现拖拽功能，默认为 0
            slide_duration (int or float): 滑动时间(Android)
            trace_id: 追踪id
            **kwargs: 基于不同的查找类型，其他需要的参数

        Returns:
            bool: 操作是否成功

        Raises:
            UBoxValidationError: 参数验证失败时抛出异常
            UBoxDeviceError: 操作失败时抛出异常
        """
        operation = SlideOperation(self)
        return operation.execute(
            loc_from=loc_from, loc_to=loc_to, by=by, timeout=timeout,
            down_duration=down_duration, slide_duration=slide_duration, trace_id=trace_id, **kwargs
        )

    def install_app(self, app_url: str = None, app_path: str = None, need_resign: bool = False,
                    resign_bundle: str = "", trace_id: Optional[str] = None) -> bool:
        """安装应用到设备

        Args:
            app_url: 安装包url链接，可下载的cos链接
            app_path: 安装包本地地址(手机所在的client本地地址，本地调试预留、请勿使用此字段)
            need_resign: 可缺省，默认为 False。只有 iOS 涉及，需要重签名时传入 True
            resign_bundle: 可缺省，默认为空。只有 iOS 涉及，need_resign 为 True 时，此参数必须传入非空的 bundleId

        Returns:
            bool: 安装是否成功

        Raises:
            UBoxValidationError: 参数验证失败时抛出异常
            UBoxDeviceError: 操作失败时抛出异常
        """
        operation = InstallAppOperation(self)
        return operation.execute(
            app_url=app_url, app_path=app_path,
            need_resign=need_resign, resign_bundle=resign_bundle, trace_id=trace_id
        )

    def local_install_app(self, local_app_path: str, need_resign: bool = False,
                          resign_bundle: str = "", trace_id: Optional[str] = None) -> bool:
        """安装应用到设备

        Args:
            local_app_path: 安装包本地地址
            need_resign: 可缺省，默认为 False。只有 iOS 涉及，需要重签名时传入 True
            resign_bundle: 可缺省，默认为空。只有 iOS 涉及，need_resign 为 True 时，此参数必须传入非空的 bundleId

        Returns:
            bool: 安装是否成功

        Raises:
            UBoxValidationError: 参数验证失败时抛出异常
            UBoxDeviceError: 操作失败时抛出异常
        """
        operation = LocalInstallAppOperation(self)
        return operation.execute(
            local_app_path=local_app_path,
            need_resign=need_resign, resign_bundle=resign_bundle, trace_id=trace_id
        )

    def uninstall_app(self, pkg: str, trace_id: Optional[str] = None) -> bool:
        """从设备卸载应用

        Args:
            pkg: 被卸载应用的包名，Android 和鸿蒙为应用的 packageName，iOS 则对应为 bundleId

        Returns:
            bool: 卸载是否成功

        Raises:
            UBoxValidationError: 参数验证失败时抛出异常
            UBoxDeviceError: 操作失败时抛出异常
        """
        operation = UninstallAppOperation(self)
        return operation.execute(pkg=pkg, trace_id=trace_id)

    def start_app(self, pkg: str, clear_data: bool = False, trace_id: Optional[str] = None, **kwargs) -> bool:
        """启动应用

        Args:
            pkg: iOS 为应用 bundle id，Android 和鸿蒙对应为包名
            clear_data: 可缺省，默认为 False。仅 Android,HM 相关，清除应用数据,ios不支持
            **kwargs: 其他扩展参数

        Returns:
            bool: 启动是否成功

        Raises:
            UBoxValidationError: 参数验证失败时抛出异常
            UBoxDeviceError: 操作失败时抛出异常
        """
        operation = StartAppOperation(self)
        return operation.execute(pkg=pkg, clear_data=clear_data, trace_id=trace_id, **kwargs)

    def stop_app(self, pkg: str, trace_id: Optional[str] = None) -> bool:
        """停止应用

        Args:
            pkg: iOS 为应用 bundle id，Android 和鸿蒙对应为包名

        Returns:
            bool: 停止是否成功

        Raises:
            UBoxValidationError: 参数验证失败时抛出异常
            UBoxDeviceError: 操作失败时抛出异常
        """
        operation = StopAppOperation(self)
        return operation.execute(pkg=pkg, trace_id=trace_id)

    #
    # def open_url(self, url: str) -> bool:
    #     """通过 URL 执行快捷操作，实现通过 URL 跳转到特定界面（仅 web）
    #
    #     Args:
    #         url: 待跳转界面的 URL
    #
    #     Returns:
    #         bool: 是否跳转成功
    #
    #     Raises:
    #         UBoxValidationError: 参数验证失败时抛出异常
    #         UBoxDeviceError: 操作失败时抛出异常
    #     """
    #     operation = OpenUrlOperation(self)
    #     return operation.execute(url=url)

    def ios_open_url(self, url: str, permission_config: dict = None, trace_id: Optional[str] = None) -> bool:
        """iOS设备智能打开URL功能
        
        自动导航到主屏幕，查找并点击"打开URL"按钮，输入URL，处理权限弹窗等。
        这是一个完整的自动化流程，专门为iOS设备设计。
        
        Args:
            url: 要打开的URL
            permission_config: 权限弹窗处理配置，包含以下字段：
                - watcher_name: 权限弹窗的watcher名称，默认"权限弹窗"
                - allow_conditions: 允许按钮的匹配条件列表，默认["允许", "打开"]
                - wait_time: 等待权限弹窗处理完成的时间（秒），默认20秒
                - enabled: 是否启用权限弹窗处理，默认True
            
        Returns:
            bool: 操作是否成功
            
        Raises:
            UBoxValidationError: 参数验证失败时抛出异常
            UBoxDeviceError: 操作失败时抛出异常
            
        Example:
            # 使用默认配置
            device.ios_open_url("https://example.com")
            
            # 自定义权限处理配置
            config = {
                 "watcher_name": "权限弹窗",
                 "allow_conditions": ["允许", "打开", "同意"],
                 "wait_time": 30,
                 "enabled": True
             }
            device.ios_open_url("https://example.com", permission_config=config)
            
            # 禁用权限处理
            device.ios_open_url("https://example.com", permission_config={"enabled": False})
        """
        helper = IOSOpenUrlHelper(self, trace_id=trace_id)
        return helper.open_url(url=url, permission_config=permission_config)

    def find_cv(self, tpl, img=None, timeout: int = 30, threshold: float = 0.8,
                pos=None, pos_weight: float = 0.05, ratio_lv: int = 21,
                is_translucent: bool = False, to_gray: bool = False,
                tpl_l=None, deviation=None, time_interval: float = 0.5, trace_id: Optional[str] = None,
                **kwargs) -> Any:
        """基于多尺寸模板匹配的图像查找

        Args:
            tpl: 待匹配查找的目标图像
            img: 在该图上进行查找，为None时则获取当前设备画面
            timeout: 查找超时时间
            threshold: 匹配阈值 (0-1.0)
            pos: 目标图像的坐标，以辅助定位图像位置
            pos_weight: 坐标辅助定位的权重
            tpl_l: 备选的尺寸更大的目标图像，以辅助定位
            deviation: 偏差，目标及备选目标间的偏差
            ratio_lv: 缩放范围，数值越大则进行更大尺寸范围的匹配查找
            is_translucent: 目标图像是否为半透明，为True则会进行图像预处理
            to_gray: 是否将图像转换为灰度图
            time_interval: 循环查找的时间间隔，默认为0.5s
            **kwargs: 其他扩展参数

        Returns:
            查找到的坐标，未找到则返回None

        Raises:
            UBoxValidationError: 参数验证失败时抛出异常
            UBoxDeviceError: 操作失败时抛出异常
        """
        operation = FindCVOperation(self)
        return operation.execute(
            tpl=tpl, img=img, timeout=timeout, threshold=threshold,
            pos=pos, pos_weight=pos_weight, ratio_lv=ratio_lv,
            is_translucent=is_translucent, to_gray=to_gray,
            tpl_l=tpl_l, deviation=deviation, time_interval=time_interval, trace_id=trace_id, **kwargs
        )

    def find_ocr(self, word: str, left_word: str = None, right_word: str = None,
                 timeout: int = 30, time_interval: float = 0.5, trace_id: Optional[str] = None, **kwargs) -> Any:
        """基于OCR文字识别的查找

        Args:
            word: 待查找文字
            left_word: 待查找文字左侧文字
            right_word: 待查找文字右侧文字
            timeout: 查找超时时间
            time_interval: 循环查找的时间间隔，默认为0.5s
            **kwargs: 其他扩展参数

        Returns:
            查找到的中心点坐标

        Raises:
            UBoxValidationError: 参数验证失败时抛出异常
            UBoxDeviceError: 操作失败时抛出异常
        """
        operation = FindOCROperation(self)
        return operation.execute(
            word=word, left_word=left_word, right_word=right_word,
            timeout=timeout, time_interval=time_interval, trace_id=trace_id, **kwargs
        )

    def find_ui(self, xpath: str, timeout: int = 30, trace_id: Optional[str] = None, **kwargs) -> Any:
        """基于控件查找

        Args:
            xpath: 控件xpath
            timeout: 查找超时时间
            **kwargs: 其他扩展参数

        Returns:
            查找到的中心点坐标

        Raises:
            UBoxValidationError: 参数验证失败时抛出异常
            UBoxDeviceError: 操作失败时抛出异常
        """
        operation = FindUIOperation(self)
        return operation.execute(xpath=xpath, timeout=timeout, trace_id=trace_id, **kwargs)

    def find(self, loc, by=1, timeout: int = 30, trace_id: Optional[str] = None, **kwargs) -> Any:
        """通用查找

        Args:
            loc: 待查找的元素，具体形式需符合基于的查找类型
            by: 查找类型，默认为1 (UI)
            timeout: 查找超时时间
            **kwargs: 基于不同的查找类型，其他需要的参数

        Returns:
            查找到的坐标，未找到则返回None

        Raises:
            UBoxValidationError: 参数验证失败时抛出异常
            UBoxDeviceError: 操作失败时抛出异常
        """
        operation = FindOperation(self)
        return operation.execute(loc=loc, by=by, timeout=timeout, trace_id=trace_id, **kwargs)

    def multi_find(self, ctrl: str = "", img=None, pos=None, by=1,
                   ctrl_timeout: int = 30, img_timeout: int = 10, trace_id: Optional[str] = None, **kwargs) -> Any:
        """综合查找

        优先基于控件定位，未查找到则基于图片匹配+坐标定位，仍未找到则返回传入坐标

        Args:
            ctrl: 待查找的控件
            img: 待匹配查找的图像
            pos: 目标图像的坐标，以辅助定位图像位置
            by: ctrl的控件类型，默认为1 (UI)
            ctrl_timeout: 基于控件查找的超时时间
            img_timeout: 基于图像匹配查找的超时时间
            **kwargs: 不同查找类型需要设置的参数

        Returns:
            查找到的中心点坐标及查找结果基于的查找类型

        Raises:
            UBoxValidationError: 参数验证失败时抛出异常
            UBoxDeviceError: 操作失败时抛出异常
        """
        operation = MultiFindOperation(self)
        return operation.execute(
            ctrl=ctrl, img=img, pos=pos, by=by,
            ctrl_timeout=ctrl_timeout, img_timeout=img_timeout, trace_id=trace_id, **kwargs
        )

    def get_uitree(self, xml: bool = False, trace_id: Optional[str] = None) -> Union[Dict[str, Any], str]:
        """获取控件树

        Args:
            xml: 为True时返回xml格式数据，否则json格式

        Returns:
            控件树数据

        Raises:
            UBoxDeviceError: 操作失败时抛出异常
        """
        operation = GetUITreeOperation(self)
        return operation.execute(xml=xml, trace_id=trace_id)

    def get_element(self, xpath: str, timeout: int = 30, trace_id: Optional[str] = None) -> Any:
        """根据xpath获取元素

        Args:
            xpath: 获取元素的xpath
            timeout: 等待时间(秒)

        Returns:
            元素对象，没有匹配到则返回None

        Raises:
            UBoxValidationError: 参数验证失败时抛出异常
            UBoxDeviceError: 操作失败时抛出异常
        """
        operation = GetElementOperation(self)
        return operation.execute(xpath=xpath, timeout=timeout, trace_id=trace_id)

    def get_elements(self, xpath: str, trace_id: Optional[str] = None) -> Any:
        """根据xpath获取元素列表

        Args:
            xpath: 获取元素的xpath

        Returns:
            元素对象的列表

        Raises:
            UBoxValidationError: 参数验证失败时抛出异常
            UBoxDeviceError: 操作失败时抛出异常
        """
        operation = GetElementsOperation(self)
        return operation.execute(xpath=xpath, trace_id=trace_id)

    #
    # def get_text(self, img, iou_th: float = 0.1) -> Any:
    #     """查找图像中的所有文本
    #
    #     Args:
    #         img: 待识别的图像
    #         iou_th: 行分割阈值
    #
    #     Returns:
    #         查找到的文本结果列表
    #
    #     Raises:
    #         UBoxValidationError: 参数验证失败时抛出异常
    #         UBoxDeviceError: 操作失败时抛出异常
    #     """
    #     operation = GetTextOperation(self)
    #     return operation.execute(img=img, iou_th=iou_th)

    def set_clipboard(self, text: str, trace_id: Optional[str] = None) -> Any:
        """设置剪贴板

        Args:
            text: 设置的文本

        Returns:
            操作结果

        Raises:
            UBoxValidationError: 参数验证失败时抛出异常
            UBoxDeviceError: 操作失败时抛出异常
        """
        operation = SetClipboardOperation(self)
        return operation.execute(text=text, trace_id=trace_id)

    def get_clipboard(self, trace_id: Optional[str] = None) -> Any:
        """获取剪贴板

        Returns:
            剪贴板文本内容

        Raises:
            UBoxDeviceError: 操作失败时抛出异常
        """
        operation = GetClipboardOperation(self)
        return operation.execute(trace_id=trace_id)

    def set_http_global_proxy(self, host: str, port: int, username: str = None, password: str = None,
                              trace_id: Optional[str] = None) -> Any:
        """设置全局代理

        Args:
            host: 代理服务器IP
            port: 代理服务器端口
            username: 用户名（可选）
            password: 密码（可选）

        Returns:
            操作结果

        Raises:
            UBoxValidationError: 参数验证失败时抛出异常
            UBoxDeviceError: 操作失败时抛出异常
        """
        operation = SetHttpGlobalProxyOperation(self)
        return operation.execute(host=host, port=port, username=username, password=password, trace_id=trace_id)

    def get_http_global_proxy(self, trace_id: Optional[str] = None) -> Any:
        """获取全局代理

        Returns:
            当前代理设置

        Raises:
            UBoxDeviceError: 操作失败时抛出异常
        """
        operation = GetHttpGlobalProxyOperation(self)
        return operation.execute(trace_id=trace_id)

    def clear_http_global_proxy(self, trace_id: Optional[str] = None) -> Any:
        """清除全局代理

        Returns:
            操作结果

        Raises:
            UBoxDeviceError: 操作失败时抛出异常
        """
        operation = ClearHttpGlobalProxyOperation(self)
        return operation.execute(trace_id=trace_id)

    def get_file_path_info(self, path: str, trace_id: Optional[str] = None) -> Any:
        """获取文件属性

        Args:
            path: 文件路径

        Returns:
            文件属性信息，包括：
            - isDirectory: 是否为目录
            - mode: 文件权限
            - modifyTime: 修改时间
            - name: 文件名
            - path: 文件路径
            - size: 文件大小
            - files: 目录下文件列表（如果是目录）

        Raises:
            UBoxValidationError: 参数验证失败时抛出异常
            UBoxDeviceError: 操作失败时抛出异常
        """
        operation = GetFilePathInfoOperation(self)
        return operation.execute(path=path, trace_id=trace_id)

    def load_default_handler(self, rule: list, trace_id: Optional[str] = None):
        """[自动处理相关] 批量加载事件自动处理规则

        Args:
            rule (list): 事件正则规则，list元素可为str、list、tuple，预设参数如下，使用预设请直接调用start_event_handler()
            rule = [
                '^(完成|关闭|关闭应用|好|允许|始终允许|好的|确定|确认|安装|下次再说|知道了|同意)$',
                r'^((?<!不)(忽略|允(\s){0,2}许|同(\s){0,2}意)|继续|清理|稍后|稍后处理|暂不|暂不设置|强制|下一步)$',
                '^((?i)allow|Sure|SURE|accept|install|done|ok)$',
                ('(建议.*清理)', '(取消|以后再说|下次再说)'),
                ('(发送错误报告|截取您的屏幕|是否删除)', '取消'),
                ('(隐私)', '同意并继续'),
                ('(隐私)', '同意'),
                ('(残留文件占用|网络延迟)', '取消'),
                ('(更新|游戏模式)', '取消'),
                ('(账号密码存储)', '取消'),
                ('(出现在其他应用上)', '关闭'),
                ('(申请获取以下权限)', '(允许|同意)'),
                ('(获取此设备)', '(仅在使用该应用时允许|允许|同意)'),
                ('(以下权限|暂不使用)', '^同[\s]{0,2}意'),
                ('(立即体验|立即升级)', '稍后处理'),
                ('(前往设置)', '暂不设置'),
                ('(我知道了)', '我知道了'),
                ('(去授权)', '去授权'),
                ('(看看手机通讯录里谁在使用微信.*)', '是'),
                ('(默认已允许以下所有权限|以下不提示|退出)', '确定'),
                ('(仅充电|仅限充电|传输文件)', '取消')
            ]

        Returns:
            None: 无返回值，操作成功时无异常抛出

        Raises:
            UBoxValidationError: 参数验证失败时抛出异常
            UBoxDeviceError: 操作失败时抛出异常
        """
        operation = LoadDefaultHandlerOperation(self)
        operation.execute(rule=rule, trace_id=trace_id)

    def start_event_handler(self, trace_id: Optional[str] = None):
        """[自动处理相关] 启动预设事件自动处理

        Returns:
            None: 无返回值，操作成功时无异常抛出

        Raises:
            UBoxDeviceError: 操作失败时抛出异常
        """
        # self._start_event_task()
        operation = StartEventHandlerOperation(self)
        operation.execute(trace_id=trace_id)

    def add_event_handler(self, match_element: str, action_element: str = None, trace_id: Optional[str] = None):
        """[自动处理相关] 添加事件自动处理规则，并运行

        Args:
            match_element (str): 判断目标的正则匹配，存在则进行action_elem匹配并点击
            action_element (str): 点击目标的正则匹配，为None时则点击match_elem规则匹配结果

        Returns:
            None: 无返回值，操作成功时无异常抛出

        Raises:
            UBoxValidationError: 参数验证失败时抛出异常
            UBoxDeviceError: 操作失败时抛出异常
        """
        operation = AddEventHandlerOperation(self)
        operation.execute(match_element=match_element, action_element=action_element, trace_id=trace_id)

    def sync_event_handler(self, trace_id: Optional[str] = None):
        """[自动处理相关] 事件自动处理立即处理一次

        Returns:
            None: 无返回值，操作成功时无异常抛出

        Raises:
            UBoxDeviceError: 操作失败时抛出异常
        """
        self.get_element("//*[@content-desc='*$*none']", trace_id=trace_id)
        # operation = SyncEventHandlerOperation(self)
        # operation.execute()

    def clear_event_handler(self, trace_id: Optional[str] = None):
        """[自动处理相关] 清除事件自动处理规则

        Returns:
            None: 无返回值，操作成功时无异常抛出

        Raises:
            UBoxDeviceError: 操作失败时抛出异常
        """
        # 先停止异步监控任务
        # self._stop_event_task()
        # 然后执行清除操作
        operation = ClearEventHandlerOperation(self)
        operation.execute(trace_id=trace_id)

    # def wait_for_idle(self, idle_time: float = 0.5, timeout: float = 10.0) -> Any:
    #     """等待页面进入空闲状态
    #
    #     Args:
    #         idle_time: UI界面处于空闲状态的持续时间，当UI空闲时间>=idle_time时，该函数返回。默认0.5秒
    #         timeout: 等待超时时间，如果经过timeout秒后UI空闲时间仍然不满足，则返回。默认10秒
    #
    #     Returns:
    #         True: 页面进入idle状态; False: 在timeout时间内，页面未进入idle状态
    #
    #     Raises:
    #         UBoxDeviceError: 操作失败时抛出异常
    #     """
    #     operation = WaitForIdleOperation(self)
    #     return operation.execute(idle_time=idle_time, timeout=timeout)

    def create_remote_dir(self, trace_id: Optional[str] = None) -> Optional[str]:
        """创建远程设备client的目录

        Returns:
            str: 创建成功的临时目录

        Raises:
            UBoxDeviceError: 操作失败时抛出异常
        """
        operation = CreateRemoteDirOperation(self)
        operation.execute(trace_id=trace_id)

    def clean_remote_device_dir(self, trace_id: Optional[str] = None) -> bool:
        """清理设备client上的临时文件目录

        Returns:
            bool: 清理是否成功

        Raises:
            UBoxDeviceError: 操作失败时抛出异常
        """
        operation = CleanDeviceDirOperation(self)
        operation.execute(trace_id=trace_id)

    def current_app(self, trace_id: Optional[str] = None) -> str:
        """获取当前应用

        Args:
            trace_id: 可选的追踪ID，用于日志追踪

        Returns:
            str: 当前应用的包名或bundle ID
                - iOS设备返回bundle ID
                - Android和鸿蒙设备返回package name

        Raises:
            UBoxDeviceError: 操作失败时抛出异常

        Example:
            # 获取当前应用
            current_pkg = device.current_app()
            print(f"当前应用: {current_pkg}")
        """
        operation = CurrentAppOperation(self)
        return operation.execute(trace_id=trace_id)

    def current_activity(self, trace_id: Optional[str] = None) -> str:
        """[仅android和鸿蒙] 获取当前Activity

        Args:
            trace_id: 可选的追踪ID，用于日志追踪

        Returns:
            str: 当前Activity名称

        Raises:
            UBoxDeviceError: 操作失败时抛出异常

        Note:
            - 此功能仅适用于Android和鸿蒙设备
            - iOS设备不支持此功能

        Example:
            # 获取当前Activity
            current_activity = device.current_activity()
            print(f"当前Activity: {current_activity}")
        """
        operation = CurrentActivityOperation(self)
        return operation.execute(trace_id=trace_id)

    def clear_safari(self, close_pages: bool = False, trace_id: Optional[str] = None) -> bool:
        """清除iOS设备Safari历史缓存数据

        Args:
            close_pages: 是否关闭Safari的所有页面，默认为False
            trace_id: 可选的追踪ID，用于日志追踪

        Returns:
            bool: 清除是否成功

        Raises:
            UBoxDeviceError: 操作失败时抛出异常

        Note:
            - 此功能仅适用于iOS设备
            - 清除Safari的历史记录、缓存和Cookie等数据

        Example:
            # 清除Safari缓存
            success = device.clear_safari()
            
            # 清除Safari缓存并关闭所有页面
            success = device.clear_safari(close_pages=True)
        """
        operation = ClearSafariOperation(self)
        return operation.execute(close_pages=close_pages, trace_id=trace_id)

    def app_list_running(self, trace_id: Optional[str] = None) -> list[str]:
        """获取正在运行的app列表

        Args:
            trace_id: 可选的追踪ID，用于日志追踪

        Returns:
            list: 正在运行的app的包名列表
                - Android和鸿蒙设备返回package name列表
                - iOS设备返回bundle ID列表

        Raises:
            UBoxDeviceError: 操作失败时抛出异常

        Example:
            # 获取正在运行的app列表
            running_apps = device.app_list_running()
            print(f"正在运行的app: {running_apps}")
        """
        operation = AppListRunningOperation(self)
        return operation.execute(trace_id=trace_id)

    def perf_start(self, container_bundle_identifier: str, sub_process_name: str = '',
                   sub_window: str = '', case_name: str = '',
                   log_output_file: str = 'perf.log', trace_id: Optional[str] = None) -> bool:
        """开始采集性能数据

        Args:
            container_bundle_identifier: 应用包名
            sub_process_name: 进程名，默认为空
            sub_window: window名，默认为空
            case_name: Case名
            log_output_file: log文件名
            trace_id: 可选的追踪ID，用于日志追踪

        Returns:
            bool: 启动采集是否成功

        Raises:
            UBoxValidationError: 参数验证失败时抛出异常
            UBoxDeviceError: 操作失败时抛出异常

        Example:
            # 开始采集性能数据
            success = device.perf_start(
                container_bundle_identifier="com.tencent.mqq",
            )
        """
        # 检查是否已有性能采集在进行中
        if self.perf_case_name is not None:
            raise UBoxDeviceError(
                f"性能采集已在进行中，当前case_name: {self.perf_case_name}。请先调用perf_stop()结束当前采集"
            )

        operation = PerfStartOperation(self)
        return operation.execute(
            container_bundle_identifier=container_bundle_identifier,
            sub_process_name=sub_process_name,
            sub_window=sub_window,
            case_name=case_name,
            log_output_file=log_output_file,
            trace_id=trace_id
        )

    def perf_stop(self, output_directory: str = None, trace_id: Optional[str] = None) -> bool:
        """停止采集性能数据

        Args:
            trace_id: 可选的追踪ID，用于日志追踪
            output_directory: 数据输出文件目录,可不传，不传则不保存数据；需要使用perf_save_data保存
        Returns:
            bool: 停止采集是否成功

        Raises:
            UBoxDeviceError: 操作失败时抛出异常

        Example:
            # 停止采集性能数据
            success = device.perf_stop("./perf_output")
        """
        operation = PerfStopOperation(self)
        return operation.execute(output_directory=output_directory, trace_id=trace_id)

    def perf_save_data(self, output_directory: str, case_name: str = None,
                       trace_id: Optional[str] = None) -> bool:
        """导出性能数据

        Args:
            output_directory: 数据输出文件目录，默认为空
            case_name: Case名，默认为空
            trace_id: 可选的追踪ID，用于日志追踪

        Returns:
            bool: 是否成功导出

        Raises:
            UBoxDeviceError: 操作失败时抛出异常

        Example:
            # 导出性能数据
            success = device.perf_save_data(
                output_directory="/path/to/my/output",
            )
        """
        operation = PerfSaveDataOperation(self)
        return operation.execute(
            output_directory=output_directory,
            case_name=case_name,
            trace_id=trace_id
        )

    def logcat_start(self, file: str, clear: bool = False,
                     re_filter: Union[str, re.Pattern] = None, trace_id: Optional[str] = None) -> 'LogcatTask':
        """[仅android和鸿蒙] 启动logcat日志采集

        Args:
            file: 保存logcat的文件路径
            clear: 开始前是否清除logcat，默认为False
            re_filter: 用于过滤logcat的正则表达式模式
            trace_id: 可选的追踪ID，用于日志追踪

        Returns:
            LogcatTask: logcat任务对象，可直接调用stop()方法停止采集

        Raises:
            UBoxDeviceError: 操作失败时抛出异常

        Note:
            - 此功能仅适用于Android和鸿蒙设备
            - 返回的LogcatTask对象可以直接调用stop()方法停止采集

        Example:
            # 启动logcat采集
            task = device.logcat_start("logcat.txt", clear=True, re_filter=".*python.*")
            # 运行一段时间后停止
            task.stop()
        """
        operation = LogcatStartOperation(self)
        return operation.execute(
            file=file,
            clear=clear,
            re_filter=re_filter,
            trace_id=trace_id
        )

    def logcat_stop_all(self, trace_id: Optional[str] = None) -> bool:
        """[仅android和鸿蒙] 停止所有logcat日志采集任务

        Args:
            trace_id: 可选的追踪ID，用于日志追踪

        Returns:
            bool: 停止是否成功

        Raises:
            UBoxDeviceError: 操作失败时抛出异常

        Note:
            - 此功能仅适用于Android和鸿蒙设备
            - 停止设备上所有正在运行的logcat任务
            - 推荐使用LogcatTask.stop()方法停止特定任务

        Example:
            # 停止所有logcat采集任务
            success = device.logcat_stop_all()
        """
        if not hasattr(self, '_logcat_tasks') or not self._logcat_tasks:
            logger.info("没有正在运行的logcat任务")
            return True

        # 停止所有注册的任务
        success_count = 0
        total_count = len(self._logcat_tasks)

        # 创建任务列表的副本，避免在迭代时修改字典
        tasks_to_stop = list(self._logcat_tasks.values())

        for task in tasks_to_stop:
            try:
                if task.is_running():
                    task_stop_result = task.stop(trace_id=trace_id)
                    if task_stop_result:
                        success_count += 1
                        logger.debug(f"成功停止logcat任务: {task.task_id}")
                    else:
                        logger.warning(f"停止logcat任务失败: {task.task_id}")
                else:
                    # 任务已经停止，从注册表中移除
                    if task.task_id in self._logcat_tasks:
                        del self._logcat_tasks[task.task_id]
                    success_count += 1
            except Exception as e:
                logger.error(f"停止logcat任务{task.task_id}时发生异常: {e}")

        logger.info(f"logcat停止结果: {success_count}/{total_count} 个任务成功停止")
        return success_count == total_count

    def logcat_list_tasks(self) -> List['LogcatTask']:
        """[仅android和鸿蒙] 获取所有正在运行的logcat任务列表

        Returns:
            List[LogcatTask]: 正在运行的logcat任务列表

        Example:
            # 获取所有正在运行的logcat任务
            tasks = device.logcat_list_tasks()
            for task in tasks:
                print(f"任务ID: {task.task_id}, 文件路径: {task.file_path}")
        """
        if not hasattr(self, '_logcat_tasks'):
            return []

        # 过滤出正在运行的任务
        running_tasks = [task for task in self._logcat_tasks.values() if task.is_running()]
        return running_tasks

    def logcat_get_task(self, task_id: str) -> Optional['LogcatTask']:
        """[仅android和鸿蒙] 根据任务ID获取logcat任务

        Args:
            task_id: 任务ID

        Returns:
            Optional[LogcatTask]: 找到的任务对象，如果不存在则返回None

        Example:
            # 根据任务ID获取任务
            task = device.logcat_get_task("task_123")
            if task:
                task.stop()
        """
        if not hasattr(self, '_logcat_tasks'):
            return None

        return self._logcat_tasks.get(task_id)

    def anr_start(self, package_name: str, collect_am_monitor: bool = False, trace_id: Optional[str] = None) -> bool:
        """[仅android和鸿蒙] 启动ANR/Crash监控

        Args:
            package_name: 要监控的应用包名
            collect_am_monitor: 是否开启采集AM监控日志，默认为False
            trace_id: 可选的追踪ID，用于日志追踪

        Returns:
            bool: 启动是否成功

        Raises:
            UBoxDeviceError: 操作失败时抛出异常
            UBoxValidationError: 参数验证失败时抛出异常

        Note:
            - 此功能仅适用于Android和鸿蒙设备
            - 监控指定应用的ANR（Application Not Responding）和Crash问题
            - 需要调用anr_stop()停止监控
            - collect_am_monitor=True时会额外采集Activity Manager监控日志

        Example:
            # 启动ANR/Crash监控（不采集AM监控日志）
            success = device.anr_start(package_name="com.example.app")
            
            # 启动ANR/Crash监控（采集AM监控日志）
            success = device.anr_start(package_name="com.example.app", collect_am_monitor=True)
            if success:
                print("ANR监控已启动")
        """
        operation = ANRStartOperation(self)
        return operation.execute(package_name=package_name, collect_am_monitor=collect_am_monitor, trace_id=trace_id)

    def anr_stop(self, output_directory: Optional[str] = None, trace_id: Optional[str] = None) -> Dict[str, Any]:
        """[仅android和鸿蒙] 停止ANR/Crash监控

        Args:
            output_directory: 输出目录，用于保存监控结果文件（截图、日志等）
            trace_id: 可选的追踪ID，用于日志追踪

        Returns:
            Dict[str, Any]: 监控结果，包含以下字段：
                - success: 是否成功
                - run_time: 运行时间（秒）
                - crash_count: Crash次数
                - anr_count: ANR次数
                - logcat_file: 本地logcat文件路径（如果指定了output_directory）
                - screenshots: 本地截图文件路径列表（如果指定了output_directory）
                - context_files: 本地上下文文件路径列表（如果指定了output_directory）
                - am_monitor_file: 本地AM监控文件路径（如果指定了output_directory）

        Raises:
            UBoxDeviceError: 操作失败时抛出异常

        Note:
            - 此功能仅适用于Android和鸿蒙设备
            - 如果指定了output_directory，会自动下载相关文件到本地
            - 返回的字典包含监控统计信息和文件路径

        Example:
            # 停止ANR/Crash监控并下载文件
            result = device.anr_stop(output_directory="./anr_output")
            print(f"监控结果: ANR={result['anr_count']}, Crash={result['crash_count']}")
            print(f"截图文件: {result['screenshots_local']}")
        """
        operation = ANRStopOperation(self)
        return operation.execute(output_directory=output_directory, trace_id=trace_id)

    def init_driver(self, trace_id: Optional[str] = None) -> bool:
        """初始化设备

        Args:
            trace_id: 可选的追踪ID，用于日志追踪

        Returns:
            bool: 初始化是否成功

        Raises:
            UBoxDeviceError: 操作失败时抛出异常
        """
        operation = InitDriverOperation(self)
        return operation.execute(trace_id=trace_id)

    def pinch(self, rect: Union[list, tuple], scale: float, direction: Union[str, PinchDirection],
              trace_id: Optional[str] = None) -> bool:
        """执行双指缩放操作

        Args:
            rect: 用相对坐标系表示的缩放区域，由左上角顶点坐标x,y和区域宽高w,h组成，排列为[x,y,w,h]
                 - 坐标和尺寸取值区间为 [0, 1.0)，左闭右开，不含1，可以传0.99
            scale: 缩放倍数，小于1.0时为缩小，大于1.0时为放大，最大取2.0
            direction: 缩放方向，可以是字符串或PinchDirection枚举值
                - 'horizontal' 或 PinchDirection.HORIZONTAL: 横向/水平
                - 'vertical' 或 PinchDirection.VERTICAL: 纵向/垂直
                - 'diagonal' 或 PinchDirection.DIAGONAL: 斜向/对角线
            trace_id: 可选的追踪ID，用于日志追踪

        Returns:
            bool: 缩放是否成功

        Raises:
            UBoxValidationError: 参数验证失败时抛出异常
            UBoxDeviceError: 操作失败时抛出异常

        Example:
            # 在屏幕中心区域进行水平放大
            device.pinch(
                rect=[0.3, 0.3, 0.4, 0.4],
                scale=1.5,
                direction=PinchDirection.HORIZONTAL
            )

            # 在屏幕中心区域进行垂直缩小
            device.pinch(
                rect=[0.3, 0.3, 0.4, 0.4],
                scale=0.8,
                direction='vertical'
            )

            # 在屏幕中心区域进行对角线缩放
            device.pinch(
                rect=[0.25, 0.25, 0.5, 0.5],
                scale=2.0,
                direction='diagonal'
            )
        """
        operation = PinchOperation(self)
        return operation.execute(rect=rect, scale=scale, direction=direction, trace_id=trace_id)
