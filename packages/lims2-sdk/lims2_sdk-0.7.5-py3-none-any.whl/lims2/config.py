"""配置管理模块"""

import logging
import os
from typing import Optional

logger = logging.getLogger("lims2.config")


class Config:
    """配置管理类"""

    # 类型声明
    api_url: str
    token: Optional[str]
    team_id: str
    sts_agent_url: Optional[str]
    timeout: int
    connection_timeout: int
    read_timeout: int
    oss_endpoint: str
    oss_bucket_name: str

    def __init__(self, api_url: Optional[str] = None, token: Optional[str] = None):
        """初始化配置

        Args:
            api_url: API 地址，如果不提供则从环境变量读取
            token: API Token，如果不提供则从环境变量读取
        """
        # API URL配置和来源跟踪
        if api_url is not None:
            self.api_url = api_url
            self._api_url_source = "参数"
        elif env_url := os.environ.get("LIMS2_API_URL"):
            self.api_url = env_url
            self._api_url_source = "环境变量"
        else:
            self.api_url = "https://api-v1.lims2.com"
            self._api_url_source = "默认值"

        # 输出配置信息
        logger.info(f"API地址: {self.api_url} (来源: {self._api_url_source})")

        self.token = token or os.environ.get("LIMS2_API_TOKEN")
        self.team_id = (
            os.environ.get("LIMS2_TEAM_ID") or "be4e0714c336d2b4bfe00718310d01d5"
        )

        # 网络配置
        self.timeout = int(os.environ.get("LIMS2_TIMEOUT", "600"))  # 默认10分钟
        self.connection_timeout = int(
            os.environ.get("LIMS2_CONNECTION_TIMEOUT", "30")
        )  # 连接超时
        self.read_timeout = int(os.environ.get("LIMS2_READ_TIMEOUT", "300"))  # 读取超时

        # OSS配置
        self.oss_endpoint = (
            os.environ.get("LIMS2_OSS_ENDPOINT")
            or "https://oss-cn-shanghai.aliyuncs.com"
        )
        self.oss_bucket_name = os.environ.get("LIMS2_OSS_BUCKET_NAME") or "protree"

        # 临时目录配置
        self.custom_temp_dir = os.environ.get("LIMS2_TEMP_DIR")  # 自定义临时目录

        # STS Agent 配置
        self.sts_agent_url = os.environ.get("LIMS2_STS_AGENT_URL")
        if self.sts_agent_url:
            logger.info(f"STS Agent 地址: {self.sts_agent_url} (来源: 环境变量)")

        # 缩略图配置
        self.auto_generate_thumbnail = self._get_bool_env(
            "LIMS2_AUTO_GENERATE_THUMBNAIL", True
        )
        self.thumbnail_width = int(os.environ.get("LIMS2_THUMBNAIL_WIDTH", "800"))
        self.thumbnail_height = int(os.environ.get("LIMS2_THUMBNAIL_HEIGHT", "600"))
        self.thumbnail_format = os.environ.get("LIMS2_THUMBNAIL_FORMAT", "png")

    def validate(self) -> None:
        """验证配置是否完整"""
        if not self.api_url:
            raise ValueError("API URL 未配置，请设置环境变量 LIMS2_API_URL")
        if not self.token:
            raise ValueError("API Token 未配置，请设置环境变量 LIMS2_API_TOKEN")

    def get_headers(self) -> dict[str, str]:
        """获取 API 请求头"""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    def _get_bool_env(self, key: str, default: bool) -> bool:
        """从环境变量获取布尔值"""
        value = os.environ.get(key)
        if value is None:
            return default
        return value.lower() in ("true", "1", "yes", "on")
