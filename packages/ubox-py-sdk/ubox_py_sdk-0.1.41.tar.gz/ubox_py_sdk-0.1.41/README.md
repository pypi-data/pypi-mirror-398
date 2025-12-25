# 优测 Python UBox

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

用于操作优测设备的 Python UBox 包，提供简单易用的 API 接口来与优测设备进行交互。

## 功能特性

- 🚀 **简单易用**: 提供直观的 Python API 接口
- 🔑 **JWT Token管理**: 自动token生成、过期检测和懒申请机制
- 🛡️ **错误处理**: 完善的异常处理和错误信息
- 📚 **类型提示**: 完整的类型注解支持
- 🔧 **上下文管理**: 支持 `with` 语句自动管理连接
- 📱 **设备操作**: 支持点击、滑动、输入、截图、录制等设备操作
- 🔍 **智能识别**: 支持UI控件、图像匹配、OCR文字识别等多种定位方式
- 📊 **性能监控**: 支持设备性能数据采集和分析
- 📝 **日志采集**: 支持Android/鸿蒙设备logcat日志采集和过滤
- 🚨 **ANR/Crash监控**: 支持应用ANR和Crash问题检测，自动截图和日志收集

## 安装

### 使用 uv 安装（推荐）

```bash
# 安装 uv（如果还没有安装）

# 创建虚拟环境
uv venv
# 安装包
uv pip install -U ubox-py-sdk -i https://mirrors.tencent.com/repository/pypi/tencent_pypi/simple
```

### 使用 pip 安装
确保python版本>=3.9.5
```bash
python -m pip install ubox-py-sdk --index-url https://pypi.tuna.tsinghua.edu.cn/simple --extra-index-url https://mirrors.tencent.com/repository/pypi/tencent_pypi/simple
```

## 架构说明

1. **默认模式（自动占用设备）**
   - 特点：自动占用、续期、释放设备

2. **默认模式（使用预获取的authCode）**
   - 适用：已有authCode
   - 特点：跳过占用流程，更稳定可靠

3. **本地模式**
   - 适用：仅限本地设备调试
   - 特点：直接访问，性能更好
   - 注意：仅限本地调试自动化脚本

## 快速开始

### 运行示例

我们提供了完整的示例文件来帮助你快速上手：

```bash
# 运行基础示例文件（包含logcat功能演示）
python examples/example.py

# 运行事件处理示例
python examples/event_handler_example.py

# 运行设备列表示例
python examples/device_list_example.py
```

**注意**: `example.py` 包含了完整的功能演示，包括：
- 设备操作（点击、滑动、输入等）
- 截图录制功能
- 性能监控采集
- **logcat日志采集**（仅Android/鸿蒙设备）

### 基础使用

```python
from ubox_py_sdk import UBox, UBoxConnectionError, UBoxAuthenticationError, OSType, RunMode

try:
    # 调试模式示例
    with UBox(secret_id="sid", secret_key="skey") as client:
        device = client.init_device(udid="device-001", os_type=OSType.ANDROID)

except UBoxAuthenticationError as e:
    print(f"认证失败: {e}")
except UBoxConnectionError as e:
    print(f"连接失败: {e}")
except Exception as e:
    print(f"其他错误: {e}")
```

### 主要功能示例

#### 设备操作
```python
# 点击操作
device.click_pos([0.5, 0.5])  # 点击屏幕中心
# 滑动操作
device.slide_pos([0.1, 0.5], [0.9, 0.5])  # 左右滑动
# 文本输入
device.input_text("Hello World")
```

#### 性能监控
```python
# 开始性能采集
device.perf_start(
    container_bundle_identifier="com.example.app"
)
# 停止性能采集并保存数据
device.perf_stop("./perf_output")
```

#### 日志采集（仅Android/鸿蒙）
```python
# 启动logcat日志采集
task = device.logcat_start(
    file="./logcat_output/app_logs.txt",  # 用户指定的最终保存路径
    clear=True,
    re_filter=".*MyApp.*"  # 过滤包含MyApp的日志
)

# 运行一段时间后停止
time.sleep(10)
success = task.stop()  # 停止特定任务

if success:
    print(f"logcat日志已保存到: {task.file_path}")
```

#### ANR/Crash监控（仅Android/鸿蒙）
```python
# 启动ANR/Crash监控（不采集AM监控日志）
success = device.anr_start(package_name="com.example.app")
if success:
    print("ANR监控已启动")
    
    # 运行一段时间后停止监控
    time.sleep(30)
    
    # 停止监控并下载文件
    result = device.anr_stop(output_directory="./anr_output")
    print(f"监控结果: ANR={result['anr_count']}, Crash={result['crash_count']}")
    print(f"截图文件: {result['screenshots']}")
    print(f"日志文件: {result['logcat_file']}")

# 启动ANR/Crash监控（采集AM监控日志）
success = device.anr_start(package_name="com.example.app", collect_am_monitor=True)
if success:
    print("ANR监控已启动（包含AM监控）")
    
    # 停止监控并下载文件
    result = device.anr_stop(output_directory="./anr_output")
    print(f"AM监控文件: {result['am_monitor_file']}")
```

### 日志配置

UBox SDK 提供了灵活的日志配置功能：

```python
# 默认配置（仅控制台输出）
ubox = UBox(secret_id="sid", secret_key="skey")

# 自定义日志级别
ubox = UBox(
    secret_id="sid", 
    secret_key="skey",
    log_level="DEBUG"  # 显示详细调试信息
)

# 文件日志输出
ubox = UBox(
    secret_id="sid", 
    secret_key="skey",
    log_level="INFO",
    log_to_file=True,
    log_file_path="logs/ubox.log"  # 自动创建目录
)

# 生产环境配置
ubox = UBox(
    secret_id="sid", 
    secret_key="skey",
    log_level="WARNING",  # 只记录警告和错误
    log_to_file=True,
    log_file_path="logs/production.log"
)
```

#### PhonePlatform 枚举值说明

- `PhonePlatform.ANDROID = 1`: Android设备
- `PhonePlatform.IOS = 2`: iOS设备  
- `PhonePlatform.HARMONYOS = 3`: 鸿蒙设备
- `PhonePlatform.HARMONYOS_NEXT = 4`: 鸿蒙NEXT设备

#### OSType

设备操作系统类型枚举：

- `OSType.ANDROID`: Android设备
- `OSType.IOS`: iOS设备
- `OSType.HM`: HarmonyOS设备

### 异常类

- `UBoxError`: 基础异常类
- `UBoxConnectionError`: 连接异常
- `UBoxAuthenticationError`: 认证异常
- `UBoxValidationError`: 数据验证异常
- `UBoxTimeoutError`: 超时异常
- `UBoxRateLimitError`: 速率限制异常
- `UBoxDeviceError`: 设备异常

## 项目结构

```
ubox-py-sdk/
├── src/                        # 源代码目录
│   └── ubox_py_sdk/           # 主包目录
│       ├── __init__.py         # 包初始化文件，导出主要API
│       ├── client.py           # 主要客户端类，管理连接和认证
│       ├── device.py           # 设备管理类，封装设备操作接口
│       ├── device_operations.py # 设备操作实现，包含各种操作的具体逻辑
│       ├── exceptions.py       # 异常定义，包含各种错误类型
│       ├── jwt_util.py         # JWT工具类，处理认证token
│       ├── logger.py           # 日志工具，提供统一的日志记录
│       └── models.py           # 数据模型，定义各种数据结构
├── examples/                   # 使用示例目录
│   ├── example.py             # 基础功能演示（包含logcat示例）
│   ├── event_handler_example.py # 事件处理示例
│   ├── device_list_example.py # 设备列表示例
│   └── README.md              # 示例说明文档
├── api.py                     # API接口定义文件
├── pyproject.toml             # 项目配置文件
├── Makefile                   # 构建和部署脚本
├── uv.lock                    # 依赖锁定文件
├── .python-version            # Python版本文件
├── README.md                  # 项目说明文档
├── ubox-py-sdk接口文档.md     # 详细接口文档
└── .gitignore                 # Git忽略文件
```

## 编译

```shell
uv build
```

## 发布包

```shell
uv publish --publish-url https://mirrors.tencent.com/repository/pypi/tencent_pypi/simple
```