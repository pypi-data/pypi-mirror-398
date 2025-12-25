"""工具函数"""

import math
import os
import re
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any, Optional, Union

import orjson
import requests

from .exceptions import APIError


def sanitize_filename(filename: str, max_length: int = 100) -> str:
    """清理文件名，保留中文等 Unicode 字符

    Args:
        filename: 原始文件名
        max_length: 最大长度

    Returns:
        清理后的文件名
    """
    # 保留字母、数字、中文、日文、韩文等常见字符，以及 .-_
    filename = re.sub(
        r"[^\w\u4e00-\u9fff\u3040-\u309f\u30a0-\u30ff\uac00-\ud7af\.-]", "_", filename
    )

    # 移除开头和结尾的特殊字符
    filename = filename.strip("._")

    # 限制长度
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        if ext:
            name = name[: max_length - len(ext)]
            filename = name + ext
        else:
            filename = filename[:max_length]

    return filename or "unnamed"


def make_safe_filename(name: str, ext: str = "") -> str:
    """生成安全的文件名

    将任意输入转换为适合OSS存储的安全文件名

    Args:
        name: 基础文件名
        ext: 文件扩展名（可以带或不带点）

    Returns:
        str: 安全的文件名，总长度不超过100字符

    Example:
        >>> make_safe_filename("中文图表@#$", "json")
        "中文图表.json"
        >>> make_safe_filename("long_name_" * 20, ".txt")
        "long_name_long_name_long_name_...txt"
    """
    # 标准化扩展名格式
    if ext and not ext.startswith("."):
        ext = "." + ext

    # 考虑扩展名长度，为基础名预留空间
    max_name_length = 80 - len(ext)
    safe_name = sanitize_filename(name, max_length=max_name_length)

    return f"{safe_name}{ext}"


def read_file_content(file_path: Union[str, Path]) -> Union[dict[str, Any], bytes]:
    """读取文件内容

    Args:
        file_path: 文件路径

    Returns:
        JSON 文件返回字典，其他文件返回字节
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"文件不存在: {file_path}")

    if file_path.suffix.lower() == ".json":
        with open(file_path, encoding="utf-8") as f:
            return orjson.loads(f.read())
    else:
        with open(file_path, "rb") as f:
            return f.read()


def get_file_size(file_path: Union[str, Path]) -> int:
    """获取文件大小（字节）

    Args:
        file_path: 文件路径

    Returns:
        文件大小（字节）
    """
    return Path(file_path).stat().st_size


def format_file_size(size_bytes: Optional[int] = None) -> str:
    """格式化文件大小为人类可读格式

    Args:
        size_bytes: 文件大小（字节）

    Returns:
        格式化后的字符串
    """
    if size_bytes is None:
        return "0 B"

    size: float = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def handle_api_response(
    response: requests.Response, operation: str = "API调用"
) -> dict[str, Any]:
    """统一处理 API 响应

    Args:
        response: requests 响应对象
        operation: 操作描述，用于错误信息

    Returns:
        解析后的响应数据

    Raises:
        APIError: 当 HTTP 状态码非 200 或业务错误码非 200 时
    """
    if response.status_code == 200:
        response_data = orjson.loads(response.content)

        # 检查业务错误码
        if "code" in response_data and response_data.get("code") != 200:
            error_msg = f"{operation}失败: {response_data.get('message', '未知错误')}"
            raise APIError(error_msg, response_data.get("code"), response)

        return response_data
    else:
        error_msg = f"{operation}失败: HTTP {response.status_code}"
        try:
            error_detail = orjson.loads(response.content)
            if "detail" in error_detail:
                error_msg += f" - {error_detail['detail']}"
            elif "error" in error_detail:
                error_msg += f" - {error_detail['error']}"
        except (orjson.JSONDecodeError, ValueError, KeyError):
            error_msg += f" - {response.text}"
        except Exception as e:
            error_msg += f" - 响应解析失败: {e}"

        raise APIError(error_msg, response.status_code, response)


def round_floats(o: Any, precision: int = 3) -> Any:
    """递归处理数据结构中的浮点数，使用 decimal 实现精确四舍五入

    对于 NaN 和 Infinity 等特殊值，转换为 None 以确保 JSON 兼容性。

    Args:
        o: 要处理的对象
        precision: 保留的小数位数（0-10），默认为 3

    Returns:
        处理后的对象，NaN/Infinity 转换为 None
    """
    if isinstance(o, float):
        if math.isnan(o) or math.isinf(o):
            return None

        # 使用 decimal 进行精确四舍五入
        try:
            decimal_value = Decimal(str(o))
            quantizer = Decimal("0.1") ** precision
            rounded = decimal_value.quantize(quantizer, rounding=ROUND_HALF_UP)
            return float(rounded)
        except (ValueError, ArithmeticError):
            # 如果 decimal 转换失败，回退到普通 round
            return round(o, precision)
    elif isinstance(o, dict):
        return {k: round_floats(v, precision) for k, v in o.items()}
    elif isinstance(o, (list, tuple)):
        return type(o)(round_floats(x, precision) for x in o)
    return o


def get_json_size(data: Any) -> int:
    """获取数据序列化为 JSON 后的字节大小

    Args:
        data: 要序列化的数据

    Returns:
        JSON 字节大小
    """
    json_str = orjson.dumps(data).decode("utf-8")
    return len(json_str.encode("utf-8"))


def get_temp_dir(custom_dir: Optional[str] = None, purpose: str = "oss-upload") -> str:
    """获取可用的临时目录

    Args:
        custom_dir: 自定义临时目录，优先使用
        purpose: 目录用途，用于创建子目录

    Returns:
        可用的临时目录路径
    """
    import tempfile

    # 候选目录列表，按优先级排序
    candidates = []
    if custom_dir and isinstance(custom_dir, str):
        candidates.append(os.path.expanduser(custom_dir))

    candidates.extend(
        [
            os.path.join(tempfile.gettempdir(), f"lims2-{purpose}"),
            os.path.expanduser(f"~/.cache/lims2-sdk/{purpose}"),
            f".lims2-{purpose}",
        ]
    )

    # 测试每个目录
    for temp_dir in candidates:
        try:
            Path(temp_dir).mkdir(parents=True, exist_ok=True)
            test_file = Path(temp_dir) / ".test"
            test_file.write_text("test")
            test_file.unlink()
            return temp_dir
        except (PermissionError, OSError):
            continue

    # 兜底方案
    fallback = os.path.join(tempfile.gettempdir(), f"lims2-{os.getpid()}")
    Path(fallback).mkdir(parents=True, exist_ok=True)
    return fallback


def detect_task_hash() -> Optional[str]:
    """从当前工作目录检测 Nextflow task hash

    检测逻辑：从当前目录路径中匹配 `work/{xx}/{xxxxxx...}` 模式，
    提取 hashLog 格式：`xx/xxxxxx`（前 2 位 + 后 6 位）

    Returns:
        task hash（格式：xx/xxxxxx），如果未检测到则返回 None

    Example:
        >>> # 在 /path/to/work/2f/0075a6xxx/output 目录中
        >>> detect_task_hash()
        '2f/0075a6'
        >>> # 在普通目录中
        >>> detect_task_hash()
        None
    """
    cwd = os.getcwd()
    # 匹配 work/xx/xxxxxx 模式（至少 6 个十六进制字符）
    pattern = r"/work/([0-9a-f]{2})/([0-9a-f]{6})"
    match = re.search(pattern, cwd.lower())
    if match:
        return f"{match.group(1)}/{match.group(2)}"
    return None


def validate_task_hash(task_hash: str) -> bool:
    """验证 task hash 格式

    格式要求: xx/xxxxxx（2位/6位，共9字符，全部为十六进制字符）

    Args:
        task_hash: 要验证的 task hash

    Returns:
        True 如果格式有效，False 否则
    """
    if not task_hash:
        return True  # 可选参数，空值有效
    pattern = r"^[0-9a-f]{2}/[0-9a-f]{6}$"
    return bool(re.match(pattern, task_hash.lower()))


def clean_plotly_data(data: dict) -> dict:
    """优化Plotly数据中的template以减少文件大小

    Args:
        data: Plotly图表数据（会被直接修改）

    Returns:
        dict: 输入的data对象（template已优化）
    """
    if isinstance(data, dict) and "layout" in data and "template" in data["layout"]:
        # 提取实际使用的图表类型
        used_types = set()
        for trace in data.get("data", []):
            if isinstance(trace, dict):
                chart_type = trace.get("type", "scatter")
                used_types.add(chart_type)

        # 优化template
        data["layout"]["template"] = optimize_plotly_template(
            data["layout"]["template"], used_types or {"scatter"}
        )

    return data


def optimize_plotly_template(template: dict, used_types: set) -> dict:
    """根据使用的图表类型过滤template配置

    Args:
        template: 原始template配置
        used_types: 需要保留的图表类型集合

    Returns:
        dict: 优化后的template
    """
    if (
        not isinstance(template, dict)
        or "data" not in template
        or not isinstance(template["data"], dict)
    ):
        return template

    # 直接过滤，只拷贝需要保留的部分
    filtered_data = {
        chart_type: template["data"][chart_type]
        for chart_type in template["data"]
        if chart_type in used_types
    }

    # 浅拷贝template，只替换data部分
    return {**template, "data": filtered_data}
