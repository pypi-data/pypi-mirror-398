"""缩略图生成模块"""

from typing import Any, Optional

import plotly.graph_objects as go
import plotly.io as pio


def generate_thumbnail(
    chart_data: dict[str, Any],
    width: int = 800,
    height: int = 600,
    format: str = "webp",
) -> Optional[bytes]:
    """生成Plotly图表的缩略图

    Args:
        chart_data: 标准的Plotly图表数据，应包含'data'和'layout'字段
        width: 图片宽度（默认800像素）
        height: 图片高度（默认600像素）
        format: 图片格式，支持'webp'、'png'、'jpeg'等（默认'webp'）

    Returns:
        bytes: 图片的字节数据，如果生成失败返回None
    """
    try:
        if not isinstance(chart_data, dict) or "data" not in chart_data:
            return None

        # 使用 skip_invalid=True 跳过无效属性，validate=False 禁用验证
        fig = go.Figure(chart_data, skip_invalid=True)
        return pio.to_image(
            fig, format=format, width=width, height=height, validate=False
        )

    except Exception:
        return None
