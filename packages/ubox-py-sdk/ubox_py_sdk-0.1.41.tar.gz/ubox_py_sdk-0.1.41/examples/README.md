# 优测 UBox 示例文件

本目录包含了优测 UBox 的使用示例，帮助开发者快速上手和了解 UBox 的功能。

## 📁 文件说明

### 🚀 `example.py` - 统一示例文件（推荐）
**展示三种不同的SDK初始化模式，包含完整功能演示和时间监控**

#### **三种初始化模式**
1. **调试模式（自动占用设备）**
   - 特点：自动占用、续期、释放设备

2. **调试模式（使用预获取的authCode）**
   - 适用：已有authCode
   - 特点：跳过占用流程，更稳定可靠

3. **执行模式**
   - 适用：仅限自动化脚本上传到优测平台执行
   - 特点：直接访问，性能更好
   - 注意：仅限平台环境使用

#### **推荐使用方式：上下文管理器**
使用 `with` 语句是推荐的使用方式，可以自动管理资源：

```python
# 推荐：使用上下文管理器
with UBox(mode=RunMode.DEBUG, secret_id="sid", secret_key="skey") as ubox:
    device = ubox.init_device(udid="device-001", os_type=OSType.ANDROID)
    # 执行操作...
    device_info = device.device_info()
    # 无需手动调用 ubox.close()

# 不推荐：手动管理
ubox = UBox(mode=RunMode.DEBUG, secret_id="sid", secret_key="skey")
try:
    device = ubox.init_device(udid="device-001", os_type=OSType.ANDROID)
    # 执行操作...
finally:
    ubox.close()  # 必须手动关闭
```

#### **上下文管理器的优势**
- **自动资源管理**: 自动关闭连接，无需手动调用 `close()`
- **异常安全**: 即使发生异常也会正确关闭资源
- **代码简洁**: 代码更易读，更易维护
- **避免资源泄漏**: 确保资源在作用域结束时被正确释放

## ⚡ 运行方式

```bash
# 运行示例文件
python examples/example.py
```

## 🔧 配置说明

### 必需配置
- `secret_id`: 优测平台的密钥ID
- `secret_key`: 优测平台的密钥Key
- `udid`: 设备唯一标识符
- `os_type`: 设备操作系统类型（ANDROID/IOS/HM）

### 可选配置
- `auth_code`: 预获取的认证码（用于跳过设备占用）

## 📊 时间监控功能

示例文件包含了精确到毫秒的操作时间监控：

```python
@contextmanager
def operation_timer(operation_name):
    """操作时间监控上下文管理器，精确到毫秒"""
    start_time = time.time()
    try:
        yield
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000
        print(f"⏱️ {operation_name} 执行完成，耗时: {execution_time:.2f}毫秒")
    except Exception as e:
        # 错误处理...
```

## 🎨 示例输出

运行示例后会看到类似这样的输出：

```
⏱️ 坐标点击 执行完成，耗时: 45.23毫秒
⏱️ 左右滑动 执行完成，耗时: 128.67毫秒
⏱️ 截图操作 执行完成，耗时: 89.12毫秒
```

## 🎯 事件自动处理功能

### 📁 `event_handler_example.py` - 事件自动处理示例

**展示如何使用UBox SDK的事件自动处理功能，自动处理常见的系统弹窗和权限请求**

### 📁 `watcher_example.py` - Watcher功能示例（新增）

**展示如何使用新的watcher功能，类似于u2的watcher能力，支持自动监控和处理弹窗**

#### **Watcher功能特点**
- **链式调用**: 支持 `watcher("name").when("condition").click()` 或 `watcher("name").when("condition").call(func)`
- **多种匹配方式**: 支持文本匹配和XPath匹配
- **多种动作类型**: 支持自动点击和自定义函数调用
- **后台监控**: 自动在后台监控UI变化，无需手动调用

#### **使用示例**
```python
# 配置watcher
device.handler.watcher("wsq1").when("已知悉该应用存在风险").call(handle_common_event)
device.handler.watcher("始终允许").when("始终允许").click()
device.handler.watcher("oppo安装").when('//*[@resource-id="com.android.packageinstaller:id/confirm_bottom_button_layout"]').click()

# 开始后台监控
device.handler.start(2.0)  # 每2秒检查一次

# 停止监控
device.handler.stop()
```

#### **功能特性**
- **批量加载规则**: 一次性加载多个事件处理规则
- **预设规则**: 内置常用的系统弹窗处理规则
- **自定义规则**: 支持添加自定义的事件处理逻辑
- **自动处理**: 后台自动监控和处理匹配的事件
- **同步处理**: 支持立即处理一次事件

#### **使用场景**
- **应用安装**: 自动处理权限请求和安装确认
- **系统更新**: 自动处理更新提示和权限申请
- **权限管理**: 自动处理各种应用权限请求
- **弹窗处理**: 自动关闭或确认系统弹窗

#### **核心方法**

```python
# 1. 批量加载事件处理规则
device.load_default_handler(rules_list)

# 2. 启动预设事件自动处理
device.start_event_handler()

# 3. 添加自定义事件处理规则
device.add_event_handler("匹配文本", "点击文本")

# 4. 同步处理事件（立即处理一次）
device.sync_event_handler()

# 5. 清除事件处理规则
device.clear_event_handler()

# 注意：这些方法不返回任何值，操作成功时无异常抛出，失败时抛出异常

#### **预设规则示例**

```python
# 内置的常用规则
default_rules = [
    '^(完成|关闭|关闭应用|好|允许|始终允许|好的|确定|确认|安装|下次再说|知道了|同意)$',
    r'^((?<!不)(忽略|允(\s){0,2}许|同(\s){0,2}意)|继续|清理|稍后|稍后处理|暂不|暂不设置|强制|下一步)$',
    '^((?i)allow|Sure|SURE|accept|install|done|ok)$',
    ('(建议.*清理)', '(取消|以后再说|下次再说)'),
    ('(发送错误报告|截取您的屏幕|是否删除)', '取消'),
    ('(隐私)', '同意并继续'),
    # ... 更多规则
]
```

#### **自定义规则示例**

```python
# 应用安装权限规则
install_rules = [
    ('(安装此应用需要以下权限)', '确定'),
    ('(此应用需要访问您的)', '允许'),
    ('(是否允许应用)', '允许')
]

# 系统更新提示规则
update_rules = [
    ('(系统更新)', '稍后'),
    ('(新版本可用)', '稍后提醒'),
    ('(立即更新)', '稍后')
]

# 网络权限规则
network_rules = [
    ('(网络访问权限)', '允许'),
    ('(位置信息权限)', '仅在使用时允许'),
    ('(相机权限)', '允许')
]
```

#### **运行方式**

```bash
# 运行事件处理示例
python examples/event_handler_example.py
```

#### **注意事项**

1. **规则匹配**: 使用正则表达式进行文本匹配，确保规则准确性
2. **处理顺序**: 规则按添加顺序处理，先添加的规则优先级更高
3. **性能影响**: 事件处理在后台运行，对主程序性能影响较小
4. **规则清理**: 测试完成后建议清除规则，避免影响后续操作
5. **平台兼容**: 支持Android、iOS和鸿蒙系统

#### **最佳实践**

```python
# 推荐的使用流程
try:
    # 1. 加载默认规则
    device.load_default_handler(default_rules)
    
    # 2. 启动自动处理
    device.start_event_handler()
    
    # 3. 执行主要业务逻辑
    # ... 你的测试代码 ...
    
    # 4. 可选：添加自定义规则
    device.add_event_handler("特殊弹窗", "处理方式")
    
finally:
    # 5. 清理规则（可选）
    device.clear_event_handler()
```
