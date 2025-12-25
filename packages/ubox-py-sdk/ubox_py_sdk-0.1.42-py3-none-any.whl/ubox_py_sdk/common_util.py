import base64
import os
from io import BytesIO
from PIL import Image
from typing import Dict, Any, Tuple, Union
import json
from ubox_py_sdk.logger import get_logger

logger = get_logger(__name__)


def save_base64_image(b64_str, out_path):
    import base64, os
    if ',' in b64_str:
        b64_str = b64_str.split(',', 1)[1]
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(base64.b64decode(b64_str))


def print_curl_info(method: str, url: str, params: Dict[str, Any],
                    data: Dict[str, Any], headers: Dict[str, str]) -> None:
    """打印curl命令信息，方便调试和复制使用

    Args:
        method: HTTP方法
        url: 请求URL
        params: 查询参数
        data: 请求体数据
        headers: 请求头
    """
    try:
        # 构建查询字符串
        query_string = ""
        if params:
            query_parts = []
            for k, v in params.items():
                if isinstance(v, (list, tuple)):
                    for item in v:
                        query_parts.append(f"{k}={item}")
                else:
                    query_parts.append(f"{k}={v}")
            query_string = "&".join(query_parts)

        # 构建完整的URL
        full_url = url
        if query_string:
            full_url = f"{url}?{query_string}"

        # 构建curl命令
        curl_parts = [f"curl -X {method.upper()}"]

        # 添加请求头
        for k, v in headers.items():
            curl_parts.append(f'-H "{k}: {v}"')

        # 添加请求体
        if data and method.upper() in ['POST', 'PUT', 'PATCH']:
            data_json = json.dumps(data, ensure_ascii=False, indent=2)
            curl_parts.append(f"-d '{data_json}'")

        # 添加URL
        curl_parts.append(f'"{full_url}"')

        # 组合完整的curl命令
        curl_command = " ".join(curl_parts)

        # 打印curl信息
        logger.info(f"=== CURL命令 ===")
        logger.info(f"URL: {full_url}")
        logger.info(f"方法: {method.upper()}")
        if headers:
            logger.info(f"请求头: {json.dumps(headers, ensure_ascii=False, indent=2)}")
        if data:
            logger.info(f"请求体: {json.dumps(data, ensure_ascii=False, indent=2)}")
        logger.info(f"完整curl命令:")
        logger.info(curl_command)
        logger.info(f"==================")

    except Exception as e:
        logger.warning(f"生成curl信息失败: {e}")


def crop_base64_image(base64_str: str,
                      crop: Tuple[Union[int, float], Union[int, float], Union[int, float], Union[int, float]]) -> str:
    """
    crop: tuple of four numbers (left, upper, right, lower)
      - 如果所有元素都在0~1之间，视为比例 (0.1, 0.1, 0.9, 0.9)
      - 否则视为像素坐标(100, 50, 400, 300)

    返回裁剪后的base64 png字符串，带 data:image/png;base64, 前缀
    """

    if base64_str.startswith('data:image'):
        base64_str = base64_str.split(',', 1)[1]

    img_data = base64.b64decode(base64_str)
    img = Image.open(BytesIO(img_data))
    width, height = img.size

    # 判定crop类型
    if all(0 <= x <= 1 for x in crop):
        # 视为比例裁剪
        left = int(width * crop[0])
        upper = int(height * crop[1])
        right = int(width * crop[2])
        lower = int(height * crop[3])
    else:
        # 视为像素坐标裁剪
        left, upper, right, lower = crop

    # 限制边界
    left = max(0, min(left, width - 1))
    right = max(left + 1, min(right, width))
    upper = max(0, min(upper, height - 1))
    lower = max(upper + 1, min(lower, height))

    cropped_img = img.crop((left, upper, right, lower))

    buffered = BytesIO()
    cropped_img.save(buffered, format="PNG")
    cropped_base64 = base64.b64encode(buffered.getvalue()).decode()

    return "data:image/png;base64," + cropped_base64


def crop_image_save(input_path: str,
                    crop: Tuple[Union[int, float], Union[int, float], Union[int, float], Union[int, float]],
                    suffix='_cropped') -> str:
    """
    从图片路径读取图片，根据crop裁剪后，保存为同目录下的新文件

    参数：
        input_path (str): 原图片文件路径
        crop (tuple): (left, upper, right, lower)，坐标或比例（0~1）
        suffix (str): 新文件名后缀（默认 '_cropped'）

    返回：
        str: 新图片文件完整路径
    """

    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"文件不存在: {input_path}")

    img = Image.open(input_path)
    width, height = img.size

    if len(crop) != 4:
        raise ValueError("crop 必须是长度为4的元组或列表")

    # 判断是比例还是像素坐标
    if all(0 <= x <= 1 for x in crop):
        left = int(width * crop[0])
        upper = int(height * crop[1])
        right = int(width * crop[2])
        lower = int(height * crop[3])
    else:
        left, upper, right, lower = crop

    # 限制边界
    left = max(0, min(left, width - 1))
    right = max(left + 1, min(right, width))
    upper = max(0, min(upper, height - 1))
    lower = max(upper + 1, min(lower, height))

    cropped_img = img.crop((left, upper, right, lower))

    base_dir, filename = os.path.split(input_path)
    name, ext = os.path.splitext(filename)
    new_name = f"{name}{suffix}{ext}"
    new_path = os.path.join(base_dir, new_name)

    cropped_img.save(new_path)

    return new_path


def make_dir(path: str) -> None:
    """
    创建目录，如果目录已存在则忽略

    Args:
        path (str): 要创建的目录路径
    """
    try:
        if not os.path.isdir(path):
            os.makedirs(path)
    except Exception as e:
        print("make_dir Exception:" + str(e))
