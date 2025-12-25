"""OSS操作基类

提取图表服务和存储服务的共同OSS操作逻辑
"""

import logging
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from requests import Session

    from .config import Config

import oss2

from .network import network_retry
from .utils import handle_api_response

logger = logging.getLogger("lims2.oss_base")


class OSSMixin:
    """OSS操作混入类

    提供STS临时凭证获取和OSS Bucket创建的通用功能
    """

    # 类型声明：这些属性由子类提供
    config: "Config"
    session: "Session"

    def __init_oss__(self):
        """初始化OSS混入功能"""
        # STS 凭证缓存，避免频繁请求
        self._sts_cache = {}
        self._max_cache_size = 50  # 最大缓存条目数，防止内存泄漏

    def _get_oss_path_prefix(self) -> str:
        """根据API URL判断环境并返回相应的OSS路径前缀

        Returns:
            str: 环境相关的路径前缀
                - 生产环境 (api-v2): "media"
                - 预发布环境 (gray): "gray"
                - 测试环境 (其他): "test"
        """
        # 检查API URL是否包含"api-v2"
        if "api-v2" in self.config.api_url:
            return "media"
        elif "gray" in self.config.api_url:
            return "gray"

        return "test"

    @network_retry(max_retries=3, base_delay=1.0, max_delay=60.0)
    def _get_sts_token(self, project_id: str) -> dict[str, Any]:
        """获取阿里云 STS 临时访问凭证

        Args:
            project_id: 项目 ID

        Returns:
            dict[str, Any]: STS 凭证信息，包含：
                - access_key_id: 临时访问密钥 ID
                - access_key_secret: 临时访问密钥
                - security_token: 安全令牌
                - endpoint: OSS 服务端点
                - bucket_name: OSS 存储桶名称

        Raises:
            APIError: 获取 STS 凭证失败

        Note:
            - 使用带时间戳的内存缓存避免频繁请求
            - 缓存键格式：project_id:team_id
            - STS 凭证有时效性，默认15分钟，缓存10分钟后自动刷新
            - 批量上传时能显著减少API请求次数
        """
        cache_key = f"{project_id}:{self.config.team_id}"

        # 检查缓存是否有效（包含时间检查）
        if cache_key in self._sts_cache:
            cached_data = self._sts_cache[cache_key]
            # STS凭证默认有效期15分钟，提前5分钟刷新
            if time.time() - cached_data["cache_time"] < 10 * 60:  # 10分钟内有效
                return {k: v for k, v in cached_data.items() if k != "cache_time"}

        # 尝试从 STS Agent 获取（如果配置了）
        if self.config.sts_agent_url:
            try:
                token_data = self._fetch_sts_from_agent(project_id)
                logger.debug("成功从 STS Agent 获取凭证")
                return self._cache_and_return_token(cache_key, token_data)
            except Exception as e:
                logger.warning(f"从 STS Agent 获取凭证失败: {e}，回退到主 API")

        # 从主 API 获取（默认方式或回退）
        token_data = self._fetch_sts_from_main_api(project_id)
        logger.debug("从主 API 获取凭证")
        return self._cache_and_return_token(cache_key, token_data)

    def _parse_sts_response(self, result: dict) -> dict[str, Any]:
        """解析 STS API 响应，提取凭证信息

        Args:
            result: API 响应结果

        Returns:
            dict[str, Any]: 标准化的凭证信息，包含 cache_time
        """
        raw_data = result.get("record", result)
        return {
            "access_key_id": raw_data.get("AccessKeyId"),
            "access_key_secret": raw_data.get("AccessKeySecret"),
            "security_token": raw_data.get("SecurityToken"),
            "endpoint": self.config.oss_endpoint,
            "bucket_name": self.config.oss_bucket_name,
            "cache_time": time.time(),
        }

    def _fetch_sts_from_agent(self, project_id: str) -> dict[str, Any]:
        """从 STS Agent 服务获取凭证

        Args:
            project_id: 项目 ID

        Returns:
            dict[str, Any]: 凭证信息

        Raises:
            Exception: 请求失败时抛出异常
        """
        assert self.config.sts_agent_url is not None  # 调用前已检查
        params = {"team_id": self.config.team_id} if self.config.team_id else {}
        response = self.session.get(
            self.config.sts_agent_url,
            params=params,
            timeout=self.config.timeout,
        )
        result = handle_api_response(response, "从STS Agent获取凭证")
        return self._parse_sts_response(result)

    def _fetch_sts_from_main_api(self, project_id: str) -> dict[str, Any]:
        """从主 API 获取 STS 凭证

        Args:
            project_id: 项目 ID

        Returns:
            dict[str, Any]: 凭证信息

        Raises:
            APIError: 请求失败时抛出异常
        """
        params = {"team_id": self.config.team_id} if self.config.team_id else {}
        response = self.session.get(
            f"{self.config.api_url}/get_data/aliyun_sts/",
            params=params,
            timeout=self.config.timeout,
        )
        result = handle_api_response(response, "从主API获取STS凭证")
        return self._parse_sts_response(result)

    def _cache_and_return_token(
        self, cache_key: str, token_data: dict[str, Any]
    ) -> dict[str, Any]:
        """缓存凭证并返回（去除时间戳）

        Args:
            cache_key: 缓存键
            token_data: 包含 cache_time 的凭证数据

        Returns:
            dict[str, Any]: 去除 cache_time 的凭证数据
        """
        self._sts_cache[cache_key] = token_data
        self._cleanup_cache()
        return {k: v for k, v in token_data.items() if k != "cache_time"}

    def _cleanup_cache(self) -> None:
        """清理过期的STS缓存条目，防止内存泄漏"""
        current_time = time.time()
        expired_keys = []

        # 找出所有过期的缓存键（超过10分钟）
        for key, data in self._sts_cache.items():
            if current_time - data.get("cache_time", 0) > 10 * 60:
                expired_keys.append(key)

        # 删除过期缓存
        for key in expired_keys:
            self._sts_cache.pop(key, None)

        # 如果缓存仍然过大，删除最旧的条目
        if len(self._sts_cache) > self._max_cache_size:
            # 按缓存时间排序，删除最旧的条目
            sorted_items = sorted(
                self._sts_cache.items(), key=lambda x: x[1].get("cache_time", 0)
            )

            num_to_remove = len(self._sts_cache) - self._max_cache_size
            for key, _ in sorted_items[:num_to_remove]:
                self._sts_cache.pop(key, None)

    def _get_oss_bucket(self, project_id: str) -> oss2.Bucket:
        """获取配置了 STS 认证的 OSS Bucket 对象

        Args:
            project_id: 项目 ID，用于获取对应的 STS 凭证

        Returns:
            oss2.Bucket: 配置了临时凭证的 Bucket 实例

        Raises:
            APIError: STS 凭证获取失败
        """
        sts_info = self._get_sts_token(project_id)
        auth = oss2.StsAuth(
            sts_info["access_key_id"],
            sts_info["access_key_secret"],
            sts_info["security_token"],
        )

        endpoint = sts_info["endpoint"]
        bucket_name = sts_info["bucket_name"]

        # 使用标准的oss2.Bucket
        return oss2.Bucket(auth, endpoint, bucket_name)

    @network_retry(max_retries=5, base_delay=3.0, max_delay=60.0)
    def _put_object_with_retry(
        self, bucket: oss2.Bucket, oss_key: str, data, headers=None
    ) -> oss2.models.PutObjectResult:
        """带重试的OSS对象上传

        Args:
            bucket: OSS Bucket 对象
            oss_key: OSS 文件键名
            data: 上传的数据
            headers: HTTP 头信息

        Returns:
            oss2.models.PutObjectResult: 上传结果
        """
        return bucket.put_object(oss_key, data, headers=headers or {})

    def _get_object_meta_with_retry(self, bucket, oss_key):
        """OSS对象元数据获取

        注意：不使用重试装饰器，因为404是正常的业务逻辑
        """
        return bucket.get_object_meta(oss_key)

    @network_retry(max_retries=3, base_delay=1.0, max_delay=60.0)
    def _get_object_to_file_with_retry(
        self, bucket, oss_key, file_path, progress_callback=None
    ):
        """带重试的OSS对象下载"""
        return bucket.get_object_to_file(
            oss_key, file_path, progress_callback=progress_callback
        )

    def _object_exists_with_retry(self, bucket, oss_key):
        """OSS对象存在性检查

        注意：文件不存在是正常的业务逻辑，不应该重试
        """
        try:
            return bucket.object_exists(oss_key)
        except Exception:
            # 任何异常都认为文件不存在
            return False

    def _check_file_exists_and_same_size(
        self, bucket, oss_key, local_size: int
    ) -> bool:
        """检查OSS文件是否存在且大小相同

        Args:
            bucket: OSS bucket对象
            oss_key: OSS文件键名
            local_size: 本地文件大小

        Returns:
            bool: 文件存在且大小相同返回True
        """
        try:
            if not self._object_exists_with_retry(bucket, oss_key):
                return False

            # 获取远程文件元数据
            meta = self._get_object_meta_with_retry(bucket, oss_key)
            remote_size = int(meta.headers.get("Content-Length", 0))

            # 比较文件大小
            return remote_size == local_size
        except Exception:
            # 如果检查失败，为了安全起见，认为文件不存在
            return False
