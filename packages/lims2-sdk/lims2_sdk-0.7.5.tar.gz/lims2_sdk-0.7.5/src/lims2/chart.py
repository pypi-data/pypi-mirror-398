"""图表服务模块

基于原 biotree_chart 功能实现
"""

import gzip
import hashlib
import logging
from pathlib import Path
from typing import Any, Optional, Union

import orjson

from .network import network_retry
from .oss_base import OSSMixin
from .thumbnail import generate_thumbnail
from .utils import (
    clean_plotly_data,
    detect_task_hash,
    get_file_size,
    handle_api_response,
    make_safe_filename,
    read_file_content,
    round_floats,
    validate_task_hash,
)

logger = logging.getLogger("lims2.chart")


class ChartService(OSSMixin):
    """图表服务"""

    def __init__(self, client):
        """初始化图表服务

        Args:
            client: Lims2Client 实例
        """
        self.client = client
        self.config = client.config
        self.session = client.session

        # 初始化OSS混入功能
        self.__init_oss__()

    def upload(
        self,
        data_source: Union[dict[str, Any], str, Path],
        project_id: str,
        chart_name: str,
        sample_id: Optional[str] = None,
        chart_type: Optional[str] = None,
        description: Optional[str] = None,
        contrast: Optional[str] = None,
        analysis_node: Optional[str] = None,
        precision: Optional[int] = None,
        generate_thumbnail: Optional[bool] = None,
        file_name: Optional[str] = None,
        task_hash: Optional[str] = None,
    ) -> dict[str, Any]:
        """上传图表

        Args:
            data_source: 图表数据源，可以是字典、文件路径或 Path 对象
            project_id: 项目 ID
            chart_name: 图表名称
            sample_id: 样本 ID（可选）
            chart_type: 图表类型（可选）
            description: 图表描述（可选）
            contrast: 对比策略（可选，有 task_hash 时在 OSS 路径中被忽略，但仍会上报到 API）
            analysis_node: 分析节点名称（可选）
            precision: 浮点数精度控制，保留小数位数（0-10，默认3）
            generate_thumbnail: 是否生成缩略图，None时使用配置中的auto_generate_thumbnail
            file_name: 自定义基础文件名（仅对字典数据有效），如有 contrast/sample_id/chart_type 会自动追加 hash 后缀
            task_hash: Nextflow task hash（格式：xx/xxxxxx），不指定时自动检测

        Returns:
            上传结果
        """
        # 验证并处理参数
        chart_name = self._validate_and_process_params(
            chart_name, project_id, data_source, precision
        )

        # 自动检测或验证 task_hash
        if task_hash is None:
            task_hash = detect_task_hash()
        elif task_hash and not validate_task_hash(task_hash):
            raise ValueError(
                f"无效的 task_hash 格式: {task_hash}，"
                "应为 xx/xxxxxx（2位/6位十六进制字符）"
            )

        # 构建请求数据
        request_data = self._build_request_data(
            chart_name,
            project_id,
            chart_type,
            description,
            sample_id,
            contrast,
            analysis_node,
            task_hash,
        )

        # 根据数据源类型处理
        if isinstance(data_source, dict):
            return self._upload_from_dict(
                request_data, data_source, precision, generate_thumbnail, file_name
            )
        elif isinstance(data_source, (str, Path)):
            return self._upload_from_file(
                request_data, data_source, precision, generate_thumbnail
            )
        else:
            raise ValueError("数据源必须是字典、文件路径或 Path 对象")

    def _validate_and_process_params(
        self,
        chart_name: str,
        project_id: str,
        data_source: Any,
        precision: Optional[int],
    ) -> str:
        """验证并处理上传参数

        Returns:
            处理后的chart_name（可能被截短）
        """
        if not chart_name:
            raise ValueError("图表名称不能为空")
        if len(chart_name) > 80:
            original_name = chart_name
            chart_name = chart_name[:80]
            logger.warning(
                f"图表名称长度超过80个字符，已自动截短: '{original_name}' -> '{chart_name}'"
            )
        if not project_id:
            raise ValueError("项目 ID 不能为空")
        if not data_source:
            raise ValueError("数据源不能为空")
        if precision is not None and not 0 <= precision <= 10:
            raise ValueError("precision 必须在 0-10 之间")
        return chart_name

    def _build_request_data(
        self,
        chart_name: str,
        project_id: str,
        chart_type: Optional[str],
        description: Optional[str],
        sample_id: Optional[str],
        contrast: Optional[str],
        analysis_node: Optional[str],
        task_hash: Optional[str] = None,
    ) -> dict[str, Any]:
        """构建请求数据字典"""
        request_data = {
            "chart_name": chart_name,
            "project_id": project_id,
            "chart_type": chart_type,
            "description": description,
        }

        # 添加可选参数
        if sample_id:
            request_data["sample_id"] = sample_id
        if contrast:
            request_data["contrast"] = contrast
        if analysis_node:
            request_data["analysis_node"] = analysis_node
        if task_hash:
            request_data["task_hash"] = task_hash

        return request_data

    def _upload_from_dict(
        self,
        request_data: dict[str, Any],
        chart_data: dict[str, Any],
        precision: Optional[int] = None,
        generate_thumbnail: Optional[bool] = None,
        file_name: Optional[str] = None,
    ) -> dict[str, Any]:
        """从字典数据上传图表"""
        # 检测渲染器类型并处理数据
        chart_data = self._prepare_chart_data(request_data, chart_data, precision)

        # 设置文件信息
        base_name = file_name if file_name else request_data["chart_name"]
        request_data["file_name"] = self._generate_unique_filename(
            request_data, base_name
        )
        request_data["file_format"] = "json"

        # 上传到OSS
        json_str = orjson.dumps(chart_data).decode("utf-8")
        self._upload_chart_to_oss(request_data, json_str)

        # 处理缩略图
        self._handle_thumbnail_generation(request_data, chart_data, generate_thumbnail)

        # 创建图表记录
        return self._create_chart_record(request_data)

    def _prepare_chart_data(
        self, request_data: dict, chart_data: dict, precision: Optional[int]
    ) -> dict:
        """准备图表数据：检测类型、清理数据、应用精度控制"""
        # 检测渲染器类型
        if "data" in chart_data and "layout" in chart_data:
            request_data["renderer_type"] = "plotly"
        elif "elements" in chart_data or (
            "nodes" in chart_data and "edges" in chart_data
        ):
            request_data["renderer_type"] = "cytoscape"
        else:
            raise ValueError("不支持的图表数据格式")

        # 清理Plotly数据，移除不必要的属性
        if request_data["renderer_type"] == "plotly":
            chart_data = clean_plotly_data(chart_data)

        # 应用精度控制并返回处理后的数据
        precision = precision if precision is not None else 3
        return round_floats(chart_data, precision)

    def _generate_unique_filename(self, request_data: dict, base_name: str) -> str:
        """根据图表属性生成唯一文件名

        将 contrast、sample_id、chart_type 组合计算哈希，追加到基础文件名后

        Args:
            request_data: 图表请求数据
            base_name: 基础文件名（来自 chart_name、file_name 参数或 file_path.stem）

        Returns:
            str: 唯一文件名，格式为 "{base_name}_{hash8}" 或 "{base_name}"
        """
        # 收集用于计算哈希的属性
        hash_parts = []
        for key in ("contrast", "chart_type", "sample_id"):
            value = request_data.get(key)
            if value:
                hash_parts.append(f"{key}:{value}")

        # 如果没有额外属性，直接返回基础名
        if not hash_parts:
            return base_name

        # 计算哈希并追加到文件名
        hash_input = "|".join(hash_parts)
        hash_suffix = hashlib.md5(hash_input.encode()).hexdigest()[:8]
        return f"{base_name}_{hash_suffix}"

    def _upload_chart_to_oss(self, request_data: dict, json_str: str) -> str:
        """上传图表数据到OSS"""
        compressed_data = gzip.compress(json_str.encode("utf-8"))
        oss_filename = make_safe_filename(request_data["file_name"], "json")
        oss_key = self._build_chart_oss_key(
            request_data["project_id"],
            oss_filename,
            request_data.get("analysis_node"),
            request_data.get("contrast"),
            request_data.get("sample_id"),
            request_data.get("task_hash"),
        )
        bucket = self._get_oss_bucket(request_data["project_id"])

        # 检查文件是否已存在
        data_size = len(compressed_data)
        if self._check_file_exists_and_same_size(bucket, oss_key, data_size):
            logger.info(f"文件已存在且大小相同，跳过OSS上传: {oss_key}")
        else:
            self._put_object_with_retry(
                bucket,
                oss_key,
                compressed_data,
                headers={
                    "Content-Type": "application/json",
                    "Content-Encoding": "gzip",
                },
            )

        request_data["oss_key"] = oss_key
        return oss_key

    def _handle_thumbnail_generation(
        self, request_data: dict, chart_data: dict, generate_thumbnail: Optional[bool]
    ) -> None:
        """处理缩略图生成"""
        should_generate = (
            generate_thumbnail
            if generate_thumbnail is not None
            else self.config.auto_generate_thumbnail
        )
        if should_generate:
            renderer_type = request_data.get("renderer_type")
            if renderer_type == "plotly":
                logger.debug("开始生成Plotly缩略图...")
                self._generate_and_upload_thumbnail(chart_data, request_data)
            elif renderer_type == "cytoscape":
                logger.debug("设置Cytoscape网络图缩略图...")
                self._set_cytoscape_thumbnail(request_data)

    def _upload_from_file(  # noqa: C901
        self,
        request_data: dict[str, Any],
        file_path: Union[str, Path],
        precision: Optional[int] = None,
        generate_thumbnail: Optional[bool] = None,
    ) -> dict[str, Any]:
        """从文件上传图表"""
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        file_format = file_path.suffix.lower().strip(".")
        request_data["file_size"] = get_file_size(file_path)

        # JSON 文件特殊处理
        if file_format == "json":
            try:
                chart_data = read_file_content(file_path)
                if isinstance(chart_data, dict):
                    # JSON文件上传：使用文件名（不带扩展名）
                    request_data["file_name"] = file_path.stem
                    return self._upload_from_dict(
                        request_data,
                        chart_data,
                        precision,
                        generate_thumbnail,
                    )
            except FileNotFoundError:
                raise
            except orjson.JSONDecodeError as e:
                raise ValueError(f"JSON 文件格式错误: {e}")
            except Exception as e:
                raise ValueError(f"读取 JSON 文件失败: {e}")

        # 其他文件类型
        if file_format in ["png", "jpg", "jpeg", "svg", "pdf"]:
            request_data["renderer_type"] = "image"
        elif file_format == "html":
            request_data["renderer_type"] = "html"
        else:
            raise ValueError(f"不支持的文件格式: {file_format}")

        # 设置文件信息
        request_data["file_name"] = self._generate_unique_filename(
            request_data, file_path.stem
        )
        request_data["file_format"] = file_format
        # 生成安全的文件名
        oss_filename = make_safe_filename(request_data["file_name"], file_format)

        # 构建OSS键名
        oss_key = self._build_chart_oss_key(
            request_data["project_id"],
            oss_filename,
            request_data.get("analysis_node"),
            request_data.get("contrast"),
            request_data.get("sample_id"),
            request_data.get("task_hash"),
        )

        # 读取文件内容
        raw_content = read_file_content(file_path)
        file_content: bytes = (
            orjson.dumps(raw_content) if isinstance(raw_content, dict) else raw_content
        )

        # 检查文件是否已存在且大小相同
        content_size = len(file_content)
        bucket = self._get_oss_bucket(request_data["project_id"])

        if self._check_file_exists_and_same_size(bucket, oss_key, content_size):
            logger.info(f"文件已存在且大小相同，跳过OSS上传: {oss_key}")
            # 文件已存在，跳过OSS上传，但仍然创建数据库记录
        else:
            # 上传到 OSS
            content_type = self._get_content_type(file_format)

            # 上传到OSS，如果失败则直接抛出原始异常，不创建数据库记录
            result = self._put_object_with_retry(
                bucket, oss_key, file_content, headers={"Content-Type": content_type}
            )

            if result.status == 200:
                logger.info(f"OSS上传成功: {oss_key}")

        request_data["oss_key"] = oss_key

        # 创建图表记录
        return self._create_chart_record(request_data)

    def _build_chart_oss_key(
        self,
        project_id: str,
        filename: str,
        analysis_node: Optional[str] = None,
        contrast: Optional[str] = None,
        sample_id: Optional[str] = None,
        task_hash: Optional[str] = None,
    ) -> str:
        """构建图表的OSS键名

        根据是否提供 task_hash 使用不同的路径策略：
        - 有 task_hash：biochart/{env}/{project_id}/{analysis_node}/{bucket}/{suffix}/{filename}
        - 无 task_hash：biochart/{env}/{project_id}/{analysis_node}/{contrast}/{sample_id}/{filename}

        Args:
            project_id: 项目ID（必需）
            filename: 文件名（必需）
            analysis_node: 分析节点名称（可选）
            contrast: 对比策略（可选，有 task_hash 时在 OSS 路径中被忽略，但仍会上报到 API）
            sample_id: 样本ID（可选，有 task_hash 时被忽略）
            task_hash: Nextflow task hash（格式：xx/xxxxxx）

        Returns:
            str: OSS键名
            - 环境前缀：生产环境使用media，测试环境使用test
        """
        # 使用环境相关的路径前缀
        env_prefix = self._get_oss_path_prefix()
        parts = ["biochart", env_prefix, project_id]

        if analysis_node:
            parts.append(analysis_node)

        if task_hash:
            # 策略 A：有 task_hash，用 task_hash 替代 contrast/sample_id
            parts.extend(task_hash.split("/"))
        else:
            # 策略 B：原有路径方案
            if contrast:
                parts.append(contrast)
            if sample_id:
                parts.append(sample_id)

        parts.append(filename)
        return "/".join(parts)

    @network_retry(max_retries=3, base_delay=1.0, max_delay=15.0)
    def _create_chart_record(self, request_data: dict[str, Any]) -> dict[str, Any]:
        """创建图表记录"""

        request_data["token"] = self.config.token
        request_data["team_id"] = self.config.team_id

        # 使用配置的超时时间和分离的连接/读取超时
        timeout = (self.config.connection_timeout, self.config.read_timeout)

        response = self.session.post(
            f"{self.config.api_url}/get_data/biochart/create_chart/",
            json=request_data,
            timeout=timeout,
        )
        result = handle_api_response(response, "创建图表记录")

        # 将截短后的chart_name添加到返回结果中，方便CLI显示
        result["record"]["chart_name"] = request_data["chart_name"]
        return result

    def _get_content_type(self, file_format: str) -> str:
        """获取文件内容类型"""
        content_types = {
            "json": "application/json",
            "png": "image/png",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "svg": "image/svg+xml",
            "pdf": "application/pdf",
            "html": "text/html",
        }
        return content_types.get(file_format, "application/octet-stream")

    def _generate_and_upload_thumbnail(
        self, chart_data: dict[str, Any], request_data: dict[str, Any]
    ) -> None:
        """生成并上传缩略图到OSS"""
        try:
            # 此时chart_data已经被清理过了，直接使用
            thumb_bytes = generate_thumbnail(
                chart_data,
                self.config.thumbnail_width,
                self.config.thumbnail_height,
                self.config.thumbnail_format,
            )
            if thumb_bytes:
                thumb_filename = (
                    f"{request_data['file_name']}_thumb.{self.config.thumbnail_format}"
                )
                thumb_oss_key = self._build_chart_oss_key(
                    request_data["project_id"],
                    thumb_filename,
                    request_data.get("analysis_node"),
                    request_data.get("contrast"),
                    request_data.get("sample_id"),
                    request_data.get("task_hash"),
                )
                bucket = self._get_oss_bucket(request_data["project_id"])
                content_type = f"image/{self.config.thumbnail_format}"

                self._put_object_with_retry(
                    bucket,
                    thumb_oss_key,
                    thumb_bytes,
                    headers={"Content-Type": content_type},
                )
                request_data["img_url"] = thumb_oss_key
                logger.info(f"缩略图已生成: {thumb_oss_key}")
        except Exception:
            pass  # 缩略图失败不影响正常上传

    def _set_cytoscape_thumbnail(self, request_data: dict[str, Any]) -> None:
        """为Cytoscape网络图设置预定义缩略图"""
        try:
            # 使用固定的网络图缩略图路径
            oss_key = "biochart/resource/network.thumbnail.800.webp"

            # 直接使用OSS key，不添加域名前缀
            request_data["img_url"] = oss_key
            logger.info(f"Cytoscape缩略图已设置: {oss_key}")
        except Exception:
            pass  # 缩略图失败不影响正常上传
