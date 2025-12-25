"""
优测 UBox 数据模型

使用 Pydantic 定义 API 请求和响应的数据结构。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class DeviceStatus(str, Enum):
    """设备状态枚举"""
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class DeviceButton(object):
    HOME = 3
    VOLUME_UP = 24
    VOLUME_DOWN = 25

    # for Android special
    BACK = 4
    POWER = 26
    DEL = 67
    FORWARD_DEL = 112
    MENU = 82
    RECENT_APP = 187
    SLEEP = 223
    WAKE_UP = 224

    # for IOS special
    LOCK = 1000
    UNLOCK = 1001

class DriverType(object):
    """面向用户的驱动类型参数，尽量避免用户选择具体的框架"""
    NA = -1
    POS = 0
    UI = 1
    OCR = 2
    CV = 3
    GA = 4
    GA_UNITY = 5
    GA_UE = 6


class PinchDirection(str, Enum):
    """双指缩放方向枚举"""
    HORIZONTAL = "horizontal"  # 横向/水平
    VERTICAL = "vertical"  # 纵向/垂直
    DIAGONAL = "diagonal"  # 斜向/对角线

class OSType(str, Enum):
    """操作系统类型枚举"""
    ANDROID = "android"
    IOS = "ios"
    HM = "hm"


class RunMode(str, Enum):
    """运行模式枚举"""
    NORMAL = "normal"  # 正常模式：优先尝试直接连接，如果无法连接则回退到代理访问
    LOCAL = "local"    # 本地模式：直接链接本地127.0.0.1:26000，没有占用释放，用于本地调试自动化脚本


class DisplayInfo(BaseModel):
    """显示信息"""
    width: int = Field(0, description="屏幕宽度")
    height: int = Field(0, description="屏幕高度")
    rotation: int = Field(0, description="屏幕旋转角度")
    scale: Optional[float] = Field(None, description="屏幕缩放比例（iOS设备）")


class DensityInfo(BaseModel):
    """密度信息"""
    density: float = Field(0.0, description="屏幕密度")
    dpx: Optional[float] = Field(None, description="X轴密度")
    dpy: Optional[float] = Field(None, description="Y轴密度")


class CPUInfo(BaseModel):
    """CPU信息"""
    cores: Union[int, str] = Field(0, description="CPU核心数（可能是数字或字符串）")
    hardware: Optional[str] = Field(None, description="CPU硬件信息")
    
    @property
    def cores_count(self) -> int:
        """获取CPU核心数的数字表示"""
        if isinstance(self.cores, str):
            try:
                return int(self.cores)
            except (ValueError, TypeError):
                return 0
        return self.cores


class MemoryInfo(BaseModel):
    """内存信息"""
    total: int = Field(0, description="总内存（字节）")
    free: Optional[int] = Field(None, description="可用内存（字节）")
    available: Optional[int] = Field(None, description="可用内存（字节）")


class RecordStartResponse(BaseModel):
    """开始录制响应模型"""
    success: Optional[bool] = Field(None, description="录制是否成功启动")
    msg: str = Field("", description="响应消息")
    record_id: str = Field(..., description="录制ID，用于后续停止录制")


class RecordStopResponse(BaseModel):
    """停止录制响应模型"""
    success: bool = Field(..., description="停止录制是否成功")
    msg: str = Field("", description="响应消息")
    localUrl: str = Field("", description="本地文件路径")
    videoUrl: str = Field("", description="云端视频文件URL")
    fileKey: str = Field("", description="文件在云端的键值")
    size: int = Field(0, description="文件大小（字节）")


class ScreenshotResponse(BaseModel):
    """截图响应模型"""
    success: bool = Field(..., description="截图是否成功")
    msg: str = Field("", description="响应消息")
    localUrl: str = Field("", description="本地文件路径")
    imageUrl: str = Field("", description="云端图片文件URL")
    fileKey: str = Field("", description="文件在云端的键值")
    size: int = Field(0, description="文件大小（字节）")


class ScreenshotBase64Response(BaseModel):
    """Base64截图响应模型"""
    jsonrpc: str = Field("2.0", description="JSON-RPC版本")
    result: Dict[str, Any] = Field(..., description="结果数据")
    id: int = Field(..., description="请求ID")
    around: Optional[str] = Field(None, description="内存大小描述，如 '7 GB'")


class StorageInfo(BaseModel):
    """存储信息"""
    total: Optional[int] = Field(None, description="总存储空间（字节）")
    available: Optional[int] = Field(None, description="可用存储空间（字节）")


class ClientConfig(BaseModel):
    """客户端配置"""
    secret_id: Optional[str] = Field(None, description="Secret ID")
    secret_key: Optional[str] = Field(None, description="Secret Key")
    timeout: int = Field(30, description="请求超时时间（秒）")
    verify_ssl: bool = Field(True, description="是否验证SSL证书")

    @field_validator('timeout')
    def validate_timeout(cls, v):
        if v <= 0:
            raise ValueError("timeout 必须大于0")
        return v

    @property
    def is_authenticated(self) -> bool:
        """是否已配置认证信息"""
        return bool(self.secret_id and self.secret_key)

# 设备列表相关模型
class PhonePlatform(int, Enum):
    """手机平台类型枚举"""
    ANDROID = 1      # Android
    IOS = 2          # iOS
    HARMONYOS = 3    # 鸿蒙
    HARMONYOS_NEXT = 4  # 鸿蒙NEXT

class PhoneLabel(BaseModel):
    """手机标签"""
    id: int = Field(0, description="标签ID")
    phoneId: Optional[int] = Field(None, description="手机ID")
    key: str = Field("", description="标签键")
    value: str = Field("", description="标签值")
    udid: str = Field("", description="设备UDID")


class DeviceInfo(BaseModel):
    """设备信息"""
    id: int = Field(..., description="设备ID")
    deviceId: int = Field(..., description="设备ID（另一种表示）")
    udid: str = Field(..., description="设备唯一标识")
    osType: int = Field(..., description="操作系统类型：1=Android, 2=iOS, 4=HarmonyOS")
    manufacturer: Optional[str] = Field(None, description="制造商")
    modelKind: Optional[str] = Field(None, description="设备型号")
    pcClientIp: Optional[str] = Field(None, description="PC客户端IP")
    osVersion: Optional[str] = Field(None, description="操作系统版本")
    harmonyVersion: Optional[str] = Field(None, description="鸿蒙版本")
    secretId: Optional[str] = Field(None, description="密钥ID")
    poolId: Optional[str] = Field(None, description="设备池ID")
    resolutionRatio: Optional[str] = Field(None, description="屏幕分辨率")
    architecture: Optional[str] = Field(None, description="CPU架构")
    modelKindAliasCn: Optional[str] = Field(None, description="设备型号中文别名")
    phoneModelKindImgUrl: Optional[str] = Field(None, description="设备型号图片URL")
    phoneMarketYear: Optional[str] = Field(None, description="设备上市年份")
    onlineStatus: Optional[int] = Field(None, description="在线状态：1=在线, 0=离线")
    remotePhoneOccupy: Optional[int] = Field(None, description="远程手机占用状态")
    autoTaskOccupy: Optional[int] = Field(None, description="自动任务占用状态")
    spectatorOccupyCount: Optional[int] = Field(None, description="旁观占用数量")
    ossStatus: Optional[int] = Field(None, description="OSS状态")
    memoryAround: Optional[str] = Field(None, description="内存大小描述")
    memoryTotal: Optional[str] = Field(None, description="总内存（KB）")
    localPort: Optional[int] = Field(None, description="本地端口")
    proxyPort: Optional[int] = Field(None, description="代理端口")
    netConnStatus: Optional[int] = Field(None, description="网络连接状态")
    remotePort: Optional[int] = Field(None, description="远程端口")
    occupyStatus: Optional[int] = Field(None, description="占用状态，1正常2占用")
    wdaStatus: Optional[int] = Field(None, description="WDA状态")
    cpuCn: Optional[str] = Field(None, description="CPU中文名称")
    cpuCoreNum: Optional[str] = Field(None, description="CPU核心数")
    cpuFrequency: Optional[str] = Field(None, description="CPU频率")
    gpuName: Optional[str] = Field(None, description="GPU名称")
    openGlEsVersion: Optional[str] = Field(None, description="OpenGL ES版本")
    grade: Optional[int] = Field(None, description="设备等级")
    isFold: bool = Field(False, description="是否为折叠屏")
    phoneUuid: Optional[str] = Field(None, description="手机UUID")
    currentAutoOccupyUserId: Optional[str] = Field(None, description="当前自动占用用户ID")
    agentVersion: Optional[str] = Field(None, description="代理版本")


class DeviceListData(BaseModel):
    """设备列表数据"""
    list: List[DeviceInfo] = Field(default_factory=list, description="设备列表")
    total: int = Field(..., description="总设备数量")
    pageNum: int = Field(..., description="当前页码")
    pageSize: int = Field(..., description="每页大小")


class DeviceListResponse(BaseModel):
    """设备列表响应"""
    code: int = Field(..., description="响应状态码")
    msg: str = Field("", description="响应消息")
    data: DeviceListData = Field(..., description="响应数据")