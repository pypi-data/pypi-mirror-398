# ubox python sdk 调用文档

> 本 UBox 需要依赖实验室，并非可脱离实验室本地使用的。

## Demo

> 架构说明：
>
> - 默认模式：包含占用&续期&释放设备，如果传authcode后则不再占用释放
> - 本地模式：直接本地访问，本地编写自动化脚本时使用
> - 设备信息：支持三端（iOS、HarmonyOS、Android）共用的详细信息
> - 失败会抛出异常

## 示例导航（examples/example.py）

以下文档中每个功能在示例文件中均有对应演示，便于快速上手：

- 设备信息: demo_device_info(device)
- UI 树/截图/录制: demo_ui_tree_info(device), demo_screenshot_recording(device)
- 点击/长按/滑动/输入/按键: demo_click_operations(device), demo_slide_operations(device), demo_text_input(device), demo_key_operations(device)
- 双指缩放: demo_pinch_operations(device)
- 应用管理/命令/高级功能: demo_app_management(device), demo_commands(device), demo_advanced_features(device)
- 安装卸载: demo_install_app_features(device)
- 性能采集: demo_perf_features(device)
- 日志采集（logcat）: demo_logcat_features(device)
- ANR/Crash 监控: demo_anr_features(device)

```python
def example_debug_mode():
  print("=== 调试模式示例 ===")

  # 创建调试模式客户端
  client = UBox(
    secret_id="your_secret_id_here",
    secret_key="your_secret_key_here",
  )

  print(f"模式: {client.mode.value}")

  try:
    # 初始化多个设备
    device1 = client.init_device(udid="device-001-udid", os_type=OSType.ANDROID)
    device2 = client.init_device(udid="device-002-udid", os_type=OSType.IOS)
    print(f"已初始化 {len(client._devices)} 台设备")

    # 获取设备信息
    device_info1 = device1.device_info()
    device_info2 = device2.device_info()

    # 展示设备1的详细信息
    print(f"\n设备1详细信息:")
    print(f"  设备标识: {device_info1.serial}")
    print(f"  设备型号: {device_info1.model}")

    # 展示设备2的详细信息
    print(f"\n设备2详细信息:")
    print(f"  设备标识: {device_info2.serial}")
    print(f"  设备型号: {device_info2.model}")

  except Exception as e:
    print(f"❌ 操作失败: {e}")

  finally:
    # 关闭客户端会自动释放所有设备,也可逐个设备释放
    client.close()

```

## 设备信息相关

### 1、device_info()

获取设备的基本信息，包括显示分辨率、型号、版本、CPU 和内存等。

**参数：**

- 无

**返回值：**

```python
dict: 包含设备信息的字典
{
    "display": {
        "width": 0,      # 屏幕宽度
        "height": 0      # 屏幕高度
    },
    "model": "",         # 设备型号
    "version": "",       # 系统版本
    "cpu": {
        "cores": ""      # CPU核心数
    },
    "memory": {
        "total": 0       # 总内存大小
    }
}
```

### 2、设备列表功能

```python
from ubox_py_sdk import UBox, PhonePlatform
from ubox_py_sdk.models import DeviceListResponse

with UBox(secret_id="your_id", secret_key="your_key") as ubox:
    android_devices: DeviceListResponse = ubox.device_list(
        page_num=1,
        page_size=10,
        phone_platform=[PhonePlatform.ANDROID]  # 使用枚举值
    )
    print(f"Android设备数量: {android_devices.data.total}")
    
   
    response: DeviceListResponse = ubox.device_list(
        page_num=1,
        page_size=15,
        phone_platform=[PhonePlatform.ANDROID, PhonePlatform.IOS],  # Android和iOS
        manufacturers=["Redmi", "Xiaomi"],
        resolution_ratios=["720*1600", "1080*2376"]
    )
    
    # 从响应中提取设备信息（使用类型安全的模型）
    device_list = response.data.list
    total_devices = response.data.total
    current_page = response.data.pageNum
    page_size = response.data.pageSize
    
    # 遍历设备列表
    for device in device_list:
        print(f"设备: {device.manufacturer} {device.modelKind}")
        print(f"  UDID: {device.udid}")
        print(f"  平台: {device.osType}")  # 1=Android, 2=iOS, 3=鸿蒙, 4=鸿蒙NEXT
        print(f"  分辨率: {device.resolutionRatio}")
        print(f"  在线状态: {'在线' if device.onlineStatus == 1 else '离线'}")
```

#### PhonePlatform 枚举值说明

- `PhonePlatform.ANDROID = 1`: Android设备
- `PhonePlatform.IOS = 2`: iOS设备  
- `PhonePlatform.HARMONYOS = 3`: 鸿蒙设备
- `PhonePlatform.HARMONYOS_NEXT = 4`: 鸿蒙NEXT设备

### 3、获取占用后的设备auth_code

```python
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

```


## 录屏相关

### 1、record_start(video_path: str)

开始录制设备屏幕。

**参数：**

- `video_path` (str): 指定录屏的输出文件路径，默认为空字符串
- `trace_id` (str, 可选): 追踪ID，用于日志追踪

**返回值：**

- `bool`: 开启录制是否成功

**使用示例：**

```python
# 开始录制屏幕
success = device.record_start("/path/to/video.mp4")

# 带追踪ID的录制
success = device.record_start("/path/to/video.mp4", trace_id="record_001")
```

### 2、record_stop()

停止录制设备屏幕。

**参数：**

- `trace_id` (str, 可选): 追踪ID，用于日志追踪

**返回值：**

- `bool`: 结束录制是否成功

**使用示例：**

```python
# 停止录制屏幕
success = device.record_stop()

# 带追踪ID的停止录制
success = device.record_stop(trace_id="record_001")
```

**注意事项：**

- 录制停止后会自动将视频文件从远程设备拉取到本地
- 视频文件会保存到 `record_start` 时指定的 `video_path` 路径

## 截图相关

### 1、screenshot(label, img_path)

对设备当前画面进行截图。

**参数：**

- `label`: str 截图文件名
- `img_path`: str 文件路径

**返回值：**

```python
dict: 截图信息
{
    "imageUrl": "xx",         # 上传完成的图片的链接
    "localUrl": "",           # client上的位置
    "video_path": "",         # 保存到本地的地址
    "fileKey": "xxx",          # 图片key
    "size": 0              # 截图大小
}
```

### 2、screenshot_base64()

对设备当前画面进行截图。

**参数：**

- 无

**返回值：**

- `str`: 图片base64

## 点击操作相关

### 1、click_pos(pos, duration, times)

基于相对坐标进行点击操作。

**参数：**

- `pos` (tuple or list): 相对坐标，取值区间 [0, 1.0)，左闭右开，不含1，可以传0.99
- `duration` (int or float): 点击持续时间，默认为 0.05 秒
- `times` (int): 点击次数，默认为 1 次，传入 2 可实现双击效果

**返回值：**

- `bool`: 点击是否成功

**使用示例：**

```python
# 单击屏幕中心
success = device.click_pos([0.5, 0.5])

# 长按屏幕右上角 2 秒
success = device.click_pos([0.9, 0.1], duration=2.0)

# 双击屏幕底部
success = device.click_pos([0.5, 0.9], times=2)

# 长按屏幕左侧中间位置 1.5 秒
success = device.click_pos([0.1, 0.5], duration=1.5)
```

### 2、click(loc, by, offset, timeout, duration, times)

基于多种定位方式执行点击操作。

**参数：**

- `loc`: 待点击的元素，具体形式需符合基于的点击类型
- `by` (DriverType): 查找类型，默认为 DriverType.UI
  - DriverType.UI: 原生控件
  - DriverType.CV: 图像匹配
  - DriverType.OCR: 文字识别
  - DriverType.POS: 坐标
  - DriverType.GA_UNITY: GA Unity
  - DriverType.GA_UE: GA UE
- `offset` (list or tuple): 偏移，元素定位位置加上偏移为实际操作位置
- `timeout` (int): 定位元素的超时时间，默认为 30 秒
- `duration` (float): 点击的按压时长，以实现长按，默认为 0.05 秒
- `times` (int): 点击次数，以实现双击等效果，默认为 1 次
- `**kwargs`: 基于不同的查找类型，其他需要的参数

**返回值：**

- `bool`: 操作是否成功

**使用示例：**

```python
# 基于控件点击
success = device.click(
    loc="//XCUIElementTypeButton[@label='登录']",
    by=DriverType.UI
)

# 基于图像匹配点击
success = device.click(
    loc="login_button.png",
    by=DriverType.CV,
    timeout=10
)

# 基于文字识别点击
success = device.click(
    loc="确认",
    by=DriverType.OCR
)

# 带偏移的点击
success = device.click(
    loc="//XCUIElementTypeButton[@label='按钮']",
    by=DriverType.UI,
    offset=[10, 5]  # 向右偏移10像素，向下偏移5像素
)

# 双击操作
success = device.click(
    loc="//XCUIElementTypeIcon[@label='照片']",
    by=DriverType.UI,
    times=2
)
```

### 3、long_click(loc, by, offset, timeout, duration, \*\*kwargs)

执行长按操作。

**参数：**

- `loc`: 待操作的元素，具体形式需符合基于的操作类型
- `by` (DriverType): 查找类型，默认为 DriverType.POS坐标
- `offset` (list or tuple): 偏移，元素定位位置加上偏移为实际操作位置
- `timeout` (int): 定位元素的超时时间，默认为 30 秒
- `duration` (int or float): 点击的按压时长，默认为 1 秒

**返回值：**

- `bool`: 操作是否成功

**使用示例：**

```python
# 长按控件 3 秒
success = device.long_click(
    loc="//XCUIElementTypeButton[@label='删除']",
    by=DriverType.UI,
    duration=3.0
)

# 长按图像 2.5 秒
success = device.long_click(
    loc="delete_icon.png",
    by=device.utils.param.DriverType.CV,
    duration=2.5
)

# 长按文字 1.5 秒
success = device.long_click(
    loc="长按我",
    by=device.utils.param.DriverType.OCR,
    duration=1.5
)
```

## 文本输入相关

### 1、input_text(text, timeout, depth)

向设备输入文本内容。

**参数：**

- `text` (str): 待输入的文本
- `timeout` (int): 超时时间，默认为 30 秒
- `depth` (int): source tree 的最大深度值，默认为 10

**返回值：**

- `bool`: 输入是否成功

**使用示例：**

```python
# 基本文本输入
success = device.input_text("Hello World")

# 带超时的文本输入
success = device.input_text("测试文本", timeout=60)

# 调整深度的文本输入
success = device.input_text("复杂文本", timeout=30, depth=15)
```

## 按键操作相关

### 1、press(name)

执行设备功能键操作。

**参数：**

- `name` (DeviceButton): 设备按键类型

说明：
安卓：
DeviceButton.HOME,
DeviceButton.VOLUME_UP,
DeviceButton.VOLUME_DOWN,
DeviceButton.BACK,
DeviceButton.POWER,
DeviceButton.DEL,
DeviceButton.FORWARD_DEL,
DeviceButton.MENU,
DeviceButton.RECENT_APP,
DeviceButton.WAKE_UP,
DeviceButton.SLEEP
iOS：
DeviceButton.HOME,
DeviceButton.VOLUME_UP,
DeviceButton.VOLUME_DOWN,
DeviceButton.POWER,
HM：
DeviceButton.HOME
DeviceButton.VOLUME_UP
DeviceButton.VOLUME_DOWN,
DeviceButton.BACK,
DeviceButton.POWER,
DeviceButton.DEL,
DeviceButton.FORWARD_DEL,
DeviceButton.MENU,
DeviceButton.RECENT_APP,
DeviceButton.SLEEP,
DeviceButton.WAKE_UP,

**返回值：**

- `bool`: 点击是否成功

**使用示例：**

```python
# 按返回键
success = device.press(DeviceButton.BACK)
```

## 滑动操作相关

### 1、slide_pos(pos_from, pos_to, down_duration)

基于相对坐标执行滑动操作。

**参数：**

- `pos_from` (tuple or list): 滑动起始坐标，取值区间 [0, 1.0)，左闭右开，不含1，可以传0.99
- `pos_to` (tuple or list): 滑动结束坐标，取值区间 [0, 1.0)，左闭右开，不含1，可以传0.99
- `down_duration` (int or float): 起始位置按下时长（秒），以实现拖拽功能，默认为 0
- `slide_duration` (int or float): 滑动时间（秒），默认为 0.3，仅Android设备有效
- `trace_id` (str, 可选): 追踪ID，用于日志追踪

**返回值：**

- `bool`: 滑动是否成功

**注意事项：**

- 相对坐标取值范围是 [0, 1.0)，左闭右开，不含1，如需滑动到屏幕边缘可使用0.99
- 坐标值使用相对坐标系统，[0, 0] 表示屏幕左上角，[0.99, 0.99] 表示接近屏幕右下角

**使用示例：**

```python
# 从屏幕左侧滑到右侧
success = device.slide_pos(
    pos_from=[0.1, 0.5],
    pos_to=[0.9, 0.5]
)

# 从屏幕顶部滑到底部
success = device.slide_pos(
    pos_from=[0.5, 0.1],
    pos_to=[0.5, 0.9]
)

# 滑动到屏幕边缘（使用0.99）
success = device.slide_pos(
    pos_from=[0.5, 0.5],
    pos_to=[0.99, 0.99]
)

# 带拖拽效果的滑动
success = device.slide_pos(
    pos_from=[0.5, 0.9],
    pos_to=[0.5, 0.1],
    down_duration=0.5
)
```

### 2、slide(loc_from, loc_to, by, timeout, down_duration, **kwargs)

基于多种定位方式执行滑动操作。

**参数：**

- `loc_from`: 滑动起始元素位置
- `loc_to`: 滑动结束元素位置
- `by` (DriverType): 查找类型，默认为 DriverType.POS
- `timeout` (int): 定位元素的超时时间，默认为 120 秒
- `down_duration` (int or float): 起始位置按下时长（秒），以实现拖拽功能，默认为 0
- `**kwargs`: 基于不同的查找类型，其他需要的参数

**返回值：**

- `bool`: 操作是否成功

**使用示例：**

```python
# 从控件A滑动到控件B
success = device.slide(
    loc_from="//XCUIElementTypeButton[@label='开始']",
    loc_to="//XCUIElementTypeButton[@label='结束']",
    by=device.utils.param.DriverType.UI
)

# 基于图像匹配的滑动
success = device.slide(
    loc_from="start_icon.png",
    loc_to="end_icon.png",
    by=device.utils.param.DriverType.CV,
    timeout=60
)

# 基于文字识别的滑动
success = device.slide(
    loc_from="起点",
    loc_to="终点",
    by=device.utils.param.DriverType.OCR
)

```

## 双指缩放相关

### 1、pinch(rect, scale, direction, trace_id)

执行双指缩放操作，支持在指定区域进行放大或缩小。

**参数：**

- `rect` (list or tuple): 用相对坐标系表示的缩放区域，由左上角顶点坐标x,y和区域宽高w,h组成，排列为[x,y,w,h]
  - 坐标和尺寸取值区间为 [0, 1.0)，左闭右开，不含1，可以传0.99
  - 例如：[0.3, 0.3, 0.4, 0.4] 表示从屏幕30%位置开始，宽高各占屏幕40%的区域
- `scale` (float): 缩放倍数
  - 小于1.0时为缩小（如0.8表示缩小到80%）
  - 大于1.0时为放大（如1.5表示放大到150%）
  - 最大取2.0
- `direction` (str or PinchDirection): 缩放方向
  - `'horizontal'` 或 `PinchDirection.HORIZONTAL`: 横向/水平缩放
  - `'vertical'` 或 `PinchDirection.VERTICAL`: 纵向/垂直缩放
  - `'diagonal'` 或 `PinchDirection.DIAGONAL`: 斜向/对角线缩放
- `trace_id` (str, 可选): 追踪ID，用于日志追踪

**返回值：**

- `bool`: 缩放是否成功

**注意事项：**

- 相对坐标取值范围是 [0, 1.0)，左闭右开，不含1，如需操作屏幕边缘区域可使用0.99
- 缩放区域必须完全在屏幕范围内
- 缩放倍数不能超过2.0

**使用示例：**

```python
from ubox_py_sdk.models import PinchDirection

# 在屏幕中心区域进行水平放大
success = device.pinch(
    rect=[0.3, 0.3, 0.4, 0.4],  # 中心区域，相对坐标 [x, y, w, h]
    scale=1.5,                   # 放大1.5倍
    direction=PinchDirection.HORIZONTAL  # 水平方向
)

# 在屏幕中心区域进行垂直缩小
success = device.pinch(
    rect=[0.3, 0.3, 0.4, 0.4],
    scale=0.8,                   # 缩小到80%
    direction='vertical'         # 垂直方向
)

# 在屏幕中心区域进行对角线缩放
success = device.pinch(
    rect=[0.25, 0.25, 0.5, 0.5],  # 更大的缩放区域
    scale=2.0,                     # 放大到200%（最大倍数）
    direction='diagonal'           # 对角线方向
)

# 在屏幕边缘区域进行缩放（使用0.99）
success = device.pinch(
    rect=[0.1, 0.1, 0.3, 0.3],  # 左上角区域
    scale=1.2,
    direction=PinchDirection.HORIZONTAL
)
```

> 示例位置：examples/example.py -> demo_pinch_operations(device)

## 应用管理相关

### 1、install_app(app_url, need_resign, resign_bundle)

安装应用到设备。

**参数：**

- `app_url` (str): 安装包url链接
- `need_resign` (bool): 可缺省，默认为 False。只有 iOS 涉及，需要重签名时传入 True
- `resign_bundle` (str): 可缺省，默认为空。只有 iOS 涉及，need_resign 为 True 时，此参数必须传入非空的 bundleId

**返回值：**

- `bool`: 安装是否成功

### 2、uninstall_app(pkg)

从设备卸载应用。

**参数：**

- `pkg` (str): 被卸载应用的包名，Android 和鸿蒙为应用的 packageName，iOS 则对应为 bundleId

**返回值：**

- `bool`: 卸载是否成功

### 3、start_app(pkg, clear_data, **kwargs)

启动应用。

**参数：**

- `pkg` (str): iOS 为应用 bundle id，Android 和鸿蒙对应为包名
- `clear_data` (bool): 可缺省，默认为 False。仅 Android 相关，清除应用数据
- `**kwargs`: 其他扩展参数

**返回值：**

- `bool`: 启动是否成功

**使用示例：**

```python
# 基本启动应用
success = device.start_app("com.apple.AppStore")

# 清除数据后启动应用（仅Android）
success = device.start_app("com.example.app", clear_data=True)
```

### 4、stop_app(pkg)

结束应用。

**参数：**

- `pkg` (str): iOS 为应用 bundle id，Android 和鸿蒙对应为包名

**返回值：**

- `bool`: 启动是否成功

**使用示例：**

```python
success = device.stop_app("com.apple.AppStore")
```

## 命令执行相关

### 1、cmd_adb(cmd, timeout)

仅 Android 和鸿蒙设备，执行 adb 或 hdb 命令。

**参数：**

- `cmd` (str or list): 具体的 adb 或者 hdb 命令
- `timeout` (int): 执行命令的超时时间，默认为 10 秒

**返回值：**

- `str`: 命令执行结果

**使用示例：**

```python
# 执行 adb 命令获取设备信息
result = device.cmd_adb("getprop ro.product.model")

# 执行 adb 命令获取当前 activity
result = device.cmd_adb("dumpsys activity activities | grep mResumedActivity")

# 带超时的命令执行
result = device.cmd_adb("pm list packages", timeout=30)
```

**注意事项：**

- 此方法仅支持 Android 和鸿蒙设备，iOS 设备不支持
- 命令执行结果会返回字符串格式
- 建议设置合理的超时时间，避免长时间等待
- 某些系统级命令可能需要设备 root 权限

## 性能监控相关

### 1、perf_start(container_bundle_identifier, sub_process_name, sub_window, output_directory, case_name, log_output_file)

开始采集性能数据。

**参数：**

- `container_bundle_identifier` (str): 应用包名
- `sub_process_name` (str, 可选): 进程名，默认为空字符串
- `sub_window` (str, 可选): window名，默认为空字符串
- `output_directory` (str, 可选): 数据输出文件目录，默认为空字符串
- `case_name` (str, 可选): Case名，默认为空字符串
- `log_output_file` (str): log文件名
- `trace_id` (str, 可选): 追踪ID，用于日志追踪

**返回值：**

- `bool`: 启动采集是否成功

**使用示例：**

```python
# 开始采集性能数据
success = device.perf_start(
    container_bundle_identifier="com.tencent.mqq"
)
```

### 2、perf_stop(output_directory, trace_id)

停止采集性能数据。

**参数：**

- `output_directory` (str, 可选): 数据输出文件目录，可不传，不传则不保存数据
- `trace_id` (str, 可选): 追踪ID，用于日志追踪

**返回值：**

- `bool`: 停止采集是否成功

**使用示例：**

```python
# 停止采集性能数据
success = device.perf_stop()

# 停止采集并保存数据到指定目录
success = device.perf_stop(output_directory="/path/to/save")
```

> 示例位置：examples/example.py -> demo_perf_features(device)

### 3、perf_save_data(output_directory, case_name, trace_id)

导出性能数据。一般使用停止时直接保存

**参数：**

- `output_directory` (str): 数据输出文件目录
- `case_name` (str, 可选): Case名，默认为None
- `trace_id` (str, 可选): 追踪ID，用于日志追踪

**返回值：**

- `bool`: 是否成功导出

**使用示例：**

```python
# 导出性能数据
success = device.perf_save_data(
    output_directory="/path/to/output"
)
```

## 日志采集相关（Logcat 多任务）

### 1、logcat_start(file, clear, re_filter, trace_id) -> LogcatTask

[仅Android和鸿蒙] 启动logcat日志采集，返回 `LogcatTask` 对象，可用于单独停止该任务。

**参数：**

- `file` (str or pathlib.Path): 本地保存文件路径（SDK 会在服务端创建临时文件并在停止时拉取到该路径）
- `clear` (bool, 可选): 开始前是否清除logcat，默认为False
- `re_filter` (str or re.Pattern, 可选): 日志过滤正则
- `trace_id` (str, 可选): 追踪ID

**返回值：**

- `LogcatTask`: 任务对象，包含 `task_id`、`file_path` 等信息

**使用示例（examples/example.py: demo_logcat_features）**

```python
task = device.logcat_start(file="./logcat_output/app_logs.txt", clear=True, re_filter=".*python.*")
time.sleep(5)
task.stop()  # 停止该任务
```

### 2、logcat_stop_all(trace_id) -> bool

[仅Android和鸿蒙] 停止当前设备上所有logcat任务。

**参数：**

- `trace_id` (str, 可选): 追踪ID

**返回值：**

- `bool`: 是否全部停止成功

**示例（examples/example.py: demo_logcat_features）**

```python
device.logcat_stop_all()
```

> 示例位置：examples/example.py -> demo_logcat_features(device)

## ANR/Crash 监控

### 1、anr_start(package_name, collect_am_monitor=False, trace_id=None) -> bool

[仅Android和鸿蒙] 启动 ANR/Crash 监控。

**参数：**

- `package_name` (str): 需要监控的应用包名
- `collect_am_monitor` (bool, 可选): 是否采集 AM 监控日志，默认 False
- `trace_id` (str, 可选): 追踪ID

**返回值：**

- `bool`: 启动是否成功

### 2、anr_stop(output_directory=None, trace_id=None) -> dict

停止 ANR/Crash 监控，并将相关文件（logcat、截图、上下文、AM 监控文件）拉取到本地（若提供 `output_directory`）。

**参数：**

- `output_directory` (str, 可选): 本地输出目录
- `trace_id` (str, 可选): 追踪ID

**返回值：**

- `dict`: 监控结果，字段包含：
  - `success` (bool)
  - `run_time` (float)
  - `crash_count` (int)
  - `anr_count` (int)
  - 当提供 `output_directory` 时，还会包含：
    - `logcat_file` (str): 本地logcat路径
    - `screenshots` (list[str]): 本地截图路径
    - `context_files` (list[str]): 本地上下文文件路径
    - `am_monitor_file` (str): 本地 AM 监控文件路径

**示例（examples/example.py: demo_anr_features）**

```python
success = device.anr_start(package_name="com.example.app")
time.sleep(30)
result = device.anr_stop(output_directory="./anr_output")
```

> 示例位置：examples/example.py -> demo_anr_features(device)

## 应用管理相关（补充）

### 5、current_app(trace_id)

获取当前运行的应用。

**参数：**

- `trace_id` (str, 可选): 追踪ID，用于日志追踪

**返回值：**

- `str`: 当前应用的包名或bundle ID

**使用示例：**

```python
# 获取当前应用
current_pkg = device.current_app()
print(f"当前应用: {current_pkg}")
```

### 6、app_list_running(trace_id)

获取正在运行的app列表。

**参数：**

- `trace_id` (str, 可选): 追踪ID，用于日志追踪

**返回值：**

- `list[str]`: 正在运行的app的包名列表

**使用示例：**

```python
# 获取正在运行的app列表
running_apps = device.app_list_running()
print(f"正在运行的app: {running_apps}")
```

### 7、clear_safari(close_pages, trace_id)

清除iOS设备Safari历史缓存数据。

**参数：**

- `close_pages` (bool, 可选): 是否关闭Safari的所有页面，默认为False
- `trace_id` (str, 可选): 追踪ID，用于日志追踪

**返回值：**

- `bool`: 清除是否成功

**使用示例：**

```python
# 清除Safari缓存
success = device.clear_safari()

# 清除Safari缓存并关闭所有页面
success = device.clear_safari(close_pages=True)
```

**注意事项：**

- 此功能仅适用于iOS设备
- 清除Safari的历史记录、缓存和Cookie等数据

## 剪贴板相关

### 1、set_clipboard(text, trace_id)

设置设备剪贴板内容。

**参数：**

- `text` (str): 要设置的剪贴板文本
- `trace_id` (str, 可选): 追踪ID，用于日志追踪

**返回值：**

- `None`: 无返回值

**使用示例：**

```python
# 设置剪贴板内容
device.set_clipboard("Hello World")
```

### 2、get_clipboard(trace_id)

获取设备剪贴板内容。

**参数：**

- `trace_id` (str, 可选): 追踪ID，用于日志追踪

**返回值：**

- `str`: 剪贴板内容

**使用示例：**

```python
# 获取剪贴板内容
content = device.get_clipboard()
print(f"剪贴板内容: {content}")
```

## 网络代理相关

### 1、set_http_global_proxy(host, port, username, password, trace_id)

设置全局HTTP代理。

**参数：**

- `host` (str): 代理主机地址
- `port` (int): 代理端口
- `username` (str, 可选): 代理用户名
- `password` (str, 可选): 代理密码
- `trace_id` (str, 可选): 追踪ID，用于日志追踪

**返回值：**

- `bool`: 设置是否成功

**使用示例：**

```python
# 设置HTTP代理
success = device.set_http_global_proxy("proxy.example.com", 8080)

# 设置带认证的HTTP代理
success = device.set_http_global_proxy(
    "proxy.example.com", 
    8080, 
    username="user", 
    password="pass"
)
```

### 2、get_http_global_proxy(trace_id)

获取当前全局HTTP代理设置。

**参数：**

- `trace_id` (str, 可选): 追踪ID，用于日志追踪

**返回值：**

- `dict`: 代理配置信息

**使用示例：**

```python
# 获取当前代理设置
proxy_config = device.get_http_global_proxy()
print(f"代理配置: {proxy_config}")
```

### 3、clear_http_global_proxy(trace_id)

清除全局HTTP代理设置。

**参数：**

- `trace_id` (str, 可选): 追踪ID，用于日志追踪

**返回值：**

- `bool`: 清除是否成功

**使用示例：**

```python
# 清除代理设置
success = device.clear_http_global_proxy()
```

## 事件处理与智能匹配（Watcher）

### 1、find_optimal_element(selector, match, mode)

智能查找元素的工具函数，支持可控匹配模式。

**参数：**

- `selector` (lxml Element/ElementTree): 需要支持 `xpath` 的选择器
- `match` (str): 待匹配的文本
- `mode` (str, 可选): 匹配模式，默认为 `auto`。可选值：
  - `auto`: 按顺序尝试 严格匹配 → 模糊匹配 → 正则匹配
  - `strict`: 仅严格匹配（精确相等）
  - `fuzzy`: 仅模糊匹配（包含关系）
  - `regex`: 仅正则匹配（EXSLT）

**返回值：**

- `(element, bool)`：匹配到的元素与是否匹配成功

**说明：**

- 严格匹配等价于 `//*[@text="x" or @value="x" or @name="x" or @label="x"]`
- 模糊匹配等价于 `//*[contains(@text,"x") or contains(@value,"x") or ... ]`
- 正则匹配使用 EXSLT: `re:match`

### 2、Watcher：自定义匹配模式

`EventHandler` 的 `Watcher` 支持为每个 watcher 单独设置匹配模式。

**常用方法：**

- `device.handler.watcher(name)`：创建/获取一个 `Watcher`
- `Watcher.when(condition)`：添加一个匹配条件（文本或 XPath）
- `Watcher.click()`：匹配成功后执行点击
- `Watcher.call(func)`：匹配成功后回调函数
- `Watcher.with_match_mode(mode)`：为该 watcher 设置匹配模式（`auto/strict/fuzzy/regex`）

**使用示例：**

```python
eh = device.handler

# 仅严格匹配（精确等于）
eh.watcher("agree").with_match_mode("strict").when("同意").click()

# 仅模糊匹配（包含）
eh.watcher("allow").with_match_mode("fuzzy").when("允许").click()

# 正则匹配
eh.watcher("error").with_match_mode("regex").when("错.?误").click()

# 默认智能（auto：严格→模糊→正则）
eh.watcher("ok").when("确定").click()

# 自定义动作：函数签名 func(device, xml_element, smart_click)
def on_dialog(device, xml_element, smart_click):
    # 也可以在回调里使用 smart_click("继续") 实现智能点击
    center = device.handler.find_xml_element_center(xml_element)
    if center:
        device.click(loc=(center[0], center[1]))

eh.watcher("dialog").with_match_mode("auto").when("提示").call(on_dialog)
```

### 3、EventHandler.smart_click(text)

提供快捷的智能点击能力，内部等价于 `mode='auto'` 的 `find_optimal_element`。

**参数：**

- `text` (str): 待匹配文本

**返回值：**

- `bool`: 是否点击成功

**使用示例：**

```python
device.handler.start()
device.handler.smart_click("允许")
device.handler.stop()
```
