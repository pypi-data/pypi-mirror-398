"""
设备操作抽象基类

提供通用的设备操作处理逻辑，减少重复代码，提高可维护性和扩展性。
"""

import logging
import tempfile
import time
import traceback
import uuid
import zipfile
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union, Callable, List
import os
import json
import requests
import shutil

from requests import Response

from .common_util import make_dir
from .exceptions import UBoxDeviceError, UBoxValidationError
from .models import RunMode, DeviceButton, OSType, DriverType, PinchDirection
from .logger import default_logger
from .perf_wrapper import SaveDataWrapper

logger = default_logger


def _extract_field(data: Dict[str, Any], field: str, default=None) -> Any:
    """安全地提取字段值

    Args:
        data: 数据字典
        field: 字段名
        default: 默认值

    Returns:
        字段值或默认值
    """
    return data.get(field, default)


def _file_target_path_join(client_temp_dir: str, file_name: str) -> Any:
    """通过目标路径判断应该如何拼接路径

    Args:
        client_temp_dir: client的临时目录
        file_name: 文件名

    Returns:
        target_path
    """
    if '\\' in client_temp_dir and not '/' in client_temp_dir:
        sep = '\\'
    else:
        sep = '/'
    return client_temp_dir + sep + file_name


# 响应格式检查器函数
def check_standard_response(response_data: Dict[str, Any]) -> bool:
    """
    检查标准响应格式
    
    标准格式：
    {
        "success": true,
        "msg": "",
        "localUrl": "...",
        "imageUrl": "...",
        "fileKey": "...",
        "size": 123
    }
    
    Args:
        response_data: 响应数据
        
    Returns:
        bool: 是否成功
    """
    success = response_data.get('success')
    if success is None:
        # success 为 null 的情况（如开始录制）
        return True
    return bool(success)


def check_jsonrpc_response(response_data: Dict[str, Any]) -> bool:
    """
    检查JSON-RPC响应格式（如/rpc接口）
    
    JSON-RPC格式：
    {
        "jsonrpc": "2.0",
        "result": {...},
        "id": 123
    }
    
    Args:
        response_data: 响应数据
        
    Returns:
        bool: 是否成功
    """
    # JSON-RPC格式，只要有result字段就认为是成功的
    return 'result' in response_data


def check_jsonrpc_none_response(response_data: Dict[str, Any]) -> bool:
    """
    检查JSON-RPC响应格式（如/rpc接口）的无结果响应

    JSON-RPC格式：
    {
        "jsonrpc": "2.0",
        "id": 123
    }

    Args:
        response_data: 响应数据

    Returns:
        bool: 是否成功
    """
    if 'result' not in response_data:
        response_data['result'] = None
    if 'error' in response_data:
        return False
    return 'id' in response_data


def check_record_start_response(response_data: Dict[str, Any]) -> bool:
    """
    检查开始录制响应格式
    
    开始录制格式：
    {
        "success": null,
        "msg": "",
        "record_id": "xxx"
    }
    
    Args:
        response_data: 响应数据
        
    Returns:
        bool: 是否成功
    """
    # 开始录制接口，success为null但record_id存在就认为是成功的
    return response_data.get('record_id') is not None


class DeviceOperation(ABC):
    """设备操作抽象基类
    
    提供通用的设备操作处理逻辑，包括：
    1. 统一的请求发送逻辑
    2. 统一的响应处理逻辑
    3. 统一的错误处理逻辑
    4. 可扩展的操作配置
    """

    def __init__(self, device):
        """初始化设备操作
        
        Args:
            device: Device实例，包含sdk引用、udid、os_type等信息
        """
        self.device = device
        self._sdk = device._ubox
        self.udid = device.udid
        self.os_type = device.os_type
        self.client_addr = device.client_addr
        self.authCode = device.authCode
        self.mode = device.mode
        self._current_trace_id = None

    @property
    @abstractmethod
    def operation_config(self) -> Dict[str, Any]:
        """操作配置，子类必须实现
        
        Returns:
            Dict包含操作的配置信息
        """
        pass

    @abstractmethod
    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备请求参数，子类必须实现

        Args:
            **kwargs: 操作参数

        Returns:
            Dict: 请求参数
        """
        pass

    @abstractmethod
    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> Any:
        """后处理响应数据，子类必须实现

        Args:
            response_data: 响应数据
            **kwargs: 操作参数

        Returns:
            处理后的结果
        """
        pass

    # -------------------------------新的操作功能实现以上三个方法----------------------------------#

    def _build_request_params(self, **kwargs) -> Dict[str, Any]:
        """构建基础请求参数
        
        Args:
            **kwargs: 额外的请求参数
            
        Returns:
            Dict: 完整的请求参数
        """
        base_params = {
            "os_type": self.os_type.value,
            "udid": self.udid
        }
        base_params.update(kwargs)
        return base_params

    def _get_remote_request_headers(self, endpoint: str, method: str) -> Dict[str, str]:
        """获取请求头
        
        Args:
            endpoint: API端点
            
        Returns:
            Dict: 请求头
        """
        if self.mode == RunMode.NORMAL:
            # 正常模式：需要认证头
            return {
                'lab-auth-code': self.authCode,
                'lab-endpoint': endpoint,
                'lab-req-method': method,
                'auth-code': self.authCode,
                'serialnumber': self.udid,
                'traceId': self._current_trace_id
            }
        return {}

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Response:
        """发送请求的统一接口
        
        Args:
            method: HTTP方法
            endpoint: API端点
            **kwargs: 其他请求参数
            
        Returns:
            响应对象
            
        Raises:
            UBoxDeviceError: 请求失败时抛出异常
        """
        config = self.operation_config
        # 使用传入的traceId，如果没有则自动生成
        traceId = self._current_trace_id
        if traceId is None:
            traceId = time.strftime("%Y%m%d%H%M%S") + "_" + str(uuid.uuid4())
            self._current_trace_id = traceId
        try:
            if self.mode == RunMode.NORMAL:
                if self.device.use_proxy:
                    # 正常模式使用代理访问：通过代理转发
                    # 获取自定义参数（要转发给目标服务的）
                    custom_params = kwargs.pop('params', {})
                    # 将自定义params拼接到endpoint上，作为目标服务的查询参数
                    if custom_params:
                        # 构建查询字符串
                        query_string = '&'.join([f"{k}={v}" for k, v in custom_params.items()])
                        target_endpoint = f'{endpoint}?{query_string}'
                    else:
                        target_endpoint = endpoint
                    # 确保data有值，如果没有则给默认空字典
                    if 'data' not in kwargs or kwargs['data'] is None:
                        kwargs['data'] = {}
                    # 将代理服务器参数设置到kwargs中，这样会作为URL参数发送给代理服务器
                    kwargs['params'] = {'agentVersion': 'v2', 'authCode': self.authCode, 'traceId': traceId}
                    response = self._sdk.make_request(
                        method="POST",
                        endpoint=f'/api/v1/device/ubox/rpc',
                        headers=self._get_remote_request_headers(target_endpoint, method),
                        base_url=self.client_addr,
                        **kwargs
                    )
                else:
                    # 正常模式直接访问：直接访问目标设备地址
                    response = self._sdk.make_request(
                        method=method,
                        endpoint=endpoint,
                        base_url=self.client_addr,
                        **kwargs
                    )
            elif self.mode == RunMode.LOCAL:
                # 本地模式：直接访问本地地址，没有代理
                response = self._sdk.make_request(
                    method=method,
                    endpoint=endpoint,
                    base_url=self.client_addr,
                    **kwargs
                )
            else:
                raise UBoxDeviceError(f"不支持的运行模式: {self.mode}")

            # 在日志中添加traceId，用于链路追踪
            # logger.info(f"设备 {self.udid} {config['name']} 请求成功 - TraceID: {traceId}")
            return response

        except Exception as e:
            logger.error(
                f"设备 {self.udid} {config['name']} 请求失败 - TraceID: {traceId} - 错误: {e}\n{traceback.format_exc()}")
            raise UBoxDeviceError(f"{config['name']} 请求失败: {str(e)}")

    def _process_response(self, response: Response, success_checker=None) -> Any:
        """处理响应的统一接口
        
        Args:
            response: 响应对象
            success_checker: 自定义成功检查函数（可选，会覆盖配置中的检查器）
            
        Returns:
            Dict: 处理后的响应数据
            
        Raises:
            UBoxDeviceError: 响应处理失败时抛出异常
        """
        config = self.operation_config
        response_data = response.json()
        if self.mode == RunMode.NORMAL and self.device.use_proxy and 'data' in response_data:
            # 检查代理层是否成功
            proxy_code = response_data.get('code')
            if proxy_code != 200:
                proxy_msg = response_data.get('msg', '代理转发失败')
                raise UBoxDeviceError(f"代理转发失败，状态码: {proxy_code}, 错误信息: {proxy_msg}")

            # 提取实际的业务数据
            response_data = response_data['data']
        # elif self.mode == RunMode.NORMAL and not self.device.use_proxy:
        #     # 正常模式直接访问：直接使用响应数据，不需要代理层处理
        #     logger.debug(f"正常模式直接访问，直接使用响应数据: {response_data}")
        # elif self.mode == RunMode.LOCAL:
        #     # 本地模式：直接使用响应数据，不需要代理层处理
        #     logger.debug(f"本地模式，直接使用响应数据: {response_data}")

        # 确定使用哪个成功检查器
        # 优先级：传入的检查器 > 配置中的检查器 > 默认检查器
        final_checker = success_checker or config.get('response_checker')

        if final_checker:
            # 使用自定义检查器
            success = final_checker(response_data)
        else:
            # 默认检查器：根据数据类型进行不同的成功判断
            if isinstance(response_data, dict):
                success = response_data.get('success', False)
            elif isinstance(response_data, bool):
                success = response_data
            elif isinstance(response_data, str):
                # 字符串类型，通常非空表示成功
                success = bool(response_data.strip())
            else:
                # 其他类型，非None表示成功
                success = response_data is not None
            logger.debug(f"使用默认检查器，结果: {success}")

        if not success:
            # 尝试获取错误信息
            if isinstance(response_data, dict):
                msg = response_data.get('msg') or response_data.get('error')
                if not msg and 'result' in response_data:
                    # JSON-RPC格式，尝试从result中获取错误信息
                    result = response_data['result']
                    if isinstance(result, dict):
                        msg = result.get('error', '操作失败')
            else:
                # 非字典类型，使用类型信息作为错误信息
                msg = f"操作返回了意外的数据类型: {type(response_data).__name__}"
            logger.error(
                f"设备 {self.udid} {config['name']} 失败 - TraceID: {self._current_trace_id} - 错误: {msg}\n{traceback.format_exc()}")
            raise UBoxDeviceError(f"{config['name']}失败: {msg}")

        # logger.info(f"设备 {self.udid} {config['name']} 调用成功(不代表操作成功)")
        return response_data

    def _validate_required_field(self, data: Dict[str, Any], field: str, field_name: str = None) -> Any:
        """验证必需字段

        Args:
            data: 数据字典
            field: 字段名
            field_name: 字段显示名称

        Returns:
            字段值

        Raises:
            UBoxDeviceError: 字段不存在时抛出异常
        """
        value = data.get(field)
        if not value:
            display_name = field_name or field
            raise UBoxDeviceError(f"{self.operation_config['name']}失败：{display_name}为空")
        return value

    def _download_file(self, file_url: str, local_path: str, timeout: int = 300) -> None:
        """下载文件到本地指定路径

        Args:
            file_url: 云端文件URL
            local_path: 本地保存路径
            timeout: 下载超时时间（秒）

        Raises:
            UBoxDeviceError: 下载失败时抛出异常
        """
        import os
        import requests

        try:
            # 从文件扩展名自动判断文件类型
            file_extension = os.path.splitext(local_path)[1].lower()
            if file_extension in ['.mp4', '.avi', '.mov', '.mkv']:
                file_type = "视频文件"
            elif file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
                file_type = "图片文件"
            else:
                file_type = "文件"

            logger.info(f"开始下载{file_type}: {file_url}")
            logger.info(f"保存到本地路径: {local_path}")

            # 确保目标目录存在
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            # 下载文件
            response = requests.get(file_url, stream=True, timeout=timeout)
            response.raise_for_status()

            # 写入本地文件
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            # 下载完成，重置video_path
            file_size = os.path.getsize(local_path)
            logger.info(f"{file_type}下载完成，大小: {file_size} 字节")

        except requests.exceptions.RequestException as e:
            logger.error(f"下载文件网络错误: {e}")
            raise UBoxDeviceError(f"下载文件网络错误: {e}")
        except OSError as e:
            logger.error(f"保存文件IO错误: {e}")
            raise UBoxDeviceError(f"保存文件IO错误: {e}")
        except Exception as e:
            logger.error(f"下载文件未知错误: {e}")
            raise UBoxDeviceError(f"下载文件未知错误: {e}")

    def execute(self, trace_id: Optional[str] = None, **kwargs) -> Any:
        """执行操作的统一接口

        Args:
            trace_id: 可选的traceId，用于跟踪操作
            **kwargs: 操作参数

        Returns:
            操作结果

        Raises:
            UBoxDeviceError: 操作失败时抛出异常
        """
        try:
            # 处理traceId
            if trace_id is None:
                # 如果没有传入traceId，则自动生成一个
                import time
                import uuid
                trace_id = time.strftime("%Y%m%d%H%M%S") + "_" + str(uuid.uuid4())

            # 保存traceId到实例变量，供其他方法使用
            self._current_trace_id = trace_id

            # 构建请求参数
            request_data = self._prepare_request(**kwargs)

            # 发送请求
            response = self._make_request(**request_data)

            # 处理响应
            response_data = self._process_response(response)

            # 后处理
            result = self._post_process(response_data, **kwargs)

            return result

        except UBoxDeviceError:
            # 重新抛出已知的异常类型
            raise
        except Exception as e:
            # 捕获其他未知异常，转换为设备异常
            config = self.operation_config
            logger.error(f"设备 {self.udid} {config['name']} 时发生未知错误: {e}")
            raise UBoxDeviceError(f"{config['name']}失败: {str(e)}\n{traceback.format_exc()}")


class ScreenshotOperation(DeviceOperation):
    """截图操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "截图",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response  # 使用标准响应检查器
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备截图请求参数"""
        label = kwargs.get('label', '')
        img_path = kwargs.get('img_path', '')
        if self.mode == RunMode.NORMAL:
            img_path = FileTransferHandler(self.device).create_remote_dir()
        else:
            img_path = os.path.abspath(img_path)
            make_dir(img_path)
        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": self._build_request_params(
                method="screenshot",
                label=label,
                img_path=img_path,
            )
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> str:
        """处理截图响应数据"""
        final_path = _extract_field(response_data, 'result', '')
        if final_path is None:
            raise UBoxDeviceError("截图失败，可能设备已掉线")
        local_file_path = final_path
        if self.mode == RunMode.NORMAL:
            img_path = kwargs.get('img_path', '')
            local_file_path = os.path.join(img_path, os.path.basename(final_path))
            FileTransferHandler(self.device).pull(str(final_path), local_file_path, "file")
        return local_file_path


class ScreenshotBase64Operation(DeviceOperation):
    """Base64截图操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "Base64截图",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response  # 使用JSON-RPC响应检查器
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备Base64截图请求参数"""
        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": self._build_request_params(method="get_img")
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> str:
        """处理Base64截图响应数据"""
        # 检查返回体结构，解析base64截图响应
        if 'result' not in response_data:
            raise UBoxDeviceError(
                f"无法解析{self.operation_config['name']}返回体: {response_data}"
            )

        result_data = response_data['result']
        if not isinstance(result_data, dict) or 'data' not in result_data:
            raise UBoxDeviceError(
                f"无法解析{self.operation_config['name']}返回的result字段: {result_data}"
            )

        base64_data = result_data['data']
        if not base64_data:
            raise UBoxDeviceError(
                f"{self.operation_config['name']}失败：返回的data字段为空"
            )

        logger.debug(f"图片尺寸: {result_data.get('width', 'unknown')}x{result_data.get('height', 'unknown')}")
        logger.debug(f"耗时: {result_data.get('time_cost_ms', 'unknown')}ms")

        return base64_data


class RecordStartOperation(DeviceOperation):
    """开始录制操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "开始录制",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        RecordStopOperation(self.device).execute(reset_path=False)
        if self.mode == RunMode.NORMAL:
            fileTransfer = FileTransferHandler(self.device)
            client_temp_dir = fileTransfer.create_remote_dir()
            record_file_name = f"{self.udid}_{int(time.time())}.mp4"
            self.device.client_video_path = os.path.join(client_temp_dir, record_file_name)
            video_path = self.device.client_video_path
        else:
            video_path = os.path.abspath(self.device.video_path)
            make_dir(os.path.dirname(video_path))
        """准备开始录制请求参数"""
        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": self._build_request_params(
                method="record_start",
                video_path=video_path,
            )
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> bool:
        """处理开始录制响应数据"""
        if 'id' not in response_data:
            raise UBoxDeviceError(
                f"无法解析{self.operation_config['name']}返回体: {response_data}"
            )
        # Android系统：返回值为None表示成功
        if self.os_type == OSType.ANDROID:
            return True
        else:
            # 其他系统类型：返回布尔值
            result = response_data['result']
            return bool(result)


class RecordStopOperation(DeviceOperation):
    """停止录制操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "停止录制",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response  # 使用JSON-RPC响应检查器
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备停止录制请求参数"""
        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": self._build_request_params(
                method="record_stop",
            )
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> bool:
        """处理停止录制响应数据"""
        if 'id' not in response_data:
            raise UBoxDeviceError(
                f"无法解析{self.operation_config['name']}返回体: {response_data}"
            )
        # Android系统：返回值为None表示成功
        if self.os_type == OSType.ANDROID:
            success = True
        else:
            # 其他系统类型：返回布尔值
            result = response_data['result']
            success = bool(result)
        if success:
            if self.mode == RunMode.NORMAL:
                # 如果停止录制成功，则拉取视频文件到本地
                if hasattr(self.device, 'client_video_path') and self.device.client_video_path:
                    try:
                        if hasattr(self.device, 'video_path') and self.device.video_path:
                            fileTransfer = FileTransferHandler(self.device)
                            fileTransfer.pull(
                                target_path=self.device.client_video_path,
                                save_path=self.device.video_path,
                                path_type="file"
                            )
                            logger.debug(f"视频文件已下载到: {self.device.video_path}")
                        else:
                            logger.warning("未设置video_path，无法下载视频文件到本地")
                    except Exception as e:
                        logger.error(f"下载视频文件失败: {e}")
        reset_path = kwargs.get('reset_path', True)
        # 重置路径
        if hasattr(self.device, 'client_video_path') and reset_path:
            self.device.client_video_path = None
            self.device.video_path = None

        return success


class CmdAdbOperation(DeviceOperation):
    """ADB命令执行操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "ADB命令执行",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response  # 使用JSON-RPC响应检查器
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备ADB命令执行请求参数"""
        cmd = kwargs.get('cmd', '')
        timeout = kwargs.get('timeout', 10)

        if isinstance(cmd, list):
            cmd = ' '.join(cmd)

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": self._build_request_params(
                method="cmd_adb",
                cmd=cmd,
                timeout=timeout
            )
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> Union[tuple, str]:
        """处理ADB命令执行响应数据"""
        # 检查返回体结构，提取 result 字段
        if 'result' not in response_data:
            raise UBoxDeviceError(
                f"无法解析{self.operation_config['name']}返回体: {response_data}"
            )

        result_data = response_data['result']

        # 根据设备类型处理不同的返回格式
        if self.os_type.value == "android":
            # 安卓设备：期望返回 [output, exit_code] 格式
            if isinstance(result_data, list) and len(result_data) == 2:
                output = result_data[0]  # 命令输出
                exit_code = result_data[1]  # 退出码
                logger.info(f"安卓设备 {self.udid} 执行命令成功，退出码: {exit_code}")
                return output, exit_code
            else:
                raise UBoxDeviceError(
                    f"安卓设备命令执行返回的 result 格式错误: {result_data}"
                )
        else:
            # 鸿蒙设备：直接返回字符串
            if isinstance(result_data, str):
                logger.info(f"鸿蒙设备 {self.udid} 执行命令成功")
                return result_data
            else:
                raise UBoxDeviceError(
                    f"鸿蒙设备命令执行返回的 result 格式错误: {result_data}"
                )


class DeviceInfoOperation(DeviceOperation):
    """设备信息获取操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "获取设备信息",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response  # 使用JSON-RPC响应检查器
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备设备信息请求参数"""
        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": self._build_request_params(method="device_info")
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """处理设备信息响应数据"""
        # 如果返回体包含result字段，提取其中的设备信息
        if 'result' in response_data:
            device_data = response_data['result']
            logger.debug(f"设备 {self.udid} 获取到result数据: {device_data}")
            return device_data
        # 如果直接返回设备信息，直接使用
        elif isinstance(response_data, dict):
            logger.debug(f"设备 {self.udid} 直接返回设备数据: {response_data}")
            return response_data
        else:
            raise UBoxDeviceError(
                f"无法解析{self.operation_config['name']}返回体: {response_data}"
            )


class ScreenSizeOperation(DeviceOperation):
    """设备信息获取操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "获取屏幕分辨率",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response  # 使用JSON-RPC响应检查器
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备设备信息请求参数"""
        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": self._build_request_params(method="screen_size")
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> List[int]:
        """处理设备信息响应数据"""
        # 如果返回体包含result字段，提取其中的设备信息
        if 'result' in response_data:
            return response_data['result']
        elif isinstance(response_data, dict):
            return response_data
        else:
            raise UBoxDeviceError(
                f"无法解析{self.operation_config['name']}返回体: {response_data}"
            )


class ClickPosOperation(DeviceOperation):
    """坐标点击操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "坐标点击",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备坐标点击请求参数"""
        pos = kwargs.get('pos')
        duration = kwargs.get('duration', 0.05)
        times = kwargs.get('times', 1)

        # 验证坐标参数
        if not isinstance(pos, (list, tuple)) or len(pos) != 2:
            raise UBoxValidationError("坐标参数必须是包含两个元素的列表或元组", field="pos")

        # 验证坐标值范围（左闭右开，不含1）
        if not (0 <= pos[0] < 1.0 and 0 <= pos[1] < 1.0):
            raise UBoxValidationError("坐标值必须在[0, 1.0)区间内（左闭右开，不含1），可以传0.99", field="pos")

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": self._build_request_params(
                method="click_pos",
                pos=list(pos),
                duration=duration,
                times=times
            )
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> bool:
        """处理坐标点击响应数据"""
        # JSON-RPC格式，检查result字段
        if 'result' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        result = response_data['result']
        if self.os_type == OSType.HM and result is None:
            return True
        # 通常返回布尔值表示是否成功
        return bool(result)


class SlidePosOperation(DeviceOperation):
    """坐标滑动操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "坐标滑动",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备坐标滑动请求参数"""
        pos_from = kwargs.get('pos_from')
        pos_to = kwargs.get('pos_to')
        down_duration = kwargs.get('down_duration', 0)
        slide_duration = kwargs.get('slide_duration', 0.3)

        # 验证起始坐标
        if not isinstance(pos_from, (list, tuple)) or len(pos_from) != 2:
            raise UBoxValidationError("起始坐标必须是包含两个元素的列表或元组", field="pos_from")

        if not (0 <= pos_from[0] < 1.0 and 0 <= pos_from[1] < 1.0):
            raise UBoxValidationError("起始坐标值必须在[0, 1.0)区间内（左闭右开，不含1），可以传0.99", field="pos_from")

        # 验证结束坐标（如果提供）
        if pos_to is not None:
            if not isinstance(pos_to, (list, tuple)) or len(pos_to) != 2:
                raise UBoxValidationError("结束坐标必须是包含两个元素的列表或元组", field="pos_to")

            if not (0 <= pos_to[0] < 1.0 and 0 <= pos_to[1] < 1.0):
                raise UBoxValidationError("结束坐标值必须在[0, 1.0)区间内（左闭右开，不含1），可以传0.99", field="pos_to")

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": self._build_request_params(
                method="slide_pos",
                pos_from=list(pos_from),
                pos_to=list(pos_to) if pos_to else None,
                down_duration=down_duration,
                slide_duration=slide_duration,
            )
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> bool:
        """处理坐标滑动响应数据"""
        if 'result' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        result = response_data['result']
        if self.os_type == OSType.HM and result is None:
            return True
        return bool(result)


class ClickOperation(DeviceOperation):
    """点击操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "点击",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备点击请求参数"""
        loc = kwargs.get('loc')
        by = kwargs.get('by', 1)  # 默认UI类型
        offset = kwargs.get('offset')
        timeout = kwargs.get('timeout', 30)
        duration = kwargs.get('duration', 0.05)
        times = kwargs.get('times', 1)

        if not loc:
            raise UBoxValidationError("定位元素不能为空", field="loc")

        request_data = self._build_request_params(
            method="click",
            loc=loc,
            by=by,
            timeout=timeout,
            duration=duration,
            times=times
        )

        if offset:
            request_data['offset'] = list(offset)

        # 当by=DriverType.CV（CV类型）时，需要处理图像文件参数
        if by == DriverType.CV:
            # 获取CV相关参数，当by=3时，loc就是tpl的值
            tpl = loc  # loc参数就是模板图像路径
            img = kwargs.get('img')
            tpl_l = kwargs.get('tpl_l')

            # 验证模板图像参数
            if not tpl:
                raise UBoxValidationError("CV类型点击时模板图像路径不能为空", field="loc")

            if self.mode == RunMode.NORMAL:
                # 正常模式：需要文件传输
                fileTransfer = FileTransferHandler(self.device)
                client_temp_dir = fileTransfer.create_remote_dir()

                # 处理模板图像
                tpl_path = fileTransfer.push(tpl, _file_target_path_join(client_temp_dir, os.path.basename(tpl)))
                request_data['loc'] = tpl_path

                # 处理背景图像（如果提供）
                if img:
                    img_path = fileTransfer.push(img, _file_target_path_join(client_temp_dir, os.path.basename(img)))
                    request_data['img'] = img_path

                # 处理大尺寸模板图像（如果提供）
                if tpl_l:
                    tpl_l_path = fileTransfer.push(tpl_l,
                                                   _file_target_path_join(client_temp_dir, os.path.basename(tpl_l)))
                    request_data['tpl_l'] = tpl_l_path
            else:
                # 本地模式：直接使用本地路径，SDK和client在同一台机器上
                request_data['loc'] = os.path.abspath(tpl)

                # 处理背景图像（如果提供）
                if img:
                    request_data['img'] = os.path.abspath(img)

                # 处理大尺寸模板图像（如果提供）
                if tpl_l:
                    request_data['tpl_l'] = os.path.abspath(tpl_l)

        # 定义已经明确处理的参数列表，这些参数不需要透传
        processed_params = {
            'loc', 'by', 'offset', 'timeout', 'duration', 'times'
        }

        # 如果是CV类型，只添加需要特殊处理的文件参数到已处理列表
        if by == DriverType.CV:
            processed_params.update({
                'img', 'tpl_l'  # 只有这些参数需要特殊处理（文件传输）
            })

        # 透传其他所有未明确处理的参数
        for key, value in kwargs.items():
            if key not in processed_params:
                request_data[key] = value

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": request_data
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> bool:
        """处理点击响应数据"""
        if 'result' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        result = response_data['result']
        return bool(result)


class InputTextOperation(DeviceOperation):
    """文本输入操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "文本输入",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备文本输入请求参数"""
        text = kwargs.get('text')
        timeout = kwargs.get('timeout', 30)
        depth = kwargs.get('depth', 10)

        if not text:
            raise UBoxValidationError("输入文本不能为空", field="text")

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": self._build_request_params(
                method="input_text",
                text=text,
                timeout=timeout,
                depth=depth
            )
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> bool:
        """处理文本输入响应数据"""
        if 'result' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        result = response_data['result']
        return bool(result)


class PressOperation(DeviceOperation):
    """按键操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "按键操作",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备按键操作请求参数"""
        name = kwargs.get('name')

        if name is None:
            raise UBoxValidationError("按键类型不能为空", field="name")

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": self._build_request_params(
                method="press",
                name=name
            )
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> bool:
        """处理按键操作响应数据"""
        if 'result' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        result = response_data['result']
        return bool(result)


class SlideOperation(DeviceOperation):
    """滑动操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "滑动",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备滑动请求参数"""
        loc_from = kwargs.get('loc_from')
        loc_to = kwargs.get('loc_to')
        by = kwargs.get('by', 1)  # 默认UI类型
        timeout = kwargs.get('timeout', 120)
        down_duration = kwargs.get('down_duration', 0)

        if not loc_from:
            raise UBoxValidationError("起始位置不能为空", field="loc_from")

        request_data = self._build_request_params(
            method="slide",
            loc_from=loc_from,
            by=by,
            timeout=timeout,
            down_duration=down_duration,
        )

        if loc_to:
            request_data['loc_to'] = loc_to

        # 定义已经明确处理的参数列表，这些参数不需要透传
        processed_params = {
            'loc_from', 'loc_to', 'by', 'timeout', 'down_duration'
        }

        # 透传其他所有未明确处理的参数
        for key, value in kwargs.items():
            if key not in processed_params:
                request_data[key] = value

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": request_data
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> bool:
        """处理滑动响应数据"""
        if 'result' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        result = response_data['result']
        return bool(result)


class InstallAppOperation(DeviceOperation):
    """应用安装操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "应用安装",
            "method": "POST",
            "endpoint": "/installApp",
            "response_checker": check_standard_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备应用安装请求参数"""
        app_url = kwargs.get('app_url')
        app_path = kwargs.get('app_path')
        need_resign = kwargs.get('need_resign', False)
        resign_bundle = kwargs.get('resign_bundle', '')

        if not app_url and not app_path:
            raise UBoxValidationError("必须提供app_url或app_path其中之一", field="app_url/app_path")

        if need_resign and not resign_bundle:
            raise UBoxValidationError("需要重签名时必须提供resign_bundle", field="resign_bundle")

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": self._build_request_params(
                app_url=app_url,
                app_path=app_path,
                need_resign=need_resign,
                resign_bundle=resign_bundle
            )
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> bool:
        """处理应用安装响应数据"""
        if 'success' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        result = response_data['success']
        return bool(result)


class LocalInstallAppOperation(DeviceOperation):
    """应用安装操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "应用安装",
            "method": "POST",
            "endpoint": "/installApp",
            "response_checker": check_standard_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备应用安装请求参数"""
        local_app_path = kwargs.get('local_app_path')
        need_resign = kwargs.get('need_resign', False)
        resign_bundle = kwargs.get('resign_bundle', '')

        if need_resign and not resign_bundle:
            raise UBoxValidationError("需要重签名时必须提供resign_bundle", field="resign_bundle")

        if self.mode == RunMode.NORMAL:
            # 正常模式：需要文件传输
            fileTransferHandler = FileTransferHandler(self.device)
            client_temp_dir = fileTransferHandler.create_remote_dir()
            target_path = _file_target_path_join(client_temp_dir, os.path.basename(local_app_path))
            fileTransferHandler.push(local_app_path, target_path)
        else:
            # 本地模式：直接使用本地路径，SDK和client在同一台机器上
            target_path = os.path.abspath(local_app_path)

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": self._build_request_params(
                app_path=target_path,
                need_resign=need_resign,
                resign_bundle=resign_bundle
            )
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> bool:
        """处理应用安装响应数据"""
        if 'success' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        result = response_data['success']
        return bool(result)


class UninstallAppOperation(DeviceOperation):
    """应用卸载操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "应用卸载",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备应用卸载请求参数"""
        pkg = kwargs.get('pkg')

        if not pkg:
            raise UBoxValidationError("包名不能为空", field="pkg")

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": self._build_request_params(
                method="uninstall_app",
                pkg=pkg
            )
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> bool:
        """处理应用卸载响应数据"""
        if 'result' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        result = response_data['result']
        return bool(result)


class StartAppOperation(DeviceOperation):
    """应用启动操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "应用启动",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备应用启动请求参数"""
        pkg = kwargs.get('pkg')
        clear_data = kwargs.get('clear_data', False)

        if not pkg:
            raise UBoxValidationError("包名不能为空", field="pkg")

        request_data = self._build_request_params(
            method="start_app",
            pkg=pkg,
            clear_data=clear_data
        )

        # 定义已经明确处理的参数列表，这些参数不需要透传
        processed_params = {
            'pkg', 'clear_data'
        }

        # 透传其他所有未明确处理的参数
        for key, value in kwargs.items():
            if key not in processed_params:
                request_data[key] = value

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": request_data
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> bool:
        """处理应用启动响应数据"""
        if 'result' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        result = response_data['result']
        return bool(result)


class StopAppOperation(DeviceOperation):
    """应用停止操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "应用停止",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备应用停止请求参数"""
        pkg = kwargs.get('pkg')

        if not pkg:
            raise UBoxValidationError("包名不能为空", field="pkg")

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": self._build_request_params(
                method="stop_app",
                pkg=pkg
            )
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> bool:
        """处理应用停止响应数据"""
        if 'result' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        result = response_data['result']
        return bool(result)


class OpenUrlOperation(DeviceOperation):
    """URL打开操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "URL打开",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备URL打开请求参数"""
        url = kwargs.get('url')

        if not url:
            raise UBoxValidationError("URL不能为空", field="url")

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": self._build_request_params(
                method="open_url",
                url=url
            )
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> bool:
        """处理URL打开响应数据"""
        if 'result' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        result = response_data['result']
        return bool(result)


class FindCVOperation(DeviceOperation):
    """基于多尺寸模板匹配的图像查找操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "图像查找",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:

        """准备图像查找请求参数"""
        global fileTransfer, client_temp_dir
        tpl = kwargs.get('tpl')
        img = kwargs.get('img')
        timeout = kwargs.get('timeout', 30)
        threshold = kwargs.get('threshold', 0.8)
        pos = kwargs.get('pos')
        pos_weight = kwargs.get('pos_weight', 0.05)
        ratio_lv = kwargs.get('ratio_lv', 21)
        is_translucent = kwargs.get('is_translucent', False)
        to_gray = kwargs.get('to_gray', False)
        tpl_l = kwargs.get('tpl_l')
        deviation = kwargs.get('deviation')
        time_interval = kwargs.get('time_interval', 0.5)
        if not tpl:
            raise UBoxValidationError("模板图像不能为空", field="tpl")

        if self.mode == RunMode.NORMAL:
            # 正常模式：需要文件传输
            fileTransfer = FileTransferHandler(self.device)
            client_temp_dir = fileTransfer.create_remote_dir()
            tpl_path = fileTransfer.push(tpl, _file_target_path_join(client_temp_dir, os.path.basename(tpl)))
        else:
            # 本地模式：直接使用本地路径，SDK和client在同一台机器上
            tpl_path = os.path.abspath(tpl)

        request_data = self._build_request_params(
            method="find_cv",
            tpl=tpl_path,
            timeout=timeout,
            threshold=threshold,
            pos_weight=pos_weight,
            ratio_lv=ratio_lv,
            is_translucent=is_translucent,
            to_gray=to_gray,
            time_interval=time_interval
        )

        if img:
            if self.mode == RunMode.NORMAL:
                img_path = fileTransfer.push(img, str(_file_target_path_join(client_temp_dir, os.path.basename(img))))
            else:
                img_path = os.path.abspath(img)
            request_data['img'] = img_path

        if pos:
            request_data['pos'] = list(pos)

        if tpl_l:
            if self.mode == RunMode.NORMAL:
                tpl_l_path = fileTransfer.push(tpl_l,
                                               str(_file_target_path_join(client_temp_dir, os.path.basename(tpl_l))))
            else:
                tpl_l_path = os.path.abspath(tpl_l)
            request_data['tpl_l'] = tpl_l_path

        if deviation:
            request_data['deviation'] = list(deviation)

        # 定义已经明确处理的参数列表，这些参数不需要透传
        processed_params = {
            'tpl', 'img', 'timeout', 'threshold', 'pos', 'pos_weight',
            'ratio_lv', 'is_translucent', 'to_gray', 'tpl_l', 'deviation',
            'time_interval'
        }

        # 透传其他所有未明确处理的参数
        for key, value in kwargs.items():
            if key not in processed_params:
                request_data[key] = value

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": request_data
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> Any:
        """处理图像查找响应数据"""
        if 'result' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        result = response_data['result']
        return result


class FindOCROperation(DeviceOperation):
    """基于OCR文字识别的查找操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "OCR文字查找",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备OCR查找请求参数"""
        word = kwargs.get('word')
        left_word = kwargs.get('left_word')
        right_word = kwargs.get('right_word')
        timeout = kwargs.get('timeout', 30)
        time_interval = kwargs.get('time_interval', 0.5)

        if not word:
            raise UBoxValidationError("待查找文字不能为空", field="word")

        request_data = self._build_request_params(
            method="find_ocr",
            word=word,
            timeout=timeout,
            time_interval=time_interval
        )

        if left_word:
            request_data['left_word'] = left_word
        if right_word:
            request_data['right_word'] = right_word

        # 定义已经明确处理的参数列表，这些参数不需要透传
        processed_params = {
            'word', 'left_word', 'right_word', 'timeout', 'time_interval'
        }

        # 透传其他所有未明确处理的参数
        for key, value in kwargs.items():
            if key not in processed_params:
                request_data[key] = value

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": request_data
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> Any:
        """处理OCR查找响应数据"""
        if 'result' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        result = response_data['result']
        return result


class FindUIOperation(DeviceOperation):
    """基于控件查找操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "UI控件查找",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备UI查找请求参数"""
        xpath = kwargs.get('xpath')
        timeout = kwargs.get('timeout', 30)

        if not xpath:
            raise UBoxValidationError("控件xpath不能为空", field="xpath")

        request_data = self._build_request_params(
            method="find_ui",
            xpath=xpath,
            timeout=timeout
        )

        # 定义已经明确处理的参数列表，这些参数不需要透传
        processed_params = {
            'xpath', 'timeout'
        }

        # 透传其他所有未明确处理的参数
        for key, value in kwargs.items():
            if key not in processed_params:
                request_data[key] = value

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": request_data
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> Any:
        """处理UI查找响应数据"""
        if 'result' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        result = response_data['result']
        return result


class FindOperation(DeviceOperation):
    """通用查找操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "通用查找",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备通用查找请求参数"""
        loc = kwargs.get('loc')
        by = kwargs.get('by', 1)  # 默认UI类型
        timeout = kwargs.get('timeout', 30)

        if not loc:
            raise UBoxValidationError("查找元素不能为空", field="loc")

        request_data = self._build_request_params(
            method="find",
            loc=loc,
            by=by,
            timeout=timeout
        )

        # 定义已经明确处理的参数列表，这些参数不需要透传
        processed_params = {
            'loc', 'by', 'timeout'
        }

        # 透传其他所有未明确处理的参数
        for key, value in kwargs.items():
            if key not in processed_params:
                request_data[key] = value

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": request_data
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> Any:
        """处理通用查找响应数据"""
        if 'result' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        result = response_data['result']
        return result


class MultiFindOperation(DeviceOperation):
    """综合查找操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "综合查找",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备综合查找请求参数"""
        ctrl = kwargs.get('ctrl', '')
        img = kwargs.get('img')
        pos = kwargs.get('pos')
        by = kwargs.get('by', 1)  # 默认UI类型
        ctrl_timeout = kwargs.get('ctrl_timeout', 30)
        img_timeout = kwargs.get('img_timeout', 10)

        request_data = self._build_request_params(
            method="multi_find",
            ctrl=ctrl,
            by=by,
            ctrl_timeout=ctrl_timeout,
            img_timeout=img_timeout
        )

        if img:
            request_data['img'] = img
        if pos:
            request_data['pos'] = list(pos)

        # 定义已经明确处理的参数列表，这些参数不需要透传
        processed_params = {
            'ctrl', 'img', 'pos', 'by', 'ctrl_timeout', 'img_timeout'
        }

        # 透传其他所有未明确处理的参数
        for key, value in kwargs.items():
            if key not in processed_params:
                request_data[key] = value

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": request_data
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> Any:
        """处理综合查找响应数据"""
        if 'result' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        result = response_data['result']
        return result


class GetUITreeOperation(DeviceOperation):
    """获取控件树操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "获取控件树",
            "method": "GET",
            "endpoint": "/uiTree",
            "response_checker": check_standard_response  # GET请求直接返回文本，不需要JSON检查
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备获取控件树请求参数"""
        xml = kwargs.get('xml', False)
        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "params": self._build_request_params(
                xml=str(xml).lower(),
            )
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> Union[Dict[str, Any], str]:
        """处理获取控件树响应数据
        
        Args:
            response_data: 响应数据字典，包含 success、msg 和 data 字段
            
        Returns:
            - 当 xml=False 时，返回 data 字段（JSON对象，dict类型）
            - 当 xml=True 时，返回 data 字段（XML字符串，str类型）
            
        Raises:
            UBoxDeviceError: 响应格式错误时抛出异常
        """
        # 检查响应格式
        if 'data' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")
        
        # 返回 data 字段（可能是 dict 或 str）
        return response_data['data']


class GetElementOperation(DeviceOperation):
    """根据xpath获取元素操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "获取元素",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备获取元素请求参数"""
        xpath = kwargs.get('xpath')
        timeout = kwargs.get('timeout', 30)

        if not xpath:
            raise UBoxValidationError("xpath不能为空", field="xpath")

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": self._build_request_params(
                method="get_element",
                xpath=xpath,
                timeout=timeout
            )
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> Any:
        """处理获取元素响应数据"""
        if 'result' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        result = response_data['result']
        return result


class GetElementsOperation(DeviceOperation):
    """根据xpath获取元素列表操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "获取元素列表",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备获取元素列表请求参数"""
        xpath = kwargs.get('xpath')

        if not xpath:
            raise UBoxValidationError("xpath不能为空", field="xpath")

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": self._build_request_params(
                method="get_elements",
                xpath=xpath
            )
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> Any:
        """处理获取元素列表响应数据"""
        if 'result' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        result = response_data['result']
        return result


class GetTextOperation(DeviceOperation):
    """查找图像中的所有文本操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "获取图像文本",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备获取图像文本请求参数"""
        img = kwargs.get('img')
        iou_th = kwargs.get('iou_th', 0.1)

        if not img:
            raise UBoxValidationError("图像不能为空", field="img")

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": self._build_request_params(
                method="get_text",
                img=img,
                iou_th=iou_th
            )
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> Any:
        """处理获取图像文本响应数据"""
        if 'result' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        result = response_data['result']
        return result


class SetClipboardOperation(DeviceOperation):
    """设置剪贴板操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "设置剪贴板",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备设置剪贴板请求参数"""
        text = kwargs.get('text')

        if not text:
            raise UBoxValidationError("剪贴板文本不能为空", field="text")

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": self._build_request_params(
                method="set_clipboard",
                text=text
            )
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs):
        """处理设置剪贴板响应数据"""
        if 'id' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")
        return


class GetClipboardOperation(DeviceOperation):
    """获取剪贴板操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "获取剪贴板",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备获取剪贴板请求参数"""
        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": self._build_request_params(
                method="get_clipboard"
            )
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> Any:
        """处理获取剪贴板响应数据"""
        if 'result' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        result = response_data['result']
        return result


class SetHttpGlobalProxyOperation(DeviceOperation):
    """设置全局代理操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "设置全局代理",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备设置全局代理请求参数"""
        host = kwargs.get('host')
        port = kwargs.get('port')
        username = kwargs.get('username')
        password = kwargs.get('password')

        if not host or not port:
            raise UBoxValidationError("代理主机和端口不能为空", field="host/port")

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": self._build_request_params(
                method="set_http_global_proxy",
                host=host,
                port=port,
                username=username or '',
                password=password or ''
            )
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> Any:
        """处理设置全局代理响应数据"""
        if 'result' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        result = response_data['result']
        return result


class GetHttpGlobalProxyOperation(DeviceOperation):
    """获取全局代理操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "获取全局代理",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备获取全局代理请求参数"""
        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": self._build_request_params(
                method="get_http_global_proxy"
            )
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> Any:
        """处理获取全局代理响应数据"""
        if 'result' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        result = response_data['result']
        return result


class ClearHttpGlobalProxyOperation(DeviceOperation):
    """清除全局代理操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "清除全局代理",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备清除全局代理请求参数"""
        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": self._build_request_params(
                method="clear_http_global_proxy"
            )
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> Any:
        """处理清除全局代理响应数据"""
        if 'result' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        result = response_data['result']
        return result


class GetFilePathInfoOperation(DeviceOperation):
    """获取文件属性操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "获取文件属性",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备获取文件属性请求参数"""
        path = kwargs.get('path')

        if not path:
            raise UBoxValidationError("文件路径不能为空", field="path")

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": self._build_request_params(
                method="get_file_path_info",
                path=path
            )
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> Any:
        """处理获取文件属性响应数据"""
        if 'result' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        result = response_data['result']
        return result


class WaitForIdleOperation(DeviceOperation):
    """等待页面进入空闲状态操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "等待页面空闲",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备等待页面空闲请求参数"""
        idle_time = kwargs.get('idle_time', 0.5)
        timeout = kwargs.get('timeout', 10.0)

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": self._build_request_params(
                method="wait_for_idle",
                idle_time=idle_time,
                timeout=timeout
            )
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> Any:
        """处理等待页面空闲响应数据"""
        if 'result' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        result = response_data['result']
        return result


class LoadDefaultHandlerOperation(DeviceOperation):
    """批量加载事件自动处理规则操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "批量加载事件自动处理规则",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response  # 使用JSON-RPC响应检查器
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备批量加载事件自动处理规则请求参数"""
        rule = kwargs.get('rule', [])

        if not rule:
            raise UBoxValidationError("事件处理规则不能为空", field="rule")

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": self._build_request_params(
                method="load_default_handler",
                rule=rule
            )
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> None:
        """处理批量加载事件自动处理规则响应数据"""
        # JSON-RPC格式，检查result字段
        if 'id' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")


class StartEventHandlerOperation(DeviceOperation):
    """启动预设事件自动处理操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "启动预设事件自动处理",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response  # 使用JSON-RPC响应检查器
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备启动预设事件自动处理请求参数"""
        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": self._build_request_params(
                method="start_event_handler"
            )
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> None:
        """处理启动预设事件自动处理响应数据"""
        if 'id' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        # 事件处理操作不需要返回值，只需要确保操作成功
        logger.info(f"设备 {self.udid} 启动预设事件自动处理成功")


class AddEventHandlerOperation(DeviceOperation):
    """添加事件自动处理规则操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "添加事件自动处理规则",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response  # 使用JSON-RPC响应检查器
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备添加事件自动处理规则请求参数"""
        match_element = kwargs.get('match_element')
        action_element = kwargs.get('action_element')

        if not match_element:
            raise UBoxValidationError("匹配元素不能为空", field="match_element")

        request_data = self._build_request_params(
            method="add_event_handler",
            match_element=match_element
        )

        if action_element:
            request_data['action_element'] = action_element

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": request_data
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> None:
        """处理添加事件自动处理规则响应数据"""
        # JSON-RPC格式，检查result字段
        if 'id' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        # 事件处理操作不需要返回值，只需要确保操作成功
        logger.info(f"设备 {self.udid} 添加事件自动处理规则成功")


class SyncEventHandlerOperation(DeviceOperation):
    """事件自动处理立即处理一次操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "事件自动处理立即处理一次",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response  # 使用JSON-RPC响应检查器
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备事件自动处理立即处理一次请求参数"""
        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": self._build_request_params(
                method="sync_event_handler"
            )
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> None:
        """处理事件自动处理立即处理一次响应数据"""
        # JSON-RPC格式，检查result字段
        if 'result' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        # 事件处理操作不需要返回值，只需要确保操作成功
        logger.info(f"设备 {self.udid} 事件自动处理立即处理一次成功")


class ClearEventHandlerOperation(DeviceOperation):
    """清除事件自动处理规则操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "清除事件自动处理规则",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response  # 使用JSON-RPC响应检查器
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备清除事件自动处理规则请求参数"""
        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": self._build_request_params(
                method="clear_event_handler"
            )
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> None:
        """处理清除事件自动处理规则响应数据"""
        # JSON-RPC格式，检查result字段
        if 'id' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        # 事件处理操作不需要返回值，只需要确保操作成功
        logger.info(f"设备 {self.udid} 清除事件自动处理规则成功")


class CreateRemoteDirOperation(DeviceOperation):
    """创建远程设备client的目录"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "创建远程设备client的目录",
            "method": "GET",
            "endpoint": "/ubox/file/createTempDir",
            "response_checker": check_standard_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "params": self._build_request_params()
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> Optional[str]:
        """处理清除事件自动处理规则响应数据"""
        if 'data' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")
        return response_data['data'].get('temp_dir_path')


class CleanDeviceDirOperation(DeviceOperation):
    """清理设备client上的临时目录"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "清理设备client上的临时目录",
            "method": "GET",
            "endpoint": "/ubox/file/cleanTempDir",
            "response_checker": check_standard_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "params": self._build_request_params()
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> bool:
        """处理清除事件自动处理规则响应数据"""
        if 'data' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")
        return response_data['success']


class IOSOpenUrlHelper:
    """iOS设备智能打开URL辅助类"""

    def __init__(self, device, trace_id: Optional[str]):
        self.device = device
        self.trace_id = trace_id

    def open_url(self, url: str, permission_config: dict = None) -> bool:
        """
        执行iOS智能打开URL操作
        
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
            helper.open_url("https://example.com")
            
            # 自定义权限处理配置
            config = {
                "watcher_name": "权限弹窗",
                "allow_conditions": ["允许", "打开", "同意"],
                "wait_time": 30,
                "enabled": True
            }
            helper.open_url("https://example.com", permission_config=config)
        """
        if not url:
            raise UBoxValidationError("URL不能为空", field="url")

        if self.device.os_type.value != "ios":
            raise UBoxValidationError("此功能仅支持iOS设备", field="os_type")

        # 设置默认权限配置
        default_permission_config = {
            "watcher_name": "权限弹窗",
            "allow_conditions": ["允许", "打开"],
            "wait_time": 20,
            "enabled": True
        }

        # 合并用户配置和默认配置
        if permission_config:
            default_permission_config.update(permission_config)

        logger.info(f"开始iOS打开URL: {url}")

        try:
            # 1. 导航到主屏幕
            self._navigate_to_home()

            # 2. 查找并点击"打开URL"按钮
            if not self._find_and_click_open_url():
                raise UBoxDeviceError("未找到'打开URL'按钮")

            # 3. 点击输入框
            if not self._click_input_field():
                raise UBoxDeviceError("未找到输入框")

            # 4. 输入URL
            self._input_url(url)

            # 5. 点击完成按钮
            if not self._click_complete_button():
                raise UBoxDeviceError("未找到'完成'按钮")

            # 6. 自动处理权限弹窗
            if default_permission_config["enabled"]:
                self._handle_permission_dialogs(default_permission_config)

            logger.info(f"iOS智能打开URL成功: {url}")
            return True

        except Exception as e:
            logger.error(f"iOS智能打开URL失败: {e}")
            raise UBoxDeviceError(f"iOS智能打开URL失败: {str(e)}")

    def _navigate_to_home(self) -> None:
        """导航到主屏幕"""
        logger.debug("导航到主屏幕")
        self.device.press(DeviceButton.BACK, trace_id=self.trace_id)
        self.device.press(DeviceButton.HOME, trace_id=self.trace_id)
        self.device.press(DeviceButton.BACK, trace_id=self.trace_id)
        self.device.press(DeviceButton.HOME, trace_id=self.trace_id)
        time.sleep(1)

    def _find_and_click_open_url(self) -> bool:
        """查找并点击'打开URL'按钮"""
        logger.debug("查找'打开URL'按钮")

        uitree = self.device.get_uitree(True, trace_id=self.trace_id)
        if not uitree:
            return False

        from .handler import parse_xml, find_optimal_element
        xml_tree = parse_xml(uitree)
        if not xml_tree:
            return False

        # 使用智能匹配查找"打开URL"按钮
        xml_element, found = find_optimal_element(xml_tree, "打开URL")
        if not found or xml_element is None:
            return False

        # 计算点击坐标
        center = self.device.handler.find_xml_element_center(xml_element)
        if center is None:
            return False

        # 点击按钮（稍微向上偏移以避免点击到图标边缘）
        click_x, click_y = center[0], center[1] - 30
        from .models import DriverType
        self.device.click(loc=(click_x, click_y), by=DriverType.POS, trace_id=self.trace_id)
        logger.debug(f"点击'打开URL'按钮: [{click_x}, {click_y}]")

        time.sleep(4)
        return True

    def _click_input_field(self) -> bool:
        """点击输入框"""
        logger.debug("查找并点击输入框")

        uitree = self.device.get_uitree(True)
        if not uitree:
            return False

        from .handler import parse_xml, find_optimal_element
        xml_tree = parse_xml(uitree)
        if not xml_tree:
            return False

        # 查找"完成"按钮来确定输入框位置
        xml_element, found = find_optimal_element(xml_tree, "完成")
        if not found or xml_element is None:
            return False

        # 计算输入框位置（在"完成"按钮上方）
        center = self.device.handler.find_xml_element_center(xml_element)
        size = self.device.handler.find_xml_element_size(xml_element)
        if center is None or size is None:
            return False

        # 点击输入框（在"完成"按钮上方）
        click_x, click_y = center[0], center[1] - size[1]
        from .models import DriverType
        self.device.click(loc=(click_x, click_y), by=DriverType.POS, trace_id=self.trace_id)
        logger.debug(f"点击输入框: [{click_x}, {click_y}]")

        time.sleep(1)
        return True

    def _input_url(self, url: str) -> None:
        """输入URL"""
        logger.debug(f"输入URL: {url}")
        self.device.input_text(url, trace_id=self.trace_id)
        time.sleep(1)

    def _click_complete_button(self) -> bool:
        """点击完成按钮"""
        logger.debug("点击'完成'按钮")

        # 使用智能点击
        success = self.device.handler.smart_click("完成")
        if success:
            logger.debug("成功点击'完成'按钮")
            time.sleep(3)
            return True

        return False

    def _handle_permission_dialogs(self, config: dict) -> None:
        """
        自动处理权限弹窗
        
        Args:
            config: 权限弹窗处理配置
        """
        logger.debug(f"开始处理权限弹窗，配置: {config}")

        self.device.handler.reset()
        # 创建watcher并添加条件
        watcher = self.device.handler.watcher(config["watcher_name"])
        for condition in config["allow_conditions"]:
            watcher.when(condition)
        watcher.click()

        # 启动权限处理
        self.device.handler.start()

        # 等待指定时间让权限弹窗处理完成
        wait_time = config["wait_time"]
        logger.debug(f"等待权限弹窗处理完成，等待时间: {wait_time}秒")
        time.sleep(wait_time)

        # 停止权限处理
        self.device.handler.stop()
        logger.debug("权限弹窗处理完成")


class FileTransferHandler(DeviceOperation):
    """
    统一的文件传输处理器
    整合了文件推送（push）和拉取（pull）的所有功能
    
    注意：在LOCAL模式下，SDK和client在同一台机器上运行，
    因此不需要进行文件传输，可以直接使用本地路径。
    各个功能操作类会根据self.mode来判断是否需要文件传输。
    """

    # fileserver 配置常量
    FILESERVER_BASE_URL = "https://dl.utest.21kunpeng.com/utest-paas-fileserver"
    FILESERVER_ENDPOINTS = {
        "upload": "/file/uploadFile",
        "download": "/file/downloadFile",
        "delete": "/file/deleteFile"
    }

    @property
    def operation_config(self) -> Dict[str, Any]:
        """操作配置

        Returns:
            Dict包含操作的配置信息
        """
        return {
            "name": "文件传输",
            "description": "文件推送和拉取操作",
            "endpoints": {
                "push": "/ubox/file/push",
                "pull": "/ubox/file/pull"
            }
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备请求参数

        Args:
            **kwargs: 操作参数

        Returns:
            Dict: 请求参数
        """
        return {}

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> Any:
        """后处理响应数据

        Args:
            response_data: 响应数据
            **kwargs: 操作参数

        Returns:
            处理后的结果
        """
        return response_data

    def _validate_and_prepare_paths(self, file_path: str, target_path: str) -> tuple[str, str]:
        """验证和准备路径参数（用于push操作）
        
        Args:
            file_path: 本地文件路径
            target_path: 目标路径
            
        Returns:
            tuple: (target_path, path_type)
            
        Raises:
            UBoxValidationError: 路径验证失败时抛出异常
        """
        if not os.path.exists(file_path):
            raise UBoxValidationError(f"源文件不存在: {file_path}")

        path_type = "dir" if os.path.isdir(file_path) else "file"

        if path_type == "file" and target_path.endswith('/'):
            raise UBoxValidationError(f"本地是文件，目标路径不能以'/'结尾: {target_path}")
        elif path_type == "dir" and not target_path.endswith('/'):
            target_path = target_path.rstrip('/') + '/'

        return target_path, path_type

    def _validate_path_type_and_target(self, path_type: str, save_path: str) -> None:
        """验证路径类型和目标路径的匹配性（用于pull操作）
        
        Args:
            path_type: 路径类型
            save_path: 保存路径
            
        Raises:
            UBoxValidationError: 路径验证失败时抛出异常
        """
        if path_type not in ["file", "dir"]:
            raise UBoxValidationError(f"path_type参数无效，请指定file（文件路径）或dir（目录路径）")

        if path_type == "file":
            if save_path.endswith('/') or save_path.endswith('\\'):
                raise UBoxValidationError(f"文件路径不能以'/'结尾: {save_path}")

            parent_dir = os.path.dirname(save_path)
            if parent_dir and not os.path.exists(parent_dir):
                try:
                    os.makedirs(parent_dir, exist_ok=True)
                except Exception as e:
                    raise UBoxValidationError(f"创建父目录失败: {parent_dir}, 错误: {str(e)}")
        else:
            if os.path.exists(save_path):
                if os.path.isfile(save_path):
                    raise UBoxValidationError(f"目标路径是文件，但指定的是目录类型: {save_path}")

                try:
                    if any(os.scandir(save_path)):
                        raise UBoxValidationError(f"目标目录非空，无法拉取: {save_path}")
                except Exception as e:
                    raise UBoxValidationError(f"检查目录内容失败: {save_path}, 错误: {str(e)}")
            else:
                try:
                    os.makedirs(save_path, exist_ok=True)
                except Exception as e:
                    raise UBoxValidationError(f"创建目标目录失败: {save_path}, 错误: {str(e)}")

    def _prepare_file_data(self, file_path: str, path_type: str) -> Dict[str, Any]:
        """准备文件数据，使用正确的form-data格式
        
        Args:
            file_path: 文件路径
            path_type: 路径类型
            
        Returns:
            Dict: 包含文件数据的字典
            
        Raises:
            UBoxDeviceError: 文件准备失败时抛出异常
        """
        if path_type == "dir":
            # 如果是目录，先压缩为ZIP
            temp_dir = tempfile.mkdtemp()
            try:
                zip_filename = f"{os.path.basename(file_path)}.zip"
                zip_path = os.path.join(temp_dir, zip_filename)

                # 创建ZIP文件
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(file_path):
                        for file in files:
                            file_path_in_dir = os.path.join(root, file)
                            arcname = os.path.relpath(file_path_in_dir, file_path)
                            zipf.write(file_path_in_dir, arcname)

                # 返回文件对象，而不是文件内容
                # 这样requests会自动处理multipart/form-data格式
                return {
                    'files': {'file': (zip_filename, open(zip_path, 'rb'), 'application/zip')},
                    'temp_dir': temp_dir,
                    'file_paths': [zip_path]  # 记录需要清理的文件路径
                }

            except Exception as e:
                # 清理临时文件
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass
                raise UBoxDeviceError(f"准备目录文件数据失败: {str(e)}")
        else:
            # 如果是文件，直接返回文件对象
            try:
                return {
                    'files': {'file': (os.path.basename(file_path), open(file_path, 'rb'), 'application/octet-stream')},
                    'temp_dir': None,
                    'file_paths': []  # 没有临时文件需要清理
                }
            except Exception as e:
                raise UBoxDeviceError(f"准备文件数据失败: {str(e)}")

    def _cleanup_temp_files(self, file_data: Dict[str, Any]) -> None:
        """清理临时文件和关闭文件对象
        
        Args:
            file_data: 文件数据字典
        """
        # 关闭文件对象
        if 'files' in file_data:
            for file_info in file_data['files'].values():
                if isinstance(file_info, tuple) and len(file_info) >= 2:
                    file_obj = file_info[1]
                    if hasattr(file_obj, 'close') and callable(file_obj.close):
                        try:
                            file_obj.close()
                        except Exception as close_error:
                            logger.warning(f"关闭文件对象失败: {close_error}")

        # 清理临时目录
        temp_dir = file_data.get('temp_dir')
        if temp_dir:
            try:
                shutil.rmtree(temp_dir)
                logger.debug(f"临时目录已清理: {temp_dir}")
            except Exception as cleanup_error:
                logger.warning(f"清理临时目录失败: {cleanup_error}")

        # 清理临时文件路径
        file_paths = file_data.get('file_paths', [])
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.debug(f"临时文件已清理: {file_path}")
            except Exception as file_cleanup_error:
                logger.warning(f"清理临时文件失败: {file_path}, 错误: {file_cleanup_error}")

    def _read_response_content(self, response, target_path: str = "") -> bytes:
        """
        统一读取不同响应类型的文件内容
        
        Args:
            response: HTTP响应对象
            target_path: 目标路径（用于日志记录）
            
        Returns:
            bytes: 文件内容
            
        Raises:
            UBoxDeviceError: 读取失败时抛出异常
        """
        try:
            # 优先使用专门的查找方法
            return self._find_file_content_in_response(response, target_path)

        except Exception as e:
            if isinstance(e, UBoxDeviceError):
                raise
            logger.error(f"读取响应内容失败: {target_path}, 错误: {e}")
            raise UBoxDeviceError(f"读取响应内容失败: {str(e)}\n{traceback.format_exc()}")

    def _is_image_file(self, file_path: str) -> bool:
        """
        判断文件是否为图片文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 是否为图片文件
        """
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tga'}
        file_ext = os.path.splitext(file_path)[1].lower()
        return file_ext in image_extensions

    def _validate_image_file(self, file_path: str) -> bool:
        """
        验证图片文件是否有效
        
        Args:
            file_path: 文件路径
            
        Returns:
            bool: 图片文件是否有效
        """
        try:
            # 检查文件大小
            file_size = os.path.getsize(file_path)
            if file_size < 100:  # 图片文件通常至少100字节
                logger.warning(f"图片文件过小，可能损坏: {file_path}, 大小: {file_size}")
                return False

            # 检查文件头部魔数
            with open(file_path, 'rb') as f:
                header = f.read(8)

            # 常见图片格式的魔数
            magic_numbers = {
                b'\xff\xd8\xff': 'JPEG',
                b'\x89PNG\r\n\x1a\n': 'PNG',
                b'GIF87a': 'GIF',
                b'GIF89a': 'GIF',
                b'BM': 'BMP',
                b'RIFF': 'WEBP'
            }

            for magic, format_name in magic_numbers.items():
                if header.startswith(magic):
                    logger.debug(f"检测到图片格式: {format_name}, 文件: {file_path}")
                    return True

            logger.warning(f"无法识别图片格式，文件: {file_path}, 头部: {header}")
            return False

        except Exception as e:
            logger.error(f"验证图片文件失败: {file_path}, 错误: {e}")
            return False

    def _find_file_content_in_response(self, response, target_path: str = "") -> bytes:
        """
        在响应对象中查找文件内容
        
        Args:
            response: 响应对象
            target_path: 目标路径（用于日志记录）
            
        Returns:
            bytes: 文件内容
            
        Raises:
            UBoxDeviceError: 找不到文件内容时抛出异常
        """
        logger.debug(f"=== 在响应对象中查找文件内容: {target_path} ===")
        logger.debug(f"响应对象类型: {type(response)}")

        # 方法1: 检查是否有iter_content方法（requests.Response）
        if hasattr(response, 'iter_content') and callable(response.iter_content):
            logger.debug("使用 iter_content 方法读取文件内容")
            content = b''
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    content += chunk
            if content:
                logger.debug(f"通过iter_content成功读取到 {len(content)} 字节")
                return content

        # 方法2: 检查是否有content属性
        if hasattr(response, 'content'):
            logger.debug(f"检查content属性: {type(response.content)}")
            if isinstance(response.content, bytes) and response.content:
                logger.debug(f"通过content属性成功读取到 {len(response.content)} 字节")
                return response.content

        # 方法3: 检查是否有body属性
        if hasattr(response, 'body'):
            logger.debug(f"检查body属性: {type(response.body)}")
            if isinstance(response.body, bytes) and response.body:
                logger.debug(f"通过body属性成功读取到 {len(response.body)} 字节")
                return response.body
            elif hasattr(response.body, 'read'):
                logger.debug("body有read方法，尝试读取")
                try:
                    content = response.body.read()
                    if content:
                        logger.debug(f"通过body.read()成功读取到 {len(content)} 字节")
                        return content
                except Exception as e:
                    logger.warning(f"body.read()失败: {e}")

        # 方法4: 检查是否有read方法
        if hasattr(response, 'read'):
            logger.debug("响应对象有read方法，尝试读取")
            try:
                content = response.read()
                if content:
                    if isinstance(content, str):
                        logger.debug(f"read()返回字符串，编码为bytes")
                        return content.encode('utf-8')
                    else:
                        logger.debug(f"通过read()成功读取到 {len(content)} 字节")
                        return content
            except Exception as e:
                logger.warning(f"read()失败: {e}")

        # 方法5: 检查是否有raw属性
        if hasattr(response, 'raw') and hasattr(response.raw, 'read'):
            logger.debug("检查raw属性")
            try:
                content = response.raw.read()
                if content:
                    logger.debug(f"通过raw.read()成功读取到 {len(content)} 字节")
                    return content
            except Exception as e:
                logger.warning(f"raw.read()失败: {e}")

        # 方法6: 检查是否有files属性
        if hasattr(response, 'files'):
            logger.debug(f"检查files属性: {response.files}")
            if response.files and 'file' in response.files:
                file_obj = response.files['file']
                logger.debug(f"files['file']类型: {type(file_obj)}")
                if hasattr(file_obj, 'read'):
                    try:
                        file_obj.seek(0)
                        content = file_obj.read()
                        if content:
                            logger.debug(f"通过files['file'].read()成功读取到 {len(content)} 字节")
                            return content
                    except Exception as e:
                        logger.warning(f"files['file'].read()失败: {e}")

        # 方法7: 检查其他可能的文件相关属性
        file_related_attrs = ['file', 'attachment', 'download', 'stream', 'binary']
        for attr in file_related_attrs:
            if hasattr(response, attr):
                logger.debug(f"检查{attr}属性")
                attr_value = getattr(response, attr)
                if hasattr(attr_value, 'read'):
                    try:
                        content = attr_value.read()
                        if content:
                            logger.debug(f"通过{attr}.read()成功读取到 {len(content)} 字节")
                            return content
                    except Exception as e:
                        logger.warning(f"{attr}.read()失败: {e}")
                elif isinstance(attr_value, bytes) and attr_value:
                    logger.debug(f"通过{attr}属性成功获取到 {len(attr_value)} 字节")
                    return attr_value

        # 如果都找不到，记录所有可用属性
        available_attrs = [attr for attr in dir(response) if not attr.startswith('_')]
        logger.error(f"无法找到文件内容，可用属性: {available_attrs}")

        # 尝试直接访问响应对象的所有属性
        for attr in available_attrs:
            try:
                attr_value = getattr(response, attr)
                if isinstance(attr_value, bytes) and attr_value:
                    logger.debug(f"在{attr}属性中找到bytes内容: {len(attr_value)} 字节")
                    return attr_value
            except Exception as e:
                logger.debug(f"检查{attr}属性时出错: {e}")

        raise UBoxDeviceError(f"无法在响应对象中找到文件内容，响应类型: {type(response)}")

    # ==================== 私有方法 ====================

    def _upload_to_fileserver(self, files: Dict[str, Any]) -> str:
        """
        上传文件到fileserver

        Args:
            files: 文件数据，格式为 {'file': (filename, file_obj, content_type)}

        Returns:
            str: 文件UUID

        Raises:
            UBoxDeviceError: 上传失败时抛出异常
        """
        try:
            # 准备上传参数
            url = f"{self.FILESERVER_BASE_URL}{self.FILESERVER_ENDPOINTS['upload']}"

            # 从client中获取认证token
            auth_token = self._sdk.get_auth_token()
            headers = {
                'Accept': '*/*',
                'Authorization': auth_token
            }

            # 准备文件数据
            if 'file' in files:
                file_info = files['file']
                if isinstance(file_info, tuple) and len(file_info) >= 3:
                    filename, file_obj, content_type = file_info

                    # 确保文件对象可读
                    if hasattr(file_obj, 'read'):
                        # 读取文件内容
                        file_content = file_obj.read()
                        # 重新定位文件指针到开头
                        if hasattr(file_obj, 'seek'):
                            file_obj.seek(0)

                        # 准备上传的文件数据
                        upload_files = {
                            'file': (filename, file_content, content_type)
                        }

                        # 准备其他参数
                        data = {
                            'params': json.dumps({
                                "storageType": 2,
                                "minioReq": {
                                    "bucketName": "prod",
                                    "path": "ubox/"
                                }
                            })
                        }

                        # 发送上传请求
                        response = requests.post(url, headers=headers, files=upload_files, data=data)

                        # 检查响应
                        if response.status_code == 200:
                            result = response.json()
                            if result.get("code") == 200:
                                file_uuid = result.get("data", {}).get("fileUuid")
                                if file_uuid:
                                    return file_uuid
                                else:
                                    raise UBoxDeviceError("fileserver响应中未找到fileUuid")
                            else:
                                error_msg = result.get('msg', '未知错误')
                                raise UBoxDeviceError(f"fileserver返回失败: {error_msg}")
                        else:
                            raise UBoxDeviceError(f"fileserver上传失败，HTTP状态码: {response.status_code}")
                    else:
                        raise UBoxDeviceError("文件对象不支持read方法")
                else:
                    raise UBoxDeviceError("文件数据格式不正确")
            else:
                raise UBoxDeviceError("未找到文件数据")

        except Exception as e:
            if isinstance(e, UBoxDeviceError):
                raise
            logger.error(f"上传文件到fileserver时发生异常: {e}")
            raise UBoxDeviceError(f"上传文件到fileserver异常: {str(e)}")

    def _save_file_stream(self, response, save_path: str, target_path: str) -> None:
        """
        保存文件流到指定文件路径

        Args:
            response: HTTP响应对象
            save_path: 文件保存路径
            target_path: 目标路径

        Raises:
            UBoxDeviceError: 保存失败时抛出异常
        """
        try:
            # 确保目标目录存在
            target_dir = os.path.dirname(save_path)
            if target_dir and not os.path.exists(target_dir):
                os.makedirs(target_dir, exist_ok=True)

            # 使用统一的响应内容读取方法
            content = self._read_response_content(response, target_path)

            # 安全地写入文件
            with open(save_path, 'wb') as f:
                if isinstance(content, bytes):
                    f.write(content)
                elif isinstance(content, str):
                    # 如果是字符串，可能是base64编码，需要解码
                    try:
                        import base64
                        decoded_content = base64.b64decode(content)
                        f.write(decoded_content)
                        logger.info(f"成功解码base64内容并写入文件: {save_path}")
                    except Exception as decode_error:
                        logger.warning(f"base64解码失败，尝试直接编码写入: {decode_error}")
                        f.write(content.encode('utf-8'))
                else:
                    # 其他类型，尝试转换为bytes
                    try:
                        f.write(bytes(content))
                    except Exception as convert_error:
                        logger.error(f"无法转换内容为bytes: {convert_error}")
                        raise UBoxDeviceError(f"无法转换响应内容为bytes: {type(content)}")

            file_size = os.path.getsize(save_path)
            logger.debug(f"文件保存成功: {save_path}, 大小: {file_size} 字节")

            # 验证图片文件完整性
            if self._is_image_file(save_path):
                if not self._validate_image_file(save_path):
                    logger.warning(f"保存的图片文件可能损坏: {save_path}")

        except Exception as e:
            logger.error(f"保存文件流失败: {save_path}, 错误: {e}")
            raise UBoxDeviceError(f"保存文件流失败: {str(e)}")

    def _save_and_extract_directory_stream(self, response, save_path: str, target_path: str) -> None:
        """
        保存目录流并解压到指定目录

        Args:
            response: HTTP响应对象
            save_path: 目录保存路径
            target_path: 目标路径

        Raises:
            UBoxDeviceError: 处理失败时抛出异常
        """
        try:
            # 确保目标目录存在
            if not os.path.exists(save_path):
                os.makedirs(save_path, exist_ok=True)

            # 创建临时文件用于保存下载的内容
            temp_dir = tempfile.mkdtemp()
            temp_file = os.path.join(temp_dir, "temp_download")

            try:
                # 使用统一的响应内容读取方法
                content = self._read_response_content(response, target_path)

                # 记录内容信息用于调试
                logger.debug(
                    f"目录流读取到的内容类型: {type(content)}, 长度: {len(content) if hasattr(content, '__len__') else 'unknown'}")

                # 安全地写入临时文件
                with open(temp_file, 'wb') as f:
                    if isinstance(content, bytes):
                        f.write(content)
                    elif isinstance(content, str):
                        # 如果是字符串，可能是base64编码，需要解码
                        try:
                            import base64
                            decoded_content = base64.b64decode(content)
                            f.write(decoded_content)
                            logger.info(f"成功解码base64目录内容并写入临时文件: {temp_file}")
                        except Exception as decode_error:
                            logger.warning(f"目录内容base64解码失败，尝试直接编码写入: {decode_error}")
                            f.write(content.encode('utf-8'))
                    else:
                        # 其他类型，尝试转换为bytes
                        try:
                            f.write(bytes(content))
                        except Exception as convert_error:
                            logger.error(f"无法转换目录内容为bytes: {convert_error}")
                            raise UBoxDeviceError(f"无法转换目录响应内容为bytes: {type(content)}")

                # 检查内容类型，判断是否需要解压
                content_type = response.headers.get('Content-Type', '')
                file_extension = os.path.splitext(temp_file)[1]

                if content_type == 'application/zip' or file_extension == '.zip':
                    # ZIP文件解压
                    self._extract_zip_to_directory(temp_file, save_path)
                else:
                    # 其他类型文件，当作普通文件处理
                    file_name = os.path.basename(target_path.rstrip('/\\'))
                    if not file_name:
                        file_name = "downloaded_file"

                    final_path = os.path.join(save_path, file_name)
                    shutil.copy2(temp_file, final_path)

                    file_size = os.path.getsize(final_path)
                    logger.debug(f"文件下载成功（非压缩格式）: {final_path}, 大小: {file_size} 字节")

            finally:
                # 清理临时文件
                try:
                    shutil.rmtree(temp_dir)
                except Exception as cleanup_error:
                    logger.warning(f"清理临时文件失败: {cleanup_error}")

        except Exception as e:
            logger.error(f"处理目录流失败: {save_path}, 错误: {e}")
            raise UBoxDeviceError(f"处理目录流失败: {str(e)}")

    def _extract_zip_to_directory(self, zip_path: str, target_dir: str) -> None:
        """
        解压ZIP文件到指定目录

        Args:
            zip_path: ZIP文件路径
            target_dir: 目标目录

        Raises:
            UBoxDeviceError: 解压失败时抛出异常
        """
        try:
            # 解压ZIP文件
            with zipfile.ZipFile(zip_path, 'r') as zipf:
                zipf.extractall(target_dir)

            # 计算解压后的文件信息
            extracted_files = []
            total_size = 0
            for root, dirs, files in os.walk(target_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    extracted_files.append(file_path)
                    total_size += os.path.getsize(file_path)

            logger.debug(f"ZIP文件解压成功: {target_dir}, 文件数: {len(extracted_files)}, 总大小: {total_size} 字节")

        except Exception as e:
            logger.error(f"解压ZIP文件失败: {zip_path}, 错误: {e}")
            raise UBoxDeviceError(f"解压ZIP文件失败: {str(e)}")

    def _download_from_fileserver(self, file_uuid: str, save_path: str, path_type: str) -> None:
        """
        从fileserver下载文件到本地

        Args:
            file_uuid: 文件UUID
            save_path: 本地保存路径
            path_type: 路径类型（file=文件路径，dir=目录路径）

        Raises:
            UBoxDeviceError: 下载失败时抛出异常
        """
        try:
            # 准备下载参数
            url = f"{self.FILESERVER_BASE_URL}{self.FILESERVER_ENDPOINTS['download']}"

            # 从client中获取认证token
            auth_token = self._sdk.get_auth_token()
            if not auth_token:
                raise UBoxDeviceError("缺少认证token，无法从fileserver下载文件")

            headers = {
                'Accept': '*/*',
                'Content-Type': 'application/json',
                'Authorization': auth_token
            }

            data = {
                "fileUuid": file_uuid
            }

            logger.debug(f"开始从fileserver下载文件: {file_uuid}")

            # 发送下载请求
            response = requests.post(url, headers=headers, json=data, stream=True)

            # 检查响应
            if response.status_code == 200:
                self._process_fileserver_download_stream(response, save_path, path_type, file_uuid)
            else:
                raise UBoxDeviceError(f"fileserver下载请求失败，HTTP状态码: {response.status_code}")

        except Exception as e:
            if isinstance(e, UBoxDeviceError):
                raise
            logger.error(f"从fileserver下载文件时发生异常: {e}")
            raise UBoxDeviceError(f"从fileserver下载文件异常: {str(e)}")

    def _process_fileserver_download_stream(self, response, save_path: str, path_type: str, file_uuid: str) -> None:
        """
        处理fileserver下载的文件流

        Args:
            response: HTTP响应对象
            save_path: 保存路径
            path_type: 路径类型
            file_uuid: 文件UUID

        Raises:
            UBoxDeviceError: 处理失败时抛出异常
        """
        try:
            if path_type == "dir":
                # 目录类型：需要解压
                self._save_and_extract_directory_stream(response, save_path, "fileserver_download")
            else:
                # 文件类型：直接保存
                self._save_file_stream(response, save_path, "fileserver_download")
            # 下载成功后，自动删除fileserver上的文件
            try:
                self._delete_from_fileserver(file_uuid)
            except Exception as e:
                logger.warning(f"文件下载完成后，删除fileserver文件失败: {file_uuid}, 错误: {e}")

        except Exception as e:
            logger.error(f"处理fileserver下载流失败: {e}")
            raise UBoxDeviceError(f"处理fileserver下载流失败: {str(e)}")

    def _delete_from_fileserver(self, file_uuid: str) -> None:
        """
        从fileserver删除文件

        Args:
            file_uuid: 文件UUID

        Raises:
            UBoxDeviceError: 删除失败时抛出异常
        """
        try:
            # 准备删除参数
            url = f"{self.FILESERVER_BASE_URL}{self.FILESERVER_ENDPOINTS['delete']}"

            # 从client中获取认证token
            auth_token = self._sdk.get_auth_token()
            if not auth_token:
                raise UBoxDeviceError("缺少认证token，无法删除fileserver文件")

            headers = {
                'Accept': '*/*',
                'Content-Type': 'application/json',
                'Authorization': auth_token
            }

            data = {
                "fileUuid": file_uuid
            }

            # 发送删除请求
            response = requests.post(url, headers=headers, json=data)

            # 检查响应
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 200:
                    logger.debug(f"fileserver文件删除成功: {file_uuid}")
                else:
                    error_msg = result.get('msg', '未知错误')
                    raise UBoxDeviceError(f"fileserver文件删除失败: {error_msg}")
            else:
                raise UBoxDeviceError(f"fileserver文件删除请求失败，HTTP状态码: {response.status_code}")

        except Exception as e:
            if isinstance(e, UBoxDeviceError):
                raise
            logger.error(f"删除fileserver文件时发生异常: {e}")
            raise UBoxDeviceError(f"删除fileserver文件异常: {str(e)}")

    # ==================== PUSH 操作 ====================

    def push_direct(self, file_path: str, target_path: str) -> str:
        """
        直接推送模式：将本地文件直接POST到目标服务
        使用设备操作系统的直接访问模式

        Args:
            file_path: 本地文件路径
            target_path: 目标路径（类型会自动与本地路径保持一致）

        Returns:
            str: 推送成功后的目标路径

        Raises:
            UBoxValidationError: 参数验证失败时抛出异常
            UBoxDeviceError: 推送失败时抛出异常
        """
        # 验证和准备路径参数
        target_path, path_type = self._validate_and_prepare_paths(file_path, target_path)

        # 准备请求参数
        endpoint = self.operation_config["endpoints"]["push"]
        params = {'path': target_path, 'path_type': path_type}

        # 准备文件数据
        file_data = self._prepare_file_data(file_path, path_type)

        try:
            # 使用设备操作系统的请求方法
            response = self._make_request(
                method="POST",
                endpoint=endpoint,
                params=params,
                files=file_data['files']
            )

            if hasattr(response, 'status_code') and response.status_code == 200:
                response_data = response.json()
                if not response_data.get('success', False):
                    raise UBoxDeviceError(f"push请求失败：{response_data.get('msg', 'unknown')}")
                else:
                    logger.debug(f"文件直接推送成功: {file_path} -> {target_path}")
                    return target_path
            else:
                status_code = getattr(response, 'status_code', 'unknown')
                raise UBoxDeviceError(f"推送请求失败，HTTP状态码: {status_code}")

        finally:
            # 清理临时文件
            self._cleanup_temp_files(file_data)

    def push_via_proxy(self, file_path: str, target_path: str) -> str:
        """
        代理推送模式：通过代理服务器推送文件
        1. 先上传文件到fileserver获取file_uuid
        2. 然后通过代理调用GET请求通知目标服务下载文件

        Args:
            file_path: 本地文件路径
            target_path: 目标路径（类型会自动与本地路径保持一致）

        Returns:
            str: 推送成功后的目标路径

        Raises:
            UBoxValidationError: 参数验证失败时抛出异常
            UBoxDeviceError: 推送失败时抛出异常
        """
        # 验证和准备路径参数
        target_path, path_type = self._validate_and_prepare_paths(file_path, target_path)

        # 准备文件数据
        file_data = self._prepare_file_data(file_path, path_type)

        try:
            # 上传文件到fileserver
            file_uuid = self._upload_to_fileserver(file_data['files'])

            # 获取file_uuid
            if not file_uuid:
                raise UBoxDeviceError("从fileserver响应中获取file_uuid失败")

            logger.debug(f"文件已上传到fileserver，获取到file_uuid: {file_uuid}")

            endpoint = self.operation_config["endpoints"]["push"]
            params = {
                'path': target_path,
                'path_type': path_type,
                'file_uuid': file_uuid
            }

            logger.debug(f"代理模式：通过代理通知目标服务下载文件，参数: {params}")

            # 使用GET方法调用，通过代理转发
            response = self._make_request(
                method="GET",
                endpoint=endpoint,
                params=params
            )

            # 检查远程服务的实际响应
            if hasattr(response, 'json') and callable(response.json):
                try:
                    response_data = response.json()
                    remote_success = response_data.get('success', False)
                    remote_msg = response_data.get('msg', '未知错误')

                    if remote_success:
                        logger.info(f"文件代理推送成功: {file_path} -> {target_path}")
                        return target_path
                    else:
                        raise UBoxDeviceError(f"远程服务推送失败: {remote_msg}")
                except Exception as json_error:
                    # 如果无法解析JSON，检查HTTP状态码
                    if hasattr(response, 'status_code') and response.status_code == 200:
                        logger.info(f"文件代理推送成功（无法解析响应内容）: {file_path} -> {target_path}")
                        return target_path
                    else:
                        status_code = getattr(response, 'status_code', 'unknown')
                        raise UBoxDeviceError(f"推送请求失败，HTTP状态码: {status_code}")
            else:
                # 如果响应对象没有json方法，检查其他属性
                if hasattr(response, 'status_code') and response.status_code == 200:
                    logger.info(f"文件代理推送成功: {file_path} -> {target_path}")
                    return target_path
                else:
                    status_code = getattr(response, 'status_code', 'unknown')
                    raise UBoxDeviceError(f"推送请求失败，HTTP状态码: {status_code}")

        finally:
            # 清理临时文件
            self._cleanup_temp_files(file_data)

    # ==================== PULL 操作 ====================

    def pull_direct(self, target_path: str, save_path: str, path_type: str) -> str:
        """
        直接拉取模式：直接调用目标服务pull接口获取文件流并保存
        使用设备操作系统的直接访问模式

        Args:
            target_path: 目标服务上的文件路径
            save_path: 本地保存路径
            path_type: 路径类型（file=文件路径，dir=目录路径）

        Returns:
            str: 拉取成功后的本地保存路径

        Raises:
            UBoxValidationError: 参数验证失败时抛出异常
            UBoxDeviceError: 拉取失败时抛出异常
        """
        # 验证路径类型和目标路径的匹配性
        self._validate_path_type_and_target(path_type, save_path)

        # 准备请求参数
        endpoint = self.operation_config["endpoints"]["pull"]
        params = {'path': target_path}

        logger.debug(f"直接拉取模式：开始拉取文件，目标路径: {target_path}, 保存路径: {save_path}, 类型: {path_type}")

        # 使用设备操作系统的请求方法
        response = self._make_request(
            method="POST",
            endpoint=endpoint,
            params=params
        )

        # 检查响应状态
        if hasattr(response, 'status_code') and response.status_code == 200:
            # 响应成功，处理文件流
            try:
                if path_type == "dir":
                    # 目录类型：需要解压
                    self._save_and_extract_directory_stream(response, save_path, target_path)
                else:
                    # 文件类型：直接保存
                    self._save_file_stream(response, save_path, target_path)

                logger.debug(f"文件直接拉取成功: {target_path} -> {save_path}")
                return save_path

            except Exception as stream_error:
                logger.error(f"处理文件流时发生错误: {stream_error}")
                raise UBoxDeviceError(f"处理文件流失败: {str(stream_error)}")
        else:
            # 响应失败
            status_code = getattr(response, 'status_code', 'unknown')
            raise UBoxDeviceError(f"拉取请求失败，HTTP状态码: {status_code}")

    def pull_via_proxy(self, target_path: str, save_path: str, path_type: str) -> str:
        """
        代理拉取模式：通过代理服务器拉取文件
        1. 先通知目标服务将文件上传到fileserver，获取file_uuid
        2. 然后本地根据file_uuid从fileserver下载文件，并做相应的解压或保存

        Args:
            target_path: 目标服务上的文件路径
            save_path: 保存到本地的路径
            path_type: 路径类型（file=文件路径，dir=目录路径）

        Returns:
            str: 拉取成功后的本地保存路径

        Raises:
            UBoxValidationError: 参数验证失败时抛出异常
            UBoxDeviceError: 拉取失败时抛出异常
        """
        # 验证路径类型和目标路径的匹配性
        self._validate_path_type_and_target(path_type, save_path)

        # 第一步：通过代理通知目标服务将文件上传到fileserver
        endpoint = self.operation_config["endpoints"]["pull"]
        params = {'path': target_path}

        logger.debug(f"代理拉取模式：通知目标服务上传文件到fileserver，目标路径: {target_path}")

        # 使用GET方法调用，这会触发目标服务将文件上传到fileserver
        response = self._make_request(
            method="GET",
            endpoint=endpoint,
            params=params
        )

        # 检查响应状态
        if hasattr(response, 'status_code') and response.status_code == 200:
            try:
                # 尝试解析JSON响应，获取file_uuid
                proxy_response_data = response.json()
                if proxy_response_data.get('code') == 200:
                    response_data = proxy_response_data.get('data', {})
                    if response_data.get('success', False):
                        file_uuid = response_data.get('data', {}).get('fileUuid')
                        if file_uuid:
                            logger.debug(f"获取到file_uuid: {file_uuid}，开始从fileserver下载文件")
                            # 第二步：从fileserver下载文件并处理
                            self._download_from_fileserver(file_uuid, save_path, path_type)
                            logger.info(f"文件代理拉取成功: {target_path} -> {save_path}")
                            return save_path
                        else:
                            raise UBoxDeviceError("响应中未找到fileUuid")
                    else:
                        error_msg = proxy_response_data.get('msg', '目标服务pull失败')
                        raise UBoxDeviceError(f"目标服务pull失败: {error_msg}")
                else:
                    error_msg = proxy_response_data.get('msg', '代理服务转发失败')
                    raise UBoxDeviceError(f"代理服务pull失败: {error_msg}")
            except Exception as json_error:
                raise UBoxDeviceError(f"解析代理服务pull响应失败: {str(json_error)}")
        else:
            status_code = getattr(response, 'status_code', 'unknown')
            raise UBoxDeviceError(f"代理拉取请求失败，HTTP状态码: {status_code}")

    # ==================== 便捷方法 ====================

    def push(self, file_path: str, target_path: str, use_proxy: bool = None) -> str:
        """
        便捷的推送方法，根据设备配置自动选择推送模式

        Args:
            file_path: 本地文件路径
            target_path: 目标路径
            use_proxy: 是否使用代理模式（None表示自动选择）

        Returns:
            str: 推送成功后的目标路径

        Raises:
            UBoxValidationError: 参数验证失败时抛出异常
            UBoxDeviceError: 推送失败时抛出异常
        """
        if use_proxy is None:
            # 自动选择：根据设备配置决定
            use_proxy = self.device.use_proxy if hasattr(self.device, 'use_proxy') else False

        if use_proxy:
            return self.push_via_proxy(file_path, target_path)
        else:
            return self.push_direct(file_path, target_path)

    def pull(self, target_path: str, save_path: str, path_type: str, use_proxy: bool = None) -> str:
        """
        便捷的拉取方法，根据设备配置自动选择拉取模式

        Args:
            target_path: 目标服务上的文件路径
            save_path: 本地保存路径
            path_type: 路径类型（file=文件路径，dir=目录路径）
            use_proxy: 是否使用代理模式（None表示自动选择）

        Returns:
            str: 拉取成功后的本地保存路径

        Raises:
            UBoxValidationError: 参数验证失败时抛出异常
            UBoxDeviceError: 拉取失败时抛出异常
        """
        if use_proxy is None:
            # 自动选择：根据设备配置决定
            use_proxy = self.device.use_proxy if hasattr(self.device, 'use_proxy') else False

        if use_proxy:
            return self.pull_via_proxy(target_path, save_path, path_type)
        else:
            return self.pull_direct(target_path, save_path, path_type)

    def create_remote_dir(self) -> Optional[str]:
        """
        创建远程设备所在的client上的临时目录
        
        Returns:
            str: 创建成功后的目标路径
            
        Raises:
            UBoxDeviceError: 创建失败时抛出异常
        """
        return CreateRemoteDirOperation(self.device).execute()

    def clean_remote_device_dir(self) -> Optional[str]:
        """
        创建远程设备所在的client上的临时目录

        Returns:
            str: 创建成功后的目标路径

        Raises:
            UBoxDeviceError: 创建失败时抛出异常
        """
        return CleanDeviceDirOperation(self.device).execute()


class CurrentAppOperation(DeviceOperation):
    """获取当前应用操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "获取当前应用",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备获取当前应用请求参数"""
        request_data = self._build_request_params(
            method="current_app"
        )

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": request_data
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> str:
        """处理获取当前应用响应数据"""
        if 'result' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        result = response_data['result']
        return str(result) if result is not None else ""


class CurrentActivityOperation(DeviceOperation):
    """获取当前Activity操作实现（仅Android和鸿蒙）"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "获取当前Activity",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备获取当前Activity请求参数"""
        request_data = self._build_request_params(
            method="current_activity"
        )

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": request_data
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> str:
        """处理获取当前Activity响应数据"""
        if 'result' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        result = response_data['result']
        return str(result) if result is not None else ""


class ClearSafariOperation(DeviceOperation):
    """清除Safari历史缓存数据操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "清除Safari历史缓存",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备清除Safari请求参数"""
        close_pages = kwargs.get('close_pages', False)

        request_data = self._build_request_params(
            method="clear_safari",
            close_pages=close_pages
        )

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": request_data
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> bool:
        """处理清除Safari响应数据"""
        if 'result' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        result = response_data['result']
        return bool(result)


class AppListRunningOperation(DeviceOperation):
    """获取正在运行的app列表操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "获取正在运行的app列表",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备获取正在运行的app列表请求参数"""
        request_data = self._build_request_params(
            method="app_list_running"
        )

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": request_data
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> list:
        """处理获取正在运行的app列表响应数据"""
        if 'result' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        result = response_data['result']
        return list(result) if result is not None else []


class PerfStartOperation(DeviceOperation):
    """开始采集性能数据操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "开始采集性能数据",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备开始采集性能数据请求参数"""
        container_bundle_identifier = kwargs.get('container_bundle_identifier')
        sub_process_name = kwargs.get('sub_process_name', '')
        sub_window = kwargs.get('sub_window', '')
        case_name = kwargs.get('case_name')
        log_output_file = kwargs.get('log_output_file')

        if not container_bundle_identifier:
            raise UBoxValidationError("应用包名不能为空", field="container_bundle_identifier")
        if not log_output_file:
            raise UBoxValidationError("log文件名不能为空", field="log_output_file")
        if not case_name:
            case_name = 'perf'

        if self.mode == RunMode.NORMAL:
            # 正常模式：需要创建远程目录
            fileTransfer = FileTransferHandler(self.device)
            client_temp_dir = fileTransfer.create_remote_dir()
        else:
            # 本地模式：直接使用本地路径，SDK和client在同一台机器上
            client_temp_dir = os.path.dirname(os.path.abspath(log_output_file))

        self.device.perf_case_name = case_name
        request_data = self._build_request_params(
            method="perf_start",
            container_bundle_identifier=container_bundle_identifier,
            sub_process_name=sub_process_name,
            sub_window=sub_window,
            output_directory=client_temp_dir,
            case_name=case_name,
            log_output_file=log_output_file
        )

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": request_data
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> bool:
        """处理开始采集性能数据响应数据"""
        if 'result' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        result = response_data['result']
        return bool(result)


class PerfStopOperation(DeviceOperation):
    """停止采集性能数据操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "停止采集性能数据",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备停止采集性能数据请求参数"""
        request_data = self._build_request_params(
            method="perf_stop"
        )

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": request_data
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> bool:
        """处理停止采集性能数据响应数据"""
        if 'result' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")
        output_directory = kwargs.get('output_directory')
        result = response_data['result']
        success = bool(result)
        try:
            if not output_directory:
                return success
            elif not success:
                return False
            else:
                return PerfSaveDataOperation(self.device).execute(output_directory=output_directory)
        finally:
            # 无论成功与否，都清空性能采集状态
            if hasattr(self.device, 'perf_case_name'):
                self.device.perf_case_name = None


class PerfSaveDataOperation(DeviceOperation):
    """导出性能数据操作实现"""

    def __init__(self, device):
        super().__init__(device)
        self.output_directory = Optional[str]
        self.case_name = Optional[str]

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "导出性能数据",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备导出性能数据请求参数"""
        case_name = kwargs.get('case_name', self.device.perf_case_name)
        output_directory = kwargs.get('output_directory', '')

        if self.mode == RunMode.NORMAL:
            # 正常模式：需要创建远程目录
            fileTransfer = FileTransferHandler(self.device)
            client_temp_dir = fileTransfer.create_remote_dir()
            self.output_directory = client_temp_dir
        else:
            # 本地模式：直接使用本地路径，SDK和client在同一台机器上
            client_temp_dir = os.path.abspath(output_directory)
            self.output_directory = client_temp_dir

        self.case_name = case_name
        request_data = self._build_request_params(
            method="perf_save_data",
            output_directory=client_temp_dir,
            case_name=case_name
        )

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": request_data
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> bool:
        """处理导出性能数据响应数据"""
        if 'result' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        result = response_data['result']
        if not result:
            return False
        success = bool(result)
        output_directory = kwargs.get('output_directory', '')
        if success:
            try:
                if self.mode == RunMode.NORMAL:
                    # 正常模式：需要文件传输
                    fileTransfer = FileTransferHandler(self.device)
                    save_path = os.path.join(output_directory, f"{self.case_name}.json")
                    fileTransfer.pull(
                        target_path=os.path.join(str(self.output_directory), f"{self.case_name}.json"),
                        save_path=save_path,
                        path_type="file"
                    )
                else:
                    # 本地模式：文件已经在本地，直接返回路径
                    save_path = os.path.join(str(self.output_directory), f"{self.case_name}.json")
                logger.debug(f"性能数据已下载到: {save_path},开始解析")
                success = SaveDataWrapper(self.os_type).process_json_file(save_path)
                if success:
                    logger.debug("性能数据解析成功")
                    return True
                logger.debug("性能数据解析失败")
                return True
            except Exception as e:
                logger.error(f"下载性能数据失败: {e}")
                return False
        return False


class LogcatTask:
    """logcat任务管理类"""

    def __init__(self, device, task_id: str, file_path: str, server_file_path: str, re_filter: str = None):
        self.device = device
        self.task_id = task_id
        self.file_path = file_path  # 用户指定的最终保存路径
        self.re_filter = re_filter
        self._is_running = True
        self.server_file_path = server_file_path  # 服务端实际的文件路径
        # 注册任务到设备
        device._logcat_tasks[task_id] = self

    def stop(self, trace_id: Optional[str] = None) -> bool:
        """停止logcat采集任务"""
        if not self._is_running:
            logger.warning(f"logcat任务{self.task_id}已经停止")
            return False

        success = LogcatStopOperation(self.device).execute(task_id=self.task_id, trace_id=trace_id)
        if success:
            self._is_running = False
            # 安全地从任务列表中移除
            if hasattr(self.device, '_logcat_tasks') and self.task_id in self.device._logcat_tasks:
                del self.device._logcat_tasks[self.task_id]
        return success

    def is_running(self) -> bool:
        """检查任务是否正在运行"""
        return self._is_running

    def get_info(self) -> Dict[str, Any]:
        """获取任务信息"""
        return {
            "task_id": self.task_id,
            "file_path": self.file_path,
            "re_filter": self.re_filter,
            "is_running": self._is_running,
            "server_file_path": self.server_file_path
        }


class LogcatStartOperation(DeviceOperation):
    """启动logcat日志采集操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "启动logcat日志采集",
            "method": "POST",
            "endpoint": "/ubox/logcat/start",
            "response_checker": check_standard_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备启动logcat日志采集请求参数"""
        file = kwargs.get('file')
        clear = kwargs.get('clear', False)
        re_filter = kwargs.get('re_filter')

        request_data = {
            "udid": self.device.udid,
            "os_type": self.device.os_type.value,
            "clear": clear
        }

        if self.mode == RunMode.NORMAL:
            # 正常模式：需要创建远程目录
            client_temp_dir = FileTransferHandler(self.device).create_remote_dir()
            file_name = os.path.basename(file)
            server_file_path = os.path.join(client_temp_dir, file_name)
        else:
            # 本地模式：直接使用本地路径，SDK和client在同一台机器上
            server_file_path = os.path.abspath(file)
            make_dir(os.path.dirname(server_file_path))

        request_data['file'] = server_file_path
        if re_filter:
            request_data['re_filter'] = str(re_filter)

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": request_data
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> LogcatTask:
        """处理启动logcat日志采集响应数据"""
        if 'success' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        success = response_data.get('success', False)
        if not success:
            raise UBoxDeviceError(f"启动logcat采集失败: {response_data.get('msg', '未知错误')}")

        # 从响应中获取任务信息
        data = response_data.get('data', {})
        task_id = data.get('task_id')
        server_file_path = data.get('file_path', '')
        re_filter = data.get('re_filter')

        if not task_id:
            raise UBoxDeviceError("服务端未返回task_id")
        user_file_path = kwargs.get('file')
        # 创建LogcatTask对象
        task = LogcatTask(
            device=self.device,
            task_id=task_id,
            file_path=user_file_path,  # 使用用户指定的最终保存路径
            server_file_path=server_file_path,
            re_filter=re_filter
        )
        return task


class LogcatStopOperation(DeviceOperation):
    """停止logcat日志采集操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "停止logcat日志采集",
            "method": "GET",
            "endpoint": "/ubox/logcat/stop",
            "response_checker": check_standard_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备停止logcat日志采集请求参数"""
        task_id = kwargs.get('task_id')
        if not task_id:
            raise UBoxValidationError("task_id is required")
        params = {
            "udid": self.device.udid,
            "os_type": self.device.os_type.value,
            "task_id": task_id
        }
        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "params": params
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> bool:
        """处理停止logcat日志采集响应数据"""
        if 'success' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")
        result = response_data['success']
        if not result:
            return False
        success = bool(result)
        if success:
            task_id = kwargs.get('task_id')
            if not task_id:
                logger.warning("停止logcat成功，但未提供task_id，无法下载文件")
                return True
            # 根据task_id获取任务信息
            if hasattr(self.device, '_logcat_tasks') and task_id in self.device._logcat_tasks:
                task = self.device._logcat_tasks[task_id]
                try:
                    if self.mode == RunMode.NORMAL:
                        # 正常模式：需要文件传输
                        fileTransfer = FileTransferHandler(self.device)
                        fileTransfer.pull(
                            target_path=task.server_file_path,  # 使用任务的服务器路径
                            save_path=task.file_path,  # 使用任务的用户路径
                            path_type="file"
                        )
                        logger.debug(f"logcat文件已下载到: {task.file_path}")
                    else:
                        # 本地模式：文件已经在本地，直接返回路径
                        logger.debug(f"logcat文件已在本地: {task.file_path}")
                except Exception as e:
                    logger.error(f"下载logcat文件失败: {e}")
            else:
                logger.warning(f"未找到task_id为{task_id}的logcat任务，无法下载文件")
        return success


class ANRStartOperation(DeviceOperation):
    """启动ANR/Crash监控操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "启动ANR/Crash监控",
            "method": "POST",
            "endpoint": "/ubox/anr/start",
            "response_checker": check_standard_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备启动ANR/Crash监控请求参数"""
        package_name = kwargs.get('package_name')
        collect_am_monitor = kwargs.get('collect_am_monitor', False)

        if not package_name:
            raise UBoxValidationError("package_name is required for ANR monitoring")

        request_data = {
            "udid": self.device.udid,
            "os_type": self.device.os_type.value,
            "package_name": package_name,
            "collect_am_monitor": collect_am_monitor
        }

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": request_data
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> bool:
        """处理启动ANR/Crash监控响应数据"""
        if 'success' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        success = response_data.get('success', False)
        if not success:
            raise UBoxDeviceError(f"启动ANR/Crash监控失败: {response_data.get('msg', '未知错误')}")

        return success


class ANRStopOperation(DeviceOperation):
    """停止ANR/Crash监控操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "停止ANR/Crash监控",
            "method": "GET",
            "endpoint": "/ubox/anr/stop",
            "response_checker": check_standard_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备停止ANR/Crash监控请求参数"""
        params = {
            "udid": self.device.udid,
            "os_type": self.device.os_type.value
        }

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "params": params
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """处理停止ANR/Crash监控响应数据"""
        if 'success' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        success = response_data.get('success', False)
        if not success:
            raise UBoxDeviceError(f"停止ANR/Crash监控失败: {response_data.get('msg', '未知错误')}")

        # 获取监控结果数据
        data = response_data.get('data', {})
        result = {
            'success': success,
            'run_time': data.get('run_time', 0),
            'crash_count': data.get('crash_count', 0),
            'anr_count': data.get('anr_count', 0)
        }

        # 如果指定了输出目录，则下载文件
        output_directory = kwargs.get('output_directory')
        if output_directory and success:
            try:
                self._download_anr_files(result, output_directory, data)
            except Exception as e:
                logger.error(f"下载ANR文件失败: {e}")
                # 下载失败不影响停止操作的成功状态
        result.update({"output_directory": output_directory})
        return result

    def _download_anr_files(self, result: Dict[str, Any], output_directory: str, server_data: Dict[str, Any]):
        """下载ANR监控相关文件"""
        # 确保输出目录存在
        os.makedirs(output_directory, exist_ok=True)

        if self.mode == RunMode.NORMAL:
            # 正常模式：需要文件传输
            fileTransfer = FileTransferHandler(self.device)
        else:
            # 本地模式：文件已经在本地，不需要传输
            fileTransfer = None

        # 下载logcat文件
        logcat_file = server_data.get('logcat_file')
        if logcat_file:
            logcat_filename = os.path.basename(logcat_file)
            logcat_local_path = os.path.join(output_directory, logcat_filename)
            try:
                if self.mode == RunMode.NORMAL:
                    fileTransfer.pull(
                        target_path=logcat_file,
                        save_path=logcat_local_path,
                        path_type="file"
                    )
                    logger.debug(f"ANR logcat文件已下载到: {logcat_local_path}")
                else:
                    # 本地模式：需要将文件从server路径移动到用户指定路径
                    shutil.copy2(logcat_file, logcat_local_path)
                    logger.debug(f"ANR logcat文件已复制到: {logcat_local_path}")
                result['logcat_file'] = logcat_local_path
            except Exception as e:
                logger.error(f"下载logcat文件失败: {e}")

        # 下载截图文件
        screenshots = server_data.get('screenshots', [])
        screenshots_local = []
        for screenshot in screenshots:
            screenshot_filename = os.path.basename(screenshot)
            screenshot_local_path = os.path.join(output_directory, screenshot_filename)
            try:
                if self.mode == RunMode.NORMAL:
                    fileTransfer.pull(
                        target_path=screenshot,
                        save_path=screenshot_local_path,
                        path_type="file"
                    )
                    logger.debug(f"ANR截图已下载到: {screenshot_local_path}")
                else:
                    # 本地模式：需要将文件从server路径移动到用户指定路径
                    shutil.copy2(screenshot, screenshot_local_path)
                    logger.debug(f"ANR截图已复制到: {screenshot_local_path}")
                screenshots_local.append(screenshot_local_path)
            except Exception as e:
                logger.error(f"下载截图文件失败: {e}")
        result['screenshots'] = screenshots_local

        # 下载上下文文件
        context_files = server_data.get('context_files', [])
        context_files_local = []
        for context_file in context_files:
            context_filename = os.path.basename(context_file)
            context_local_path = os.path.join(output_directory, context_filename)
            try:
                if self.mode == RunMode.NORMAL:
                    fileTransfer.pull(
                        target_path=context_file,
                        save_path=context_local_path,
                        path_type="file"
                    )
                    logger.debug(f"ANR上下文文件已下载到: {context_local_path}")
                else:
                    # 本地模式：需要将文件从server路径移动到用户指定路径
                    shutil.copy2(context_file, context_local_path)
                    logger.debug(f"ANR上下文文件已复制到: {context_local_path}")
                context_files_local.append(context_local_path)
            except Exception as e:
                logger.error(f"下载上下文文件失败: {e}")
        result['context_files'] = context_files_local

        # 下载AM监控文件
        am_monitor_file = server_data.get('am_monitor_file')
        if am_monitor_file:
            am_filename = os.path.basename(am_monitor_file)
            am_local_path = os.path.join(output_directory, am_filename)
            try:
                if self.mode == RunMode.NORMAL:
                    fileTransfer.pull(
                        target_path=am_monitor_file,
                        save_path=am_local_path,
                        path_type="file"
                    )
                    logger.debug(f"ANR AM监控文件已下载到: {am_local_path}")
                else:
                    # 本地模式：需要将文件从server路径移动到用户指定路径
                    shutil.copy2(am_monitor_file, am_local_path)
                    logger.debug(f"ANR AM监控文件已复制到: {am_local_path}")
                result['am_monitor_file'] = am_local_path
            except Exception as e:
                logger.error(f"下载AM监控文件失败: {e}")


class GetElementCVOperation(DeviceOperation):
    """基于多尺寸模板匹配的图像查找操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "基于CV的元素获取",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备基于CV的元素获取请求参数"""
        tpl = kwargs.get('tpl')
        img = kwargs.get('img')
        timeout = kwargs.get('timeout', 30)
        threshold = kwargs.get('threshold', 0.8)
        pos = kwargs.get('pos')
        pos_weight = kwargs.get('pos_weight', 0.05)
        ratio_lv = kwargs.get('ratio_lv', 21)
        crop_box = kwargs.get('crop_box')
        is_translucent = kwargs.get('is_translucent', False)
        to_gray = kwargs.get('to_gray', False)
        tpl_l = kwargs.get('tpl_l')
        deviation = kwargs.get('deviation')
        time_interval = kwargs.get('time_interval', 0.5)

        if not tpl:
            raise UBoxValidationError("模板图像不能为空", field="tpl")

        if self.mode == RunMode.NORMAL:
            # 正常模式：需要文件传输
            fileTransfer = FileTransferHandler(self.device)
            client_temp_dir = fileTransfer.create_remote_dir()
            tpl_path = fileTransfer.push(tpl, _file_target_path_join(client_temp_dir, os.path.basename(tpl)))
        else:
            # 本地模式：直接使用本地路径，SDK和client在同一台机器上
            tpl_path = os.path.abspath(tpl)

        request_data = self._build_request_params(
            method="get_element_cv",
            tpl=tpl_path,
            timeout=timeout,
            threshold=threshold,
            pos_weight=pos_weight,
            ratio_lv=ratio_lv,
            is_translucent=is_translucent,
            to_gray=to_gray,
            time_interval=time_interval
        )

        if img:
            if self.mode == RunMode.NORMAL:
                img_path = fileTransfer.push(img, _file_target_path_join(client_temp_dir, os.path.basename(img)))
            else:
                img_path = os.path.abspath(img)
            request_data['img'] = img_path

        if pos:
            request_data['pos'] = list(pos)

        if crop_box:
            request_data['crop_box'] = list(crop_box)

        if tpl_l:
            if self.mode == RunMode.NORMAL:
                tpl_l_path = fileTransfer.push(tpl_l, _file_target_path_join(client_temp_dir, os.path.basename(tpl_l)))
            else:
                tpl_l_path = os.path.abspath(tpl_l)
            request_data['tpl_l'] = tpl_l_path
        if deviation:
            request_data['deviation'] = list(deviation)

        # 透传其他所有未明确处理的参数
        processed_params = {
            'tpl', 'img', 'timeout', 'threshold', 'pos', 'pos_weight',
            'ratio_lv', 'crop_box', 'is_translucent', 'to_gray', 'tpl_l',
            'deviation', 'time_interval'
        }
        for key, value in kwargs.items():
            if key not in processed_params:
                request_data[key] = value

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": request_data
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """处理基于CV的元素获取响应数据"""
        if 'result' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        result = response_data['result']
        return result


class GetElementOCROperation(DeviceOperation):
    """基于OCR文字识别的查找操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "基于OCR的元素获取",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备基于OCR的元素获取请求参数"""
        word = kwargs.get('word')
        crop_box = kwargs.get('crop_box')
        timeout = kwargs.get('timeout', 30)
        time_interval = kwargs.get('time_interval', 0.5)

        if not word:
            raise UBoxValidationError("待查找文字不能为空", field="word")

        request_data = self._build_request_params(
            method="get_element_ocr",
            word=word,
            timeout=timeout,
            time_interval=time_interval
        )

        if crop_box:
            request_data['crop_box'] = list(crop_box)

        # 透传其他所有未明确处理的参数
        processed_params = {'word', 'crop_box', 'timeout', 'time_interval'}
        for key, value in kwargs.items():
            if key not in processed_params:
                request_data[key] = value

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": request_data
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """处理基于OCR的元素获取响应数据"""
        if 'result' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        result = response_data['result']
        return result


class InitDriverOperation(DeviceOperation):
    """初始化设备操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "初始化设备",
            "method": "GET",
            "endpoint": "/ubox/initDriver",
            "response_checker": check_standard_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "params": self._build_request_params()
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> bool:
        """处理应用安装响应数据"""
        if 'success' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        result = response_data['success']
        return bool(result)


class PinchOperation(DeviceOperation):
    """双指缩放操作实现"""

    @property
    def operation_config(self) -> Dict[str, Any]:
        return {
            "name": "双指缩放",
            "method": "POST",
            "endpoint": "/rpc",
            "response_checker": check_jsonrpc_none_response
        }

    def _prepare_request(self, **kwargs) -> Dict[str, Any]:
        """准备双指缩放请求参数"""
        rect = kwargs.get('rect')
        scale = kwargs.get('scale')
        direction = kwargs.get('direction')

        # 验证缩放区域
        if not isinstance(rect, (list, tuple)) or len(rect) != 4:
            raise UBoxValidationError("缩放区域必须是包含4个元素的列表或元组 [x, y, w, h]", field="rect")

        # 验证缩放倍数
        if not isinstance(scale, (int, float)):
            raise UBoxValidationError("缩放倍数必须是数字类型", field="scale")

        if scale <= 0 or scale > 2.0:
            raise UBoxValidationError("缩放倍数必须在(0, 2.0]区间内", field="scale")

        # 验证缩放方向
        if not isinstance(direction, (str, PinchDirection)):
            raise UBoxValidationError("缩放方向必须是字符串或PinchDirection枚举值", field="direction")

        # 如果是字符串，转换为枚举值进行验证
        if isinstance(direction, str):
            try:
                direction = PinchDirection(direction)
            except ValueError:
                raise UBoxValidationError(
                    f"缩放方向必须是 'horizontal'、'vertical' 或 'diagonal' 之一，当前值: {direction}",
                    field="direction"
                )

        return {
            "method": self.operation_config["method"],
            "endpoint": self.operation_config["endpoint"],
            "data": self._build_request_params(
                method="pinch",
                rect=list(rect),
                scale=float(scale),
                direction=direction.value if isinstance(direction, PinchDirection) else direction,
            )
        }

    def _post_process(self, response_data: Dict[str, Any], **kwargs) -> bool:
        """处理双指缩放响应数据"""
        if 'result' not in response_data:
            raise UBoxDeviceError(f"无法解析{self.operation_config['name']}返回体: {response_data}")

        result = response_data['result']
        # 鸿蒙设备可能返回None，视为成功
        if self.os_type == OSType.HM and result is None:
            return True
        return bool(result)
