import re
import traceback
from typing import TYPE_CHECKING, Optional, Tuple, Any, Callable
from lxml import etree

from ubox_py_sdk.models import DriverType
from ubox_py_sdk.logger import get_logger

if TYPE_CHECKING:
    from ubox_py_sdk.device import Device

logger = get_logger(__name__)

def parse_xml(uitree: str):
    # 解析XML，处理编码声明问题，但不改变编码
    try:
        xml_tree = etree.XML(uitree)
    except ValueError as e:
        if "encoding declaration" in str(e):
            # 转换为字节输入，保持编码不变
            xml_tree = etree.fromstring(uitree.encode('utf-8'))
        else:
            logger.error(f"XML解析失败: {e}")
            return None
    return xml_tree

def find_optimal_element(selector: Any, match: str, mode: str = 'auto') -> Tuple[Optional[Any], bool]:
    """
    智能查找元素，支持自定义匹配模式：
    - auto: 按优先级依次尝试 强匹配 -> 模糊匹配 -> 正则匹配
    - strict: 仅强匹配（精确匹配）
    - fuzzy: 仅模糊匹配（包含匹配）
    - regex: 仅正则表达式匹配

    Args:
        selector: 选择器对象，必须具有 xpath 方法（如 lxml ElementTree）
        match: 要匹配的文本内容
        mode: 匹配模式，默认 'auto'

    Returns:
        tuple: (匹配的元素, 是否找到)
    """
    # 类型检查：确保 selector 具有 xpath 方法
    if not hasattr(selector, 'xpath'):
        error_msg = f"选择器类型错误：期望具有 xpath 方法的对象，但收到 {type(selector).__name__} 类型"
        logger.error(error_msg)
        return None, False

    # 定义三个匹配子过程，便于根据模式控制调用顺序
    def try_strict() -> Tuple[Optional[Any], bool]:
        """强匹配：text、value、name、label 属性完全等于 match"""
        try:
            exact_xpath = f'//*[@text="{match}" or @value="{match}" or @name="{match}" or @label="{match}"]'
            elements = selector.xpath(exact_xpath)
            if elements:
                logger.info(f"强匹配{match}成功，找到 {len(elements)} 个精确匹配元素")
                return elements[0], True
        except Exception as exact_e:
            logger.debug(f"强匹配{match}失败: {exact_e}")
        return None, False

    def try_fuzzy() -> Tuple[Optional[Any], bool]:
        """模糊匹配：text、value、name、label 属性包含 match"""
        try:
            contains_xpath = (
                f'//*[contains(@text,"{match}") or '
                f'contains(@value,"{match}") or '
                f'contains(@name,"{match}") or '
                f'contains(@label,"{match}")]'
            )
            elements = selector.xpath(contains_xpath)
            if elements:
                logger.info(f"模糊匹配{match}成功，找到 {len(elements)} 个包含匹配元素")
                return elements[0], True
        except Exception as contains_e:
            logger.debug(f"模糊匹配{match}失败: {contains_e}")
        return None, False

    def try_regex() -> Tuple[Optional[Any], bool]:
        """正则匹配：使用EXSLT正则匹配 text/value/name/label"""
        try:
            xpath_regex = (
                f'//*[re:match(@text,"{match}") or '
                f're:match(@value,"{match}") or '
                f're:match(@name,"{match}") or '
                f're:match(@label,"{match}")]'
            )
            elements = selector.xpath(xpath_regex, namespaces={"re": "http://exslt.org/regular-expressions"})
            if elements:
                logger.info(f"正则表达式匹配{match}成功，找到 {len(elements)} 个正则匹配元素")
                return elements[0], True
        except Exception as regex_e:
            logger.debug(f"正则表达式匹配{match}失败: {regex_e}")
        return None, False

    # 根据模式执行匹配
    mode_normalized = (mode or 'auto').lower()
    if mode_normalized == 'strict':
        return try_strict()
    if mode_normalized == 'fuzzy':
        return try_fuzzy()
    if mode_normalized == 'regex':
        return try_regex()

    # auto 模式：严格 -> 模糊 -> 正则
    for fn in (try_strict, try_fuzzy, try_regex):
        node, ok = fn()
        if ok:
            return node, True

    logger.debug(f"未找到匹配 '{match}' 的元素")
    return None, False


class Watcher:
    """单个watcher配置类，支持多个条件和动作"""

    def __init__(self, device: 'Device', name: str):
        self.device = device
        self.name = name
        self.conditions = []  # 匹配条件列表
        self.action = None  # 执行动作
        self.action_type = None  # 动作类型：'click' 或 'call'
        self.match_mode = 'auto'  # 匹配模式：auto/strict/fuzzy/regex（可在watcher中自定义）

    def when(self, condition: str) -> 'Watcher':
        """添加匹配条件
        
        Args:
            condition: 匹配条件，可以是文本或XPath
            
        Returns:
            self: 支持链式调用
        """
        self.conditions.append(condition)
        return self

    def with_match_mode(self, mode: str) -> 'Watcher':
        """设置匹配模式（在watcher级别生效）

        Args:
            mode: 匹配模式：'auto' | 'strict' | 'fuzzy' | 'regex'

        Returns:
            self: 支持链式调用
        """
        # 仅接受预期值，非法值回退到 auto
        normalized = (mode or 'auto').lower()
        if normalized not in ('auto', 'strict', 'fuzzy', 'regex'):
            normalized = 'auto'
        self.match_mode = normalized
        return self

    def click(self) -> 'Watcher':
        """设置动作为点击"""
        self.action_type = 'click'
        self.action = 'click'
        return self

    def call(self, func: Callable[['Device', Any, Any], Any]) -> 'Watcher':
        """设置动作为调用函数
        
        Args:
            func: 要调用的函数: def action_example(device, xml_element, smart_click)
            device是设备对象，可以device.click等等；
            xml_element是匹配到的XML元素；
            smart_click是handler提供的智能点击方式，可以模糊、强制、正则等方式自动匹配文本去点击xpath
            >>>def smart_click(self, text: str) -> bool

        Returns:
            self: 支持链式调用
        """
        self.action_type = 'call'
        self.action = func
        return self


class EventHandler:
    """事件处理器，支持watcher模式自动处理弹窗和事件"""

    def __init__(self, device: 'Device'):
        self.device = device
        self.watchers = {}  # 存储watcher配置
        self.running = False
        self._monitor_thread = None
        self._monitor_interval = 2.0

    def start(self, interval: float = 2.0):
        """开始后台监控
        
        Args:
            interval: 监控间隔时间（秒），默认2.0秒
        """
        if self.running:
            logger.warning("监控已在运行中")
            return

        self.running = True
        self._monitor_interval = interval
        logger.info(f"事件监控已启动，监控间隔: {interval}秒")

        # 启动后台监控线程
        self._start_monitor_thread()

    def stop(self):
        """停止后台监控"""
        if not self.running:
            logger.warning("监控未在运行")
            return

        self.running = False
        logger.info("事件监控已停止")

        # 等待监控线程结束
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1.0)
            logger.info("后台监控线程已停止")

    def reset(self):
        """重置所有watcher配置"""
        self.watchers.clear()
        logger.info("所有watcher配置已重置")

    def watcher(self, name: str) -> 'Watcher':
        """创建或获取一个watcher
        
        Args:
            name: watcher名称
            
        Returns:
            Watcher实例
        """
        if name not in self.watchers:
            self.watchers[name] = Watcher(self.device, name)
        return self.watchers[name]

    def _start_monitor_thread(self):
        """启动监控线程"""
        import threading
        import time

        def monitor_worker():
            """后台监控工作线程"""
            logger.info("监控线程已启动")
            while self.running:
                try:
                    # 获取当前UI树
                    uitree = self.device.get_uitree(xml=True)
                    if uitree:
                        # 检查是否匹配任何watcher
                        self._process_watchers(uitree)
                except Exception as e:
                    logger.warning(f"后台监控异常: {e}")

                # 等待指定间隔
                time.sleep(self._monitor_interval)

            logger.info("监控线程已退出")

        # 启动监控线程
        self._monitor_thread = threading.Thread(target=monitor_worker, daemon=True, name="EventHandler-Monitor")
        self._monitor_thread.start()

    def _process_watchers(self, uitree):
        """处理所有watcher配置
        
        Args:
            uitree: UI树XML字符串
        """
        if not self.watchers:
            return

        xml_tree = etree.fromstring(uitree.encode('utf-8'))
        for watcher_name, watcher in self.watchers.items():
            if not watcher.conditions or not watcher.action:
                continue

            # 检查是否匹配任何一个条件
            matched = False
            for condition in watcher.conditions:
                # 将匹配模式从watcher传入检查函数，避免作用域问题
                xml_element, found = self._check_watcher_condition(
                    xml_tree, condition, match_mode=watcher.match_mode
                )
                if found and xml_element is not None:
                    logger.info(f"Watcher '{watcher_name}' 条件 '{condition}' 匹配成功，元素: {xml_element}")
                    # 执行动作
                    if self._execute_watcher_action(watcher, xml_element):
                        logger.info(f"Watcher '{watcher_name}' 动作执行成功")
                        matched = True
                    else:
                        logger.warning(f"Watcher '{watcher_name}' 动作执行失败")
                    break

            if not matched:
                logger.debug(f"Watcher '{watcher_name}' 所有条件都不匹配")

    def _check_watcher_condition(self, xml_tree, condition, match_mode: str = 'auto'):
        """检查watcher条件是否匹配
        
        Args:
            xml_tree: 已解析的XML树
            condition: 匹配条件（文本或XPath）
            match_mode: 匹配模式（auto/strict/fuzzy/regex）
            
        Returns:
            tuple: (匹配的元素, 是否匹配)
        """
        try:
            # 如果是XPath格式（以//开头）
            if condition.startswith('//'):
                elements = xml_tree.xpath(condition)
                if elements:
                    return elements[0], True
            else:
                # 文本匹配：根据watcher配置的匹配模式进行匹配
                return find_optimal_element(xml_tree, condition, mode=match_mode)
        except Exception as e:
            logger.warning(f"检查watcher条件失败: {e}")
        return None, False

    def _execute_watcher_action(self, watcher, xml_element):
        """执行watcher动作
        
        Args:
            watcher: Watcher实例
            xml_element: 匹配的XML元素
            
        Returns:
            bool: 动作是否执行成功
        """
        try:
            if watcher.action_type == 'click':
                # 点击动作
                center = self.find_xml_element_center(xml_element)
                if center is not None:
                    self.device.click(loc=(center[0], center[1]), by=DriverType.POS)
                    logger.info(f"Watcher点击事件: [{center[0]}, {center[1]}]")
                    return True
            elif watcher.action_type == 'call':
                # 调用函数动作
                if callable(watcher.action):
                    # 传递设备实例、匹配的元素和智能匹配方法
                    result = watcher.action(self.device, xml_element, self.smart_click)
                    logger.info(f"Watcher函数调用成功: {watcher.action.__name__}")
                    return True
                    # 注意：这里可以根据函数返回值决定是否认为执行成功
        except Exception as e:
            logger.error(f"执行watcher动作失败: {e}")
        return False

    def smart_click(self, text: str) -> bool:
        """智能点击方法，类似find_optimal_element的智能匹配
        
        Args:
            text: 要匹配的文本
        Returns:
            bool: 是否点击成功
        """
        try:
            # 获取当前UI树
            uitree = self.device.get_uitree(xml=True)
            if not uitree:
                logger.warning("无法获取UI树")
                return False

            # 解析XML，处理编码声明问题，但不改变编码
            try:
                xml_tree = etree.XML(uitree)
            except ValueError as e:
                if "encoding declaration" in str(e):
                    # 转换为字节输入，保持编码不变
                    xml_tree = etree.fromstring(uitree.encode('utf-8'))
                else:
                    logger.error(f"XML解析失败: {e}")
                    return False

            # 使用find_optimal_element进行智能匹配
            xml_element, found = find_optimal_element(xml_tree, text)
            if found and xml_element is not None:
                # 计算中心坐标并点击
                center = self.find_xml_element_center(xml_element)
                if center is not None:
                    self.device.click(loc=(center[0], center[1]), by=DriverType.POS)
                    logger.info(f"智能点击成功: {text} -> [{center[0]}, {center[1]}]")
                    return True
                else:
                    logger.warning(f"无法计算元素 {text} 的中心坐标")
            else:
                logger.warning(f"未找到匹配的元素: {text}")

        except Exception as e:
            logger.error(f"智能点击失败: {e}")

        return False

    def _parse_xml_element_bounds(self, xml_element: Any) -> Optional[dict]:
        """
        解析XML元素的边界信息
        
        Args:
            xml_element: XML元素
            
        Returns:
            dict: 包含 x, y, width, height 的字典，失败时返回None
        """
        try:
            if "bounds" in xml_element.attrib:
                bounds = xml_element.attrib["bounds"]
                rlt = re.findall(r'(\d+)', bounds)
                if len(rlt) >= 4:
                    x = int(rlt[0])
                    y = int(rlt[1])
                    width = int(rlt[2]) - x
                    height = int(rlt[3]) - y
                else:
                    return None
            else:
                x = int(xml_element.attrib.get("x", 0))
                y = int(xml_element.attrib.get("y", 0))
                width = int(xml_element.attrib.get("width", 0))
                height = int(xml_element.attrib.get("height", 0))

            if not x or not y or not width or not height:
                return None

            # 处理屏幕方向
            size = self.device.d_screen_size
            is_portrait = size[0] > size[1]
            
            if is_portrait and width < height:
                # 竖屏且元素是竖向的，需要交换坐标
                return {
                    'x': y,
                    'y': x,
                    'width': height,
                    'height': width
                }
            else:
                return {
                    'x': x,
                    'y': y,
                    'width': width,
                    'height': height
                }

        except Exception as e:
            logger.warning(f"解析XML元素边界信息失败: {e}")
            return None

    def find_xml_element_center(self, xml_element: Any) -> Optional[list]:
        """计算XML元素的中心坐标
        
        Args:
            xml_element: XML元素
            
        Returns:
            list: [x, y] 中心坐标，失败时返回None
        """
        bounds = self._parse_xml_element_bounds(xml_element)
        if bounds is None:
            return None
        
        center_x = int(bounds['x'] + bounds['width'] / 2)
        center_y = int(bounds['y'] + bounds['height'] / 2)
        return [center_x, center_y]

    def find_xml_element_size(self, xml_element: Any) -> Optional[list]:
        """计算XML元素的宽高

        Args:
            xml_element: XML元素

        Returns:
            list: [width, height] 元素尺寸，失败时返回None
        """
        bounds = self._parse_xml_element_bounds(xml_element)
        if bounds is None:
            return None
        
        return [bounds['width'], bounds['height']]

    def get_watcher_status(self):
        """获取watcher状态信息
        
        Returns:
            dict: 包含运行状态和配置信息的字典
        """
        return {
            "running": self.running,
            "monitor_interval": self._monitor_interval,
            "watcher_count": len(self.watchers),
            "watchers": {
                name: {
                    "conditions": watcher.conditions,
                    "action_type": watcher.action_type,
                    "action": watcher.action.__name__ if callable(watcher.action) else str(watcher.action)
                }
                for name, watcher in self.watchers.items()
            }
        }
