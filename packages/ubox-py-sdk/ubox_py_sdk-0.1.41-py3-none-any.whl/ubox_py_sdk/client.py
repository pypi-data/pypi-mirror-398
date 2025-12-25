import json
import logging
import time
import functools
import traceback
from contextlib import contextmanager
from typing import Any, Dict, Optional, Union, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from requests import Response

from .common_util import print_curl_info
from .exceptions import (
    UBoxAuthenticationError,
    UBoxConnectionError,
    UBoxError, UBoxValidationError,
)
from .models import (
    ClientConfig, OSType, RunMode,
    DeviceListResponse, DeviceListData, PhonePlatform
)
from .jwt_util import JWTUtil
from .logger import get_logger, configure_logging
from .device import Device

logger = get_logger(__name__)


class UBox:
    """
    优测设备客户端
    
    用于与优测设备建立连接并进行各种操作。
    支持两种模式：
    1. 正常模式：优先尝试直接连接，如果无法连接则回退到代理访问，支持设备占用、释放和续期
    2. 本地模式：相当于直接链接本地127.0.0.1:26000，没有占用释放，直接探测本地是否能链接，这个模式用于本地调试自动化脚本
    """

    def __init__(
            self,
            mode: RunMode = RunMode.NORMAL,  # 默认正常模式
            base_url: Optional[str] = None,
            secret_id: Optional[str] = None,
            secret_key: Optional[str] = None,
            timeout: int = 30,
            verify_ssl: bool = True,
            env: Optional[str] = "formal",  # formal正式  test测试环境
            # 日志配置参数
            log_level: Optional[str] = "INFO",
            log_format: Optional[str] = None,
            log_to_file: bool = False,
            log_file_path: str = "ubox/ubox_sdk.log",
    ):
        """
        初始化客户端
        
        Args:
            mode: 运行模式，RunMode.NORMAL（正常模式）或 RunMode.LOCAL（本地模式）
            base_url: 本地lab-agent的IP:PORT地址（本地模式备用地址，*用户无需关注*）
            secret_id: Secret ID，用于公网访问 (正常模式必填项)
            secret_key: Secret Key，用于公网访问 (正常模式必填项)
            timeout: 请求超时时间（秒）
            verify_ssl: 是否验证SSL证书
        """
        self.mode = mode
        if env != "formal":
            self._paas_base_url = "https://lab-paas-dev.utest.21kunpeng.com/utest-paas-manager"
        else:
            self._paas_base_url = "https://labpaas.utest.21kunpeng.com/utest-paas-manager"
        self._core_base_url = f"https://dl.utest.21kunpeng.com/utest-paas-commissioner/{env}"
        self._local_url = base_url or "127.0.0.1:26000"  # 默认本地地址
        if mode == RunMode.NORMAL:
            if not secret_id or not secret_key:
                raise UBoxValidationError("正常模式下必须提供 secret_id 和 secret_key")
            if base_url:
                logger.warning("正常模式下 base_url 将被忽略，通过设备信息接口获取目标地址")
        elif mode == RunMode.LOCAL:
            # 本地模式：直接使用本地地址，不需要secret_id和secret_key
            logger.info(f"本地模式，目标地址: {self._local_url}")
        else:
            raise UBoxValidationError(f"不支持的运行模式: {mode}")

        # 创建配置对象
        self.config = ClientConfig(
            secret_id=secret_id,
            secret_key=secret_key,
            timeout=timeout,
            verify_ssl=verify_ssl,
        )

        # 创建会话对象，配置连接池和重试机制
        self.session = requests.Session()
        self.session.verify = verify_ssl
        self.session.timeout = timeout

        # 配置连接池，提高并发性能
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=20,  # 连接池大小
            pool_maxsize=40,  # 最大连接数
            max_retries=3,  # 最大重试次数
            pool_block=False  # 连接池满时不阻塞
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

        # JWT token相关
        self._current_token: Optional[str] = None
        self._token_generated_at: Optional[float] = None
        # 配置日志
        self._setup_logging(log_level, log_format, log_to_file, log_file_path)

        # 设备上下文
        self._devices: Dict[str, Any] = {}  # 支持多个设备，udid -> Device
        self._project_uuid: Optional[str] = None
        self._user_id: Optional[str] = None

        # 设置默认请求头
        self.session.headers.update({
            'Accept': 'application/json'
        })
        if self.mode == RunMode.NORMAL and self.config.is_authenticated:
            # 正常模式：补充projectId和userId
            try:
                self._fetch_secret_info()
            except Exception as e:
                logger.error(f"获取密钥信息失败: {e}")
                raise UBoxAuthenticationError("无法获取密钥信息（secret info）")

    @property
    def devices(self):
        """获取所有已初始化的设备"""
        return self._devices

    @property
    def project_uuid(self) -> Optional[str]:
        """获取项目UUID"""
        return self._project_uuid

    @property
    def user_id(self) -> Optional[str]:
        """获取用户ID"""
        return self._user_id

    def _setup_logging(
            self,
            log_level: Optional[str] = None,
            log_format: Optional[str] = None,
            log_to_file: bool = False,
            log_file_path: str = "ubox/ubox_sdk.log"
    ) -> None:
        """
        配置日志系统

        Args:
            log_level: 日志级别 ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
            log_format: 日志格式字符串
            log_to_file: 是否输出到文件
            log_file_path: 日志文件路径
        """
        # 转换日志级别字符串为logging常量
        level_map = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }

        # 确定日志级别
        level = logging.INFO
        if log_level is not None:
            level = level_map.get(log_level.upper(), logging.INFO)

        # 配置全局日志系统
        configure_logging(
            level=level,
            format_string=log_format,
            log_to_file=log_to_file,
            log_file_path=log_file_path
        )

    def get_auth_token(self) -> Optional[str]:
        """
        获取当前的认证token
        
        Returns:
            认证token字符串，如果没有则返回None
        """
        self._ensure_valid_token()
        return self._current_token

    def _fetch_secret_info(self) -> None:
        """获取并缓存鉴权上下文（projectUuid 与 updateUuid）。

        接口：GET https://labpaas.utest.21kunpeng.com/utest-paas-manager/project/secretInfo?secretId=xxx
        要求请求头包含 Authorization: <jwt>
        """
        secret_url = f"{self._paas_base_url}/project/secretInfo"
        # 使用统一请求方法，确保携带会话头（含 Authorization）
        resp_model = self.make_request('GET', url=secret_url, params={'secretId': self.config.secret_id})
        payload = resp_model.json() if hasattr(resp_model, 'json') else {}

        # 检查业务状态码
        code = payload.get('code')
        if code != 200:
            error_msg = payload.get('msg', '未知错误')
            raise UBoxError(f"获取密钥信息失败，业务状态码: {code}, 错误信息: {error_msg}")

            # 获取结果数据
        data = payload.get('result', {})
        if not data:
            raise UBoxError("获取密钥信息失败，响应中没有result字段")

        self._project_uuid = data.get('projectUuid')
        # 优先使用updateUuid，如果没有值则使用creatorUuid作为备选
        self._user_id = data.get('updateUuid') or data.get('creatorUuid')

        # 验证必要字段
        if not self._project_uuid:
            raise UBoxError("获取密钥信息失败，响应中没有projectUuid字段")
        if not self._user_id:
            raise UBoxError("获取密钥信息失败，响应中没有updateUuid和creatorUuid字段")

        logger.info(
            f"已获取密钥信息 projectUuid={self._project_uuid}, updateUuid={self._user_id}"
        )

    def _resolve_target_device(self, udid: str, os_type: OSType) -> str:
        """
        解析目标服务的地址
        """
        if self.mode == RunMode.NORMAL:
            # 正常模式：优先尝试直接连接，如果无法连接则回退到代理访问
            client_ip = None
            port = None
            try:
                # 调用设备信息接口获取clientIp和port
                device_info_params = {'agentVersion': 'v2'}
                device_info_response = self.make_request('GET', f'/api/v1/device/{udid}/info',
                                                         params=device_info_params,
                                                         base_url=self._core_base_url)
                if device_info_response.json() and device_info_response.json().get('code') == 200:
                    device_data = device_info_response.json().get('data', {})
                    device_info = device_data.get('device')
                    client_ip = device_info.get('clientIp')
                    port = device_info.get('port')
                    logger.info(f"获取到设备 {udid} 地址信息: {client_ip}:{port}")
                else:
                    logger.warning(f"正常模式获取设备地址失败: {device_info_response.json()}")
            except Exception as e:
                logger.warning(f"正常模式获取设备地址异常: {e}")

            if client_ip and port:
                # 测试地址是否联通
                target_url = f"http://{client_ip}:{port}"
                logger.info(f"测试 {udid} 地址是否联通,地址信息: {target_url}")
                if self._test_connection(target_url):
                    # 测试是否是正确的目标设备
                    logger.info(f"目标{target_url}联通，测试 目标client是否是该设备的client")
                    if self._quick_check_local_device(target_url, udid, os_type):
                        logger.info(f"目标client正确，可直连{target_url}")
                        return target_url
                    # 如果设备列表获取失败或未找到目标设备，回退到代理访问
                    logger.info(f"正常模式回退到代理访问: {self._core_base_url}")
                    return self._core_base_url
                else:
                    logger.warning(f"设备地址 {target_url} 无法联通，回退到代理访问")

            # 如果无法获取设备地址或地址无法联通，回退到代理访问
            logger.info(f"正常模式回退到代理访问: {self._core_base_url}")
            return self._core_base_url

        elif self.mode == RunMode.LOCAL:
            # 本地模式：直接使用本地地址
            local_url = f"http://{self._local_url.rstrip('/')}"
            logger.info(f"本地模式，使用地址: {local_url}")

            # 测试本地地址是否联通
            if self._test_connection(local_url):
                logger.info(f"本地地址联通，使用: {local_url}")
                return local_url
            else:
                raise UBoxError(f"本地地址 {local_url} 无法联通，请检查本地lab-agent是否启动")
        else:
            raise UBoxError(f"不支持的运行模式: {self.mode}")

    def _test_connection(self, url: str) -> bool:
        """
        测试指定URL是否联通
        
        Args:
            url: 要测试的URL
            
        Returns:
            bool: 是否联通
        """
        try:
            # 使用更短的超时时间进行HTTP测试
            response = self.session.get(url, timeout=1.5)
            return response.status_code < 500  # 5xx错误表示服务器问题，4xx表示客户端问题但服务器可达
        except Exception as e:
            logger.debug(f"测试连接 {url} 失败: {e}")
            return False

    def _quick_check_local_device(self, target_url: str, udid: str, os_type: OSType) -> bool:
        """
        快速检查本地地址是否有目标设备 - 单次请求，3秒超时，不重试

        Args:
            target_url: 目标lab-agent URL地址
            udid: 设备串号
            os_type: OSType 设备类型

        Returns:
            bool: 是否找到目标设备
        """
        # 单次快速探测：直接请求目标的设备列表，超时3秒，不使用全局重试
        try:
            import requests
            url = f"{target_url.rstrip('/')}/cloudphone/list"
            resp = requests.get(url, params={"os_type": os_type}, timeout=3)
            if resp.status_code != 200:
                logger.debug(f"快速检查本地设备失败，状态码: {resp.status_code}")
                return False

            try:
                data = resp.json()
            except Exception as e:
                logger.debug(f"解析设备列表响应JSON失败: {e}")
                return False

            if not data or not data.get('success'):
                logger.debug(f"设备列表返回不成功: {data}")
                return False

            device_list = data.get('list', [])
            for device in device_list:
                if device.get('udid') == udid:
                    logger.info(f"在本地设备列表中找到目标设备: {udid}")
                    return True
            return False
        except Exception as e:
            logger.debug(f"快速检查本地设备异常: {e}")
            return False

    def init_device(self, udid: str, os_type: OSType, auth_code: Optional[str] = None,
                    force_proxy: bool = False, trace_id: Optional[str] = None) -> Device:
        """
        初始化/占用设备，使后续操作针对该设备。
        
        Args:
            udid: 要初始化的设备唯一标识
            os_type: 设备操作系统类型（android/ios/hm）
            auth_code: 正常模式下可选的认证码，如果提供则跳过设备占用流程
            force_proxy: 是否强制从公网连接到设备，忽略局域网就近接入，默认不强制
        
        Returns:
            Device: 设备对象
        """
        if not udid:
            raise UBoxError("udid 不能为空")
        if os_type not in (OSType.ANDROID, OSType.IOS, OSType.HM):
            raise UBoxError("os_type 仅支持 android、ios、hm")

        device = None
        try:
            # 正常模式：处理设备认证
            debug_id = None
            if self.mode == RunMode.NORMAL:
                if auth_code:
                    # 如果提供了authCode，直接使用，跳过设备占用
                    logger.info(f"正常模式使用提供的authCode: {auth_code}")
                else:
                    # 没有提供authCode，调用debug接口占用设备
                    debug_payload = {
                        "scene": 5,  # UBox调试占用
                        "zone": "zone_dalian",  # 这里可能需要从配置中获取
                        "projectId": self._project_uuid,
                        "serialNumber": udid,
                        "userId": self._user_id,
                        "deviceInfo": f"Device/{udid}/({os_type.value})",  # 简化的设备信息
                        # 系统类型：1: Android 2: IOS 4：HarmonyNext
                        "osType": 1 if os_type == OSType.ANDROID else (2 if os_type == OSType.IOS else 4)
                    }

                    debug_response = self.make_request('POST', '/cloudphone/debug', data=debug_payload,
                                                       base_url=self._paas_base_url)
                    if debug_response.json() and debug_response.json().get('code') == 200:
                        debug_data = debug_response.json().get('data', {})
                        auth_code = debug_data.get('authCode')
                        debug_id = debug_data.get('debugId')
                        logger.info(f"正常模式设备占用成功，获取到authCode: {auth_code}, debugId: {debug_id}")
                    else:
                        raise UBoxError(f"正常模式设备占用失败: {debug_response.json()}")

            elif self.mode == RunMode.LOCAL:
                # 本地模式：不需要认证码和debugId
                auth_code = None
                debug_id = None
                logger.info("本地模式，跳过设备占用流程")
            else:
                raise UBoxError(f"不支持的运行模式: {self.mode}")

            target_url = self._core_base_url
            use_proxy = force_proxy
            if not force_proxy:
                # 解析目标设备地址
                target_url = self._resolve_target_device(udid, os_type)
                # 判断是否使用代理访问
                use_proxy = (self.mode == RunMode.NORMAL and target_url == self._core_base_url)
            if self.mode == RunMode.NORMAL and not use_proxy:
                # 是正常模式 还没有使用代理，说明是直连手机，那检测一下手机是不是在本地，如果是本地，可以直接转化成local模式
                local_url = f"http://{self._local_url.rstrip('/')}"
                if self._quick_check_local_device(local_url, udid, os_type):
                    logger.info(f"手机在本地，可直连{local_url}，并转为local模式")
                    target_url = local_url
                    self.mode = RunMode.LOCAL

            device = Device(self, udid, os_type, target_url, auth_code, debug_id, self.mode, use_proxy)
            self._devices[udid] = device

            # 探测设备是否存活
            try:
                device.d_screen_size = device.screen_size(trace_id=trace_id)
            except Exception as e:
                logger.error(f"设备 {udid} 无法连接: {e}\n{traceback.format_exc()}")
                raise UBoxConnectionError(f"设备 {udid} 无法连接，请确认设备序列号正确，并且设备正常")
            logger.info(f"设备已初始化: {udid} -> {target_url} (模式: {self.mode}, 代理: {use_proxy})")
            return device

        except Exception as e:
            # 任何异常都自动释放设备
            logger.error(f"设备 {udid} 初始化失败，正在自动释放: {e}")

            if device is not None:
                try:
                    device.release()
                    logger.info(f"设备 {udid} 已自动释放")
                except Exception as release_error:
                    logger.warning(f"设备 {udid} 自动释放失败: {release_error}")

            # 从设备列表中移除
            if udid in self._devices:
                del self._devices[udid]

            # 重新抛出原始异常
            raise e

    def release_all_devices(self):
        """并发释放所有已初始化的设备。"""
        if not self._devices:
            logger.info("没有需要释放的设备")
            return

        logger.info(f"并发释放所有设备，共 {len(self._devices)} 台")
        devices = list(self._devices.values())

        def release_device_safe(device):
            """安全释放单个设备"""
            device_udid = getattr(device, 'udid', 'unknown')
            try:
                device.release()
                logger.info(f"设备 {device_udid} 释放成功")
                return True, device_udid, None
            except Exception as e:
                logger.warning(f"释放设备 {device_udid} 失败: {e}")
                return False, device_udid, str(e)

        max_workers = min(20, len(devices))
        success_count = 0
        failed_count = 0
        failed_devices = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(release_device_safe, device) for device in devices]

            # 等待所有任务完成
            for future in as_completed(futures):
                success, device_udid, error = future.result()
                if success:
                    success_count += 1
                else:
                    failed_count += 1
                    failed_devices.append((device_udid, error))

        # 输出最终结果
        logger.info(f"设备释放完成: 成功 {success_count} 台，失败 {failed_count} 台")

        if failed_count == 0:
            logger.info("✅ 全部设备释放成功")
        else:
            logger.warning(f"❌ 有 {failed_count} 台设备释放失败:")
            for device_udid, error in failed_devices:
                logger.warning(f"  - 设备 {device_udid}: {error}")

        # 清空设备列表
        self._devices.clear()

    def force_release(self, ubox_debug_id: str) -> None:
        try:
            stop_debug_payload = {"debugId": ubox_debug_id}
            self.make_request('PUT', '/cloudphone/debug', data=stop_debug_payload,
                              base_url=self.paas_base_url)
            logger.info(f"强制释放设备-debug已停止")
        except Exception as e:
            logger.warning(f"强制释放设备-debug失败: {e}")

    def device_list(self,
                    page_num: int = 1,
                    page_size: int = 20,
                    phone_platform: Optional[List[PhonePlatform]] = None,
                    manufacturers: Optional[List[str]] = None,
                    online_status: int = 1,
                    resolution_ratios: Optional[List[str]] = None) -> DeviceListData:
        """
        获取设备列表
        
        Args:
            page_num: 页码，从1开始，默认1
            page_size: 每页大小，默认20
            phone_platform: 手机平台类型列表，如 [PhonePlatform.ANDROID, PhonePlatform.IOS] 表示Android和iOS
            manufacturers: 制造商列表，如 ["Redmi", "Xiaomi"]
            online_status: 在线状态，1表示在线，0表示离线
            resolution_ratios: 分辨率比例列表，如 ["720*1600", "1080*2376"]
            
        Returns:
            DeviceListResponse: 设备列表响应数据
            
        Raises:
            UBoxError: 获取设备列表失败时抛出异常
        """
        try:
            # 构建请求参数
            request_data = {
                "basePageReq": {
                    "pageNum": page_num,
                    "pageSize": page_size
                }
            }

            # 添加可选参数
            if phone_platform:
                # 将PhonePlatform枚举转换为整数值
                platform_values = [p.value if isinstance(p, PhonePlatform) else p for p in phone_platform]
                request_data["phonePlatform"] = platform_values
            if manufacturers:
                request_data["manufacturers"] = manufacturers
            if online_status is not None:
                request_data["onlineStatus"] = online_status
            if resolution_ratios:
                request_data["resolutionRatios"] = resolution_ratios

            # 发送请求获取设备列表
            response = self.make_request(
                method="POST",
                endpoint="/api/v1/phone/list",
                base_url=self._core_base_url,
                data=request_data
            )
            # 检查响应状态
            if response.status_code != 200:
                raise UBoxError(f"获取设备列表失败，HTTP状态码: {response.status_code}")

            # 解析响应数据
            response_data = response.json()
            if not isinstance(response_data, dict):
                raise UBoxError(f"设备列表响应格式错误: {response_data}")

            # 检查业务状态码
            code = response_data.get('code')
            if code != 200:
                msg = response_data.get('msg', '未知错误')
                raise UBoxError(f"获取设备列表失败，业务状态码: {code}, 错误信息: {msg}")

            device_list_response = DeviceListResponse(**response_data)
            return device_list_response.data

        except Exception as e:
            logger.error(f"获取设备列表异常: {e}")
            if isinstance(e, UBoxError):
                raise
            raise UBoxError(f"获取设备列表失败: {str(e)}")

    def _ensure_valid_token(self) -> None:
        """
        确保有有效的JWT token

        如果token不存在或即将过期，则重新生成。
        """
        if not self.config.is_authenticated:
            return
        # 检查是否需要生成新token
        if (self._current_token is None or
                self._token_generated_at is None or
                JWTUtil.is_token_expired(
                    self._current_token,
                    self.config.secret_key
                )):
            logger.debug("生成新的JWT token")
            self._current_token = JWTUtil.generate_utest_token(
                self.config.secret_id,
                self.config.secret_key
            )
            self._token_generated_at = time.time()

            # 更新请求头中的Authorization（后端期望为原始JWT字符串，不带 Bearer 前缀）
            self.session.headers['Authorization'] = self._current_token
            logger.debug("JWT token已更新")

    def make_request(
            self,
            method: str,
            endpoint: Optional[str] = None,
            data: Optional[Dict[str, Any]] = None,
            params: Optional[Dict[str, Any]] = None,
            url: Optional[str] = None,
            base_url: Optional[str] = None,
            headers: Optional[Dict[str, str]] = None,
            **kwargs
    ) -> Response:
        """
        发送HTTP请求

        Args:
            method: HTTP方法（GET, POST, PUT, DELETE等）
            endpoint: API端点（与 url 二选一）
            data: 请求体数据
            params: 查询参数
            url: 可选，完整请求URL（与 endpoint 二选一）
            base_url: 可选，基础URL，与endpoint组合使用
            headers: 可选，自定义请求头，会与默认请求头合并
            **kwargs: 其他请求参数

        Returns:
            Response: 响应对象

        Raises:
            UBoxConnectionError: 连接错误
            UBoxAuthenticationError: 认证错误
            UBoxError: 其他错误
        """
        # 确保有有效的token
        request_url = url
        if endpoint is not None and base_url is not None:
            # 直接拼接，保留中间的斜杠
            request_url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        self._ensure_valid_token()

        # 准备请求头，合并默认请求头和自定义请求头
        request_headers = dict(self.session.headers)
        if headers:
            request_headers.update(headers)  # 自定义请求头覆盖默认值
        try:
            # 发送请求
            response = self.session.request(
                method=method,
                url=request_url,
                json=data,
                params=params,
                headers=request_headers,
                **kwargs
            )
            # print_curl_info(method=method, url=request_url, params=params, headers=request_headers, data=data)
            # 检查HTTP状态码
            response.raise_for_status()

            return response

        except requests.exceptions.ConnectionError as e:
            logger.error(f"连接错误: {e}")
            raise UBoxConnectionError(
                f"无法连接到设备: {e}\n{print_curl_info(method=method, url=request_url, params=params, headers=request_headers, data=data)}")

        except requests.exceptions.Timeout as e:
            logger.error(f"请求超时: {e}")
            raise UBoxConnectionError(
                f"请求超时: {e}\n{print_curl_info(method=method, url=request_url, params=params, headers=request_headers, data=data)}")

        except requests.exceptions.HTTPError as e:
            # 获取响应内容，了解具体错误信息
            try:
                error_content = response.text
                if not error_content:
                    error_content = response.content.decode('utf-8', errors='ignore') if response.content else "无错误详情"
            except Exception:
                error_content = "无法获取错误详情"

            logger.error(f"HTTP错误 {response.status_code}: {error_content}")

            if response.status_code == 401:
                logger.error("认证失败")
                # 清除当前token，下次请求会重新生成
                self._current_token = None
                self._token_generated_at = None
                raise UBoxAuthenticationError(f"JWT token无效或已过期: {error_content}")
            elif response.status_code == 403:
                logger.error("权限不足")
                raise UBoxAuthenticationError(f"权限不足，无法访问该资源: {error_content}")
            elif response.status_code == 504:
                logger.error("网关超时，可能是网络问题或服务端响应慢")
                raise UBoxConnectionError(f"网关超时 (504): {error_content}")
            else:
                raise UBoxError(f"HTTP错误 {response.status_code}: {error_content}")

        except Exception as e:
            logger.error(f"未知错误: {e}")
            raise UBoxError(f"未知错误: {e}")

    def make_request_with_retry(self, method: str, max_retries: int = 3, **kwargs) -> Response:
        """带智能重试的请求方法
        
        Args:
            method: HTTP方法
            max_retries: 最大重试次数
            **kwargs: 其他请求参数
            
        Returns:
            Response: 响应对象
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                logger.debug(f"尝试 {attempt + 1}/{max_retries}")
                return self.make_request(method, **kwargs)

            except UBoxConnectionError as e:
                last_exception = e
                if "504" in str(e) and attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # 递增等待时间
                    logger.warning(f"请求失败 (504错误)，{wait_time}秒后重试: {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    break

            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 1
                    logger.warning(f"请求失败，{wait_time}秒后重试: {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    break

        # 所有重试都失败了
        logger.error(f"请求失败，已重试 {max_retries} 次")
        raise last_exception

    def close(self):
        """关闭客户端连接"""
        logger.info("正在关闭UBox客户端...")

        # 关闭前尝试释放所有设备
        try:
            self.release_all_devices()
        except Exception as e:
            logger.error(f"释放设备时发生异常: {e}")
            # 忽略释放失败，继续关闭连接

        # 关闭HTTP会话
        if self.session:
            self.session.close()
            logger.info("HTTP会话已关闭")

        logger.info("UBox客户端已关闭")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()

    @property
    def paas_base_url(self):
        return self._paas_base_url


@contextmanager
def operation_timer(operation_name):
    """操作时间监控上下文管理器，精确到毫秒"""
    start_time = time.time()
    try:
        yield
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000  # 转换为毫秒
        print(f"⏱️ {operation_name} 执行完成，耗时: {execution_time:.2f}毫秒")
    except Exception as e:
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000  # 转换为毫秒
        print(f"❌ {operation_name} 执行失败，耗时: {execution_time:.2f}毫秒，错误: {e}")
        raise
