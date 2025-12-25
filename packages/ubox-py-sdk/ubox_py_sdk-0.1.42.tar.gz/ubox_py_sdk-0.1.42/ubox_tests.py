import time
import uuid

from ubox_py_sdk import DriverType, RunMode, OSType, DeviceButton, UBox, operation_timer

from examples.config import get_ubox_config, get_device_config
from examples.example import demo_install_app_features

# 从配置文件获取UBox配置
ubox_config = get_ubox_config()
device_config = get_device_config()


def test_concurrency(device):
    """完整功能演示 - 调用所有模块的演示函数"""
    print("\n=== 完整功能演示 ===")
    # 调用各个功能模块的演示函数
    # 并发获取uitree信息10次
    print("\n=== 并发执行测试 ===")
    with operation_timer("并发获取uitree信息10次"):
        from concurrent.futures import ThreadPoolExecutor, as_completed
        import time

        def get_uitree_concurrent(device, index):
            """并发获取uitree的单个任务"""
            start_time = time.time()
            request_start = time.time()
            try:
                # 记录请求开始时间
                print(f"任务 {index + 1} 开始请求 - 时间: {time.strftime('%H:%M:%S.%f')[:-3]}")
                json_xml_tree = device.get_uitree()
                request_end = time.time()
                end_time = time.time()
                return {
                    'index': index,
                    'success': True,
                    'data_length': len(json_xml_tree) if json_xml_tree else 0,
                    'time_taken': end_time - start_time,
                    'request_time': request_end - request_start,
                    'data_preview': json_xml_tree[:50] if json_xml_tree else None,
                    'start_time': start_time,
                    'end_time': end_time
                }
            except Exception as e:
                request_end = time.time()
                end_time = time.time()
                return {
                    'index': index,
                    'success': False,
                    'error': str(e),
                    'time_taken': end_time - start_time,
                    'request_time': request_end - request_start,
                    'start_time': start_time,
                    'end_time': end_time
                }

        # 使用线程池并发执行10次
        with ThreadPoolExecutor(max_workers=10) as executor:
            # 提交所有任务
            future_to_index = {
                executor.submit(get_uitree_concurrent, device, i): i
                for i in range(10)
            }

            # 收集结果
            results = []
            for future in as_completed(future_to_index):
                result = future.result()
                results.append(result)
                print(f"任务 {result['index'] + 1}: {'成功' if result['success'] else '失败'} - "
                      f"总耗时: {result['time_taken']:.3f}秒 - "
                      f"请求耗时: {result['request_time']:.3f}秒")


# 测试504
def test_install_app(device):
    demo_install_app_features(device)

# 测试15分钟后授权码过期
def test_authcode_expire(device):
    print("发起第一次")
    device.device_info()
    time.sleep(16 * 60)
    print("等待16分钟 发起第2次")
    trace_id = time.strftime("%Y%m%d%H%M%S") + "_" + str(uuid.uuid4())
    print(f"第2次请求的TraceId: {trace_id}")
    device.device_info(trace_id=trace_id)

if __name__ == '__main__':
    print("\n示例：")
    try:
        with UBox(
                # 使用时按这个注释写
                mode=RunMode.NORMAL,
                env="test",
                secret_id=ubox_config.get('secret_id'),
                secret_key=ubox_config.get('secret_key'),
        ) as ubox:
            # 初始化设备
            device = ubox.init_device(
                udid=device_config['default_udid'],
                os_type=OSType(device_config['default_os_type'])
                # auth_code="your_auth_code_here",
            )
            print(f"设备初始化成功: {device.udid}")
            # 执行操作
            test_concurrency(device)
    except Exception as e:
        print(f"❌ 示例执行失败: {e}")
