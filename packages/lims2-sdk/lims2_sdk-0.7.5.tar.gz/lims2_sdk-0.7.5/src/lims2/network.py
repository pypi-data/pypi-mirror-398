"""网络模块 - 提供智能重试和限速处理

支持网络错误重试和 HTTP 429 限速错误的智能处理
"""

import logging
from functools import wraps
from typing import Callable, Optional

import requests
from tenacity import (
    RetryCallState,
    after_log,
    before_sleep_log,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
    wait_exponential_jitter,
)

from .exceptions import APIError

logger = logging.getLogger(__name__)


def is_retryable_error(exception) -> bool:
    """判断是否为可重试的错误

    包括：
    1. 网络连接错误
    2. 超时错误
    3. HTTP 429 限速错误
    4. HTTP 5xx 服务器错误
    """
    # 网络错误
    network_errors = (
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        requests.exceptions.ReadTimeout,
        requests.exceptions.ConnectTimeout,
        requests.exceptions.SSLError,
        OSError,
    )

    # OSS 错误
    try:
        import oss2.exceptions

        if isinstance(
            exception, (oss2.exceptions.ServerError, oss2.exceptions.RequestError)
        ):
            return True
    except ImportError:
        pass

    # 检查是否为网络错误
    if isinstance(exception, network_errors):
        return True

    # 检查 API 错误
    if isinstance(exception, APIError):
        # 429 限速错误 - 总是重试
        if exception.status_code == 429:
            return True
        # 5xx 服务器错误 - 通常可重试
        if exception.status_code and 500 <= exception.status_code < 600:
            return True

    return False


def get_retry_after(exception) -> Optional[float]:
    """从异常中提取重试延迟时间

    简单实用策略：
    1. 检查 Retry-After 头（如果有）
    2. 否则使用固定的2秒延迟
    """
    if not isinstance(exception, APIError) or exception.status_code != 429:
        return None

    # 尝试从响应头获取（如果服务器支持标准）
    if hasattr(exception, "response") and exception.response:
        retry_after = exception.response.headers.get("Retry-After")
        if retry_after:
            try:
                return float(retry_after)
            except (ValueError, TypeError):
                pass  # 忽略解析错误

    # 简单策略：对所有 429 错误使用固定2秒延迟
    # 2秒是一个合理的默认值：
    # - 不会太短导致立即重试
    # - 不会太长影响用户体验
    return 2.0


def custom_wait_strategy(retry_state: RetryCallState) -> float:
    """自定义等待策略

    对于 429 错误，使用服务器建议的等待时间
    对于其他错误，使用指数退避策略
    """
    if retry_state.outcome and retry_state.outcome.failed:
        exception = retry_state.outcome.exception()
        retry_after = get_retry_after(exception)
        if retry_after:
            logger.debug(f"HTTP 429 限速错误，等待 {retry_after} 秒后重试")
            return retry_after

    # 默认使用指数退避
    attempt = retry_state.attempt_number
    return min(2 ** (attempt - 1), 60)  # 1, 2, 4, 8, 16, 32, 60


def network_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0,
    jitter: bool = True,
    handle_rate_limit: bool = True,
) -> Callable:
    """增强的网络重试装饰器

    支持：
    1. 网络错误的指数退避重试
    2. HTTP 429 限速错误的智能重试
    3. HTTP 5xx 服务器错误的重试

    Args:
        max_retries: 最大重试次数
        base_delay: 基础延迟时间（秒）
        max_delay: 最大延迟时间（秒）
        backoff_factor: 退避因子
        jitter: 是否添加抖动
        handle_rate_limit: 是否处理限速错误

    Returns:
        装饰器函数
    """
    # 配置等待策略
    if handle_rate_limit:
        # 使用自定义策略处理429错误
        wait_strategy = custom_wait_strategy
    elif jitter:
        # 使用指数退避加抖动
        wait_strategy = wait_exponential_jitter(
            initial=base_delay, max=max_delay, jitter=base_delay
        )
    else:
        # 仅使用指数退避
        wait_strategy = wait_exponential(
            multiplier=base_delay, max=max_delay, exp_base=backoff_factor
        )

    def decorator(func):
        @wraps(func)
        @retry(
            retry=retry_if_exception(is_retryable_error),
            stop=stop_after_attempt(max_retries + 1),  # +1 包含首次尝试
            wait=wait_strategy,
            before_sleep=before_sleep_log(logger, logging.DEBUG),
            after=after_log(logger, logging.DEBUG),
            reraise=True,
        )
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        # 保存原始函数引用，方便测试
        wrapper.__wrapped__ = func
        return wrapper

    return decorator
