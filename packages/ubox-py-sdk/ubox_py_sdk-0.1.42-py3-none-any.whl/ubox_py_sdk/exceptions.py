"""
优测 UBox 异常定义

定义 UBox 中使用的各种异常类型。
"""


class UBoxError(Exception):
    """
    优测 UBox 基础异常类
    
    所有 UBox 相关异常的基类。
    """
    
    def __init__(self, message: str, code: str = None):
        """
        初始化异常
        
        Args:
            message: 错误消息
            code: 错误代码（可选）
        """
        self.message = message
        self.code = code
        super().__init__(self.message)
    
    def __str__(self):
        """返回异常字符串表示"""
        result = self.message
        
        # 添加错误代码
        if self.code:
            result = f"[{self.code}] {result}"
        
        # 添加字段信息（如果有的话）
        if hasattr(self, 'field') and self.field:
            result = f"{result} (字段: {self.field})"
        return result


class UBoxConnectionError(UBoxError):
    """
    连接异常
    
    当无法连接到优测设备或连接中断时抛出。
    """
    
    def __init__(self, message: str):
        super().__init__(message, "CONNECTION_ERROR")


class UBoxAuthenticationError(UBoxError):
    """
    认证异常
    
    当用户名、密码错误或权限不足时抛出。
    """
    
    def __init__(self, message: str):
        super().__init__(message, "AUTHENTICATION_ERROR")


class UBoxValidationError(UBoxError):
    """
    数据验证异常
    
    当输入数据格式不正确或验证失败时抛出。
    """
    
    def __init__(self, message: str, field: str = None):
        self.field = field
        super().__init__(message, "VALIDATION_ERROR")


class UBoxTimeoutError(UBoxError):
    """
    超时异常
    
    当请求超时时抛出。
    """
    
    def __init__(self, message: str):
        super().__init__(message, "TIMEOUT_ERROR")


class UBoxDeviceError(UBoxError):
    """
    设备异常
    
    当设备返回错误或设备状态异常时抛出。
    """
    
    def __init__(self, message: str):
        super().__init__(message, "DEVICE_ERROR")
