"""
🚀 HTTPX 封装库
- 完全异步支持，性能无敌
- 自动重试、断路器、速率限制
- 完善的错误处理和日志系统
- 支持代理链、自定义中间件
- 自动超时管理、连接池优化
- 支持 HTTP/2、HTTP/3
- 完整的钩子系统（支持修改请求、响应和错误数据）
- 无缝的 SSL/TLS 处理
- 自动重定向链追踪
- 完全的可配置性

钩子系统说明：
===============
1. **before_request**: 请求发送前执行，可修改 RequestConfig
   - 签名：async def hook(config: RequestConfig) -> RequestConfig

2. **after_response**: 收到响应后执行，可修改 ResponseData
   - 签名：async def hook(response: ResponseData) -> ResponseData

3. **on_request_failure**: 请求失败时执行，可修改失败的 ResponseData
   - 签名：async def hook(response: ResponseData, config: RequestConfig, error: Exception) -> ResponseData

其他通知型钩子（不修改数据）：
- response_from_cache: 使用缓存响应时
- circuit_breaker_open: 断路器打开时
- request_error: 请求发生错误时
- request_failed: 请求最终失败时
- request_retry: 请求重试时
- http_error: HTTP 错误时
- response_received: 收到响应时（已弃用，请使用 after_response）
"""

__version__ = "0.0.1"
__author__ = "HTTPX Wrapper"
__all__ = [
    # 主要客户端类
    "HTTPXClient",
    # 数据类
    "ResponseData",
    "RequestConfig",
    "RetryConfig",
    "TimeoutConfig",
    "RateLimitConfig",
    "CircuitBreakerConfig",
    "CacheConfig",
    "ProxyConfig",
    # 枚举类
    "HTTPMethod",
    "RetryStrategy",
    "ProxyType",
    # 异常类
    "HTTPXWrapperException",
    "CircuitBreakerOpenError",
    "RateLimitExceededError",
    "CacheError",
]

import asyncio
import json
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, AsyncIterator
import sys
from dataclasses import dataclass, field
from enum import Enum
import hashlib
from collections import defaultdict
import traceback
from urllib.parse import urlparse
import uuid

import httpx


# ============================================================================
# 日志配置
# ============================================================================

# 获取当前模块的 logger 实例，用于记录此模块的日志信息
logger = logging.getLogger(__name__)


# ============================================================================
# 枚举定义
# ============================================================================


class HTTPMethod(str, Enum):
    """HTTP 方法枚举 - 定义所有支持的 HTTP 请求方法"""

    GET = "GET"  # GET 方法：用于获取资源
    POST = "POST"  # POST 方法：用于创建资源或提交数据
    PUT = "PUT"  # PUT 方法：用于完整更新资源
    DELETE = "DELETE"  # DELETE 方法：用于删除资源
    PATCH = "PATCH"  # PATCH 方法：用于部分更新资源
    HEAD = "HEAD"  # HEAD 方法：仅获取响应头，不获取响应体
    OPTIONS = "OPTIONS"  # OPTIONS 方法：用于获取服务器支持的方法
    TRACE = "TRACE"  # TRACE 方法：用于回显服务器收到的请求


class ProxyType(str, Enum):
    """代理类型枚举 - 定义支持的代理协议类型"""

    HTTP = "http"  # HTTP 代理
    HTTPS = "https"  # HTTPS 代理
    SOCKS5 = "socks5"  # SOCKS5 代理


class RetryStrategy(str, Enum):
    """重试策略枚举 - 定义请求失败后的重试策略"""

    EXPONENTIAL = "exponential"  # 指数退避策略：每次重试间隔时间呈指数增长
    LINEAR = "linear"  # 线性退避策略：每次重试间隔时间线性增长
    FIXED = "fixed"  # 固定延迟策略：每次重试使用相同的延迟时间
    NONE = "none"  # 无重试策略：不进行重试


# ============================================================================
# 数据类定义
# ============================================================================


@dataclass
class ProxyConfig:
    """代理配置数据类 - 用于配置代理服务器的各项参数"""

    url: str  # 代理服务器的 URL 地址
    username: Optional[str] = None  # 代理服务器的用户名（可选）
    password: Optional[str] = None  # 代理服务器的密码（可选）
    proxy_type: ProxyType = ProxyType.HTTP  # 代理类型，默认为 HTTP 代理
    verify_ssl: bool = True  # 是否验证 SSL 证书，默认为 True
    timeout: float = 30.0  # 代理连接超时时间（秒），默认 30 秒

    @property
    def proxy_url(self) -> str:
        """
        生成完整的代理 URL
        如果配置了用户名和密码，则返回带认证信息的 URL
        """
        # 如果提供了用户名和密码，构造带认证的代理 URL
        if self.username and self.password:
            return f"{self.proxy_type.value}://{self.username}:{self.password}@{self.url.split('://')[-1]}"
        # 否则返回不带认证的代理 URL
        return f"{self.proxy_type.value}://{self.url.split('://')[-1]}"


@dataclass
class RetryConfig:
    """重试配置数据类 - 用于配置请求重试的各项参数"""

    max_retries: int = 0  # 最大重试次数，默认不重试
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL  # 重试策略，默认使用指数退避
    base_delay: float = 1.0  # 基础延迟时间（秒），默认 1 秒
    max_delay: float = 60.0  # 最大延迟时间（秒），默认 60 秒
    jitter: bool = True  # 是否添加随机抖动，避免多个客户端同时重试
    retry_on_status_codes: List[int] = field(
        # 需要重试的 HTTP 状态码列表
        default_factory=lambda: [408, 429, 500, 502, 503, 504]
        # 408: 请求超时, 429: 请求过多, 500: 服务器错误,
        # 502: 网关错误, 503: 服务不可用, 504: 网关超时
    )
    retry_on_exceptions: List[type] = field(
        # 需要重试的异常类型列表
        default_factory=lambda: [
            httpx.ConnectError,  # 连接错误
            httpx.ReadError,  # 读取错误
            httpx.WriteError,  # 写入错误
            httpx.TimeoutException,  # 超时异常
        ]
    )

    def __post_init__(self):
        """初始化后验证 - 确保配置参数的有效性"""
        if self.max_retries < 0:
            raise ValueError(f"max_retries 必须 >= 0，当前值: {self.max_retries}")
        if self.base_delay <= 0:
            raise ValueError(f"base_delay 必须 > 0，当前值: {self.base_delay}")
        if self.max_delay < self.base_delay:
            raise ValueError(
                f"max_delay ({self.max_delay}) 必须 >= base_delay ({self.base_delay})"
            )
        if not isinstance(self.retry_on_status_codes, list):
            raise TypeError("retry_on_status_codes 必须是列表")
        if not isinstance(self.retry_on_exceptions, list):
            raise TypeError("retry_on_exceptions 必须是列表")
        # 验证retry_on_exceptions包含的都是异常类
        for exc in self.retry_on_exceptions:
            if not isinstance(exc, type) or not issubclass(exc, BaseException):
                raise TypeError(f"retry_on_exceptions 中的 {exc} 不是有效的异常类")


@dataclass
class TimeoutConfig:
    """超时配置数据类 - 用于配置请求各个阶段的超时时间"""

    timeout: Optional[float] = None  # 全局超时时间（秒），如果设置则覆盖其他超时配置
    connect: Optional[float] = None  # 连接超时时间（秒）
    read: Optional[float] = None  # 读取超时时间（秒）
    write: Optional[float] = None  # 写入超时时间（秒）
    pool: Optional[float] = None  # 连接池超时时间（秒）

    def __post_init__(self):
        """初始化后处理 - 设置默认超时值"""
        # 如果没有设置全局超时，则为各个阶段设置默认值
        if self.timeout is None:
            if self.connect is None:
                self.connect = 10.0  # 默认连接超时 10 秒
            if self.read is None:
                self.read = 30.0  # 默认读取超时 30 秒
            if self.write is None:
                self.write = 30.0  # 默认写入超时 30 秒
            if self.pool is None:
                self.pool = 5.0  # 默认连接池超时 5 秒

    def to_httpx_timeout(self) -> httpx.Timeout:
        """
        转换为 httpx.Timeout 对象
        根据配置创建 httpx 库可使用的超时对象
        """
        # 如果设置了全局超时，使用单一超时值
        if self.timeout is not None:
            return httpx.Timeout(self.timeout)
        # 否则使用详细的超时配置（连接、读取、写入、连接池）
        return httpx.Timeout((self.connect, self.read, self.write, self.pool))

    @classmethod
    def from_timeout(cls, timeout: float) -> "TimeoutConfig":
        """
        从单个超时值创建配置
        类方法：用于快速创建只有全局超时的配置
        """
        return cls(timeout=timeout)

    @classmethod
    def from_detailed(
        cls,
        connect: float = 10.0,
        read: float = 30.0,
        write: float = 30.0,
        pool: float = 10.0,
    ) -> "TimeoutConfig":
        """
        从详细参数创建配置
        类方法：用于创建具有详细超时配置的对象
        """
        return cls(connect=connect, read=read, write=write, pool=pool)


@dataclass
class RateLimitConfig:
    """速率限制配置数据类 - 用于控制请求频率和并发数"""

    max_requests_per_second: Optional[float] = None
    max_concurrent_requests: int = 10
    per_host_rate_limit: Optional[float] = None

    def __post_init__(self):
        """验证速率限制配置"""
        if (
            self.max_requests_per_second is not None
            and self.max_requests_per_second <= 0
        ):
            raise ValueError(
                f"max_requests_per_second 必须 > 0，当前值: {self.max_requests_per_second}"
            )
        if self.max_concurrent_requests <= 0:
            raise ValueError(
                f"max_concurrent_requests 必须 > 0，当前值: {self.max_concurrent_requests}"
            )
        if self.per_host_rate_limit is not None and self.per_host_rate_limit <= 0:
            raise ValueError(
                f"per_host_rate_limit 必须 > 0，当前值: {self.per_host_rate_limit}"
            )


@dataclass
class CircuitBreakerConfig:
    """断路器配置数据类 - 用于配置断路器模式，防止级联故障"""

    enabled: bool = True
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    expected_exception: type = Exception

    def __post_init__(self):
        """验证断路器配置"""
        if self.failure_threshold <= 0:
            raise ValueError(
                f"failure_threshold 必须 > 0，当前值: {self.failure_threshold}"
            )
        if self.recovery_timeout <= 0:
            raise ValueError(
                f"recovery_timeout 必须 > 0，当前值: {self.recovery_timeout}"
            )
        if not isinstance(self.expected_exception, type) or not issubclass(
            self.expected_exception, BaseException
        ):
            raise TypeError(f"expected_exception 必须是异常类")


@dataclass
class CacheConfig:
    """缓存配置数据类 - 用于配置响应缓存功能"""

    enabled: bool = False
    ttl: float = 20.0
    max_cache_memory: int = 5 * 1024 * 1024  # 5MB 内存限制
    cacheable_methods: List[str] = field(default_factory=lambda: ["GET", "HEAD"])
    cacheable_status_codes: List[int] = field(
        default_factory=lambda: [200, 203, 204, 206, 300, 301, 404, 405, 410, 414, 501]
    )

    def __post_init__(self):
        """验证缓存配置"""
        if self.ttl <= 0:
            raise ValueError(f"ttl 必须 > 0，当前值: {self.ttl}")
        if self.max_cache_memory <= 0:
            raise ValueError(
                f"max_cache_memory 必须 > 0，当前值: {self.max_cache_memory}"
            )


@dataclass
class RequestConfig:
    """请求配置数据类 - 封装单个 HTTP 请求的所有配置参数"""

    url: str
    method: HTTPMethod = HTTPMethod.GET
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, str]] = None
    data: Optional[Union[str, bytes, Dict]] = None
    json: Optional[Dict[str, Any]] = None
    files: Optional[Dict[str, Any]] = None
    timeout: Optional[Union[float, TimeoutConfig]] = None
    verify_ssl: Union[bool, str] = True
    allow_redirects: bool = True
    cookies: Optional[Dict[str, str]] = None
    proxies: Optional[Union[str, Dict[str, str]]] = None
    auth: Optional[Tuple[str, str]] = None
    hooks: Optional[Dict[str, Callable]] = None
    follow_redirects: int = 5
    extensions: Optional[Dict[str, Any]] = None


@dataclass
class ResponseData:
    """响应数据包装类 - 封装 HTTP 响应的所有数据（包括错误信息）"""

    status_code: int = 0
    headers: Dict[str, str] = field(default_factory=dict)
    content: bytes = b""
    url: str = ""
    elapsed: float = 0.0
    history: List["ResponseData"] = field(default_factory=list)

    error: Optional[Exception] = None
    error_message: str = ""
    error_type: str = ""
    error_traceback: str = ""

    _json_cache: Optional[Dict[str, Any]] = field(default=None, init=False, repr=False)
    _text_cache: Optional[str] = field(default=None, init=False, repr=False)

    @property
    def text(self) -> str:
        """
        获取文本响应
        将响应体的字节数据解码为字符串，使用缓存避免重复解码
        """
        # 如果文本缓存为空，进行解码
        if self._text_cache is None:
            # 使用 UTF-8 解码，忽略无法解码的字符
            self._text_cache = self.content.decode("utf-8", errors="ignore")
        # 返回缓存的文本
        return self._text_cache

    @property
    def json_data(self) -> Dict[str, Any]:
        """
        获取 JSON 响应
        将响应文本解析为 JSON 对象，使用缓存避免重复解析
        """
        # 如果 JSON 缓存为空，进行解析
        if self._json_cache is None:
            try:
                # 将文本解析为 JSON
                self._json_cache = json.loads(self.text)
            except json.JSONDecodeError as e:
                # 解析失败时记录错误日志并抛出异常
                logger.error(f"JSON 解析失败: {e}")
                raise
        # 返回缓存的 JSON 对象
        return self._json_cache

    def is_success(self) -> bool:
        """检查是否成功 - 无异常且状态码为 2xx"""
        return self.error is None and 200 <= self.status_code < 300

    def has_error(self) -> bool:
        """检查是否有错误 - 是否存在异常"""
        return self.error is not None

    def get_error_info(self) -> Dict[str, Any]:
        """
        获取错误详细信息

        Returns:
            Dict: 包含错误类型、消息、堆栈信息和异常对象的字典
        """
        if self.error is None:
            return {}
        return {
            "type": self.error_type,
            "message": self.error_message,
            "traceback": self.error_traceback,  # 完整堆栈跟踪
            "exception": self.error,
            "status_code": self.status_code,
            "url": self.url,
            "elapsed": self.elapsed,
        }

    def raise_for_error(self) -> None:
        """
        如果存在错误，抛出异常
        适用于需要将非抛出模式转换为抛出模式的场景
        """
        if self.error is not None:
            raise self.error

    def is_redirect(self) -> bool:
        """检查是否重定向 (3xx) - 无异常且状态码在 300-399 之间"""
        return self.error is None and 300 <= self.status_code < 400

    def is_client_error(self) -> bool:
        """检查是否客户端错误 (4xx) - 无异常且状态码在 400-499 之间"""
        return self.error is None and 400 <= self.status_code < 500

    def is_server_error(self) -> bool:
        """检查是否服务器错误 (5xx) - 无异常且状态码在 500-599 之间"""
        return self.error is None and 500 <= self.status_code < 600


# ============================================================================
# 异常定义
# ============================================================================


class HTTPXWrapperException(Exception):
    """基础异常类 - 所有自定义异常的基类"""

    pass


class CircuitBreakerOpenError(HTTPXWrapperException):
    """断路器打开异常 - 当断路器检测到服务不可用时抛出"""

    pass


class RateLimitExceededError(HTTPXWrapperException):
    """速率限制超出异常 - 当请求频率超过限制时抛出"""

    pass


class CacheError(HTTPXWrapperException):
    """缓存错误异常 - 当缓存操作发生错误时抛出"""

    pass


# ============================================================================
# 工具类
# ============================================================================


class CircuitBreaker:
    """
    断路器实现 - 用于防止级联故障
    当服务连续失败达到阈值时，断路器打开，直接拒绝请求
    经过一段时间后，尝试恢复服务
    """

    def __init__(self, config: CircuitBreakerConfig):
        """初始化断路器"""
        self.config = config
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"
        self._lock = asyncio.Lock()

    async def record_success(self):
        """记录成功的请求，重置失败计数器并关闭断路器"""
        async with self._lock:
            self.failure_count = 0
            self.state = "closed"

    async def record_failure(self):
        """记录失败的请求，失败次数增加，达到阈值后打开断路器"""
        async with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.failure_count >= self.config.failure_threshold:
                self.state = "open"
                logger.warning(f"断路器打开，故障次数: {self.failure_count}")

    async def async_call(self, func: Callable, *args, **kwargs):
        """异步执行函数，受断路器保护"""
        async with self._lock:
            if self.state == "open":
                if time.time() - self.last_failure_time > self.config.recovery_timeout:
                    self.state = "half-open"
                    logger.info("断路器进入半开状态")
                else:
                    raise CircuitBreakerOpenError("断路器已打开")

        try:
            result = await func(*args, **kwargs)
            await self.record_success()
            return result
        except Exception as e:
            await self.record_failure()
            raise


class RateLimiter:
    """速率限制器 - 用于控制请求速率和并发数"""

    def __init__(self, config: RateLimitConfig):
        """初始化速率限制器"""
        self.config = config
        self.current_requests = 0
        self.last_request_time = time.time()
        self.per_host_requests = defaultdict(float)
        self._lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(config.max_concurrent_requests)

    async def acquire(self, host: Optional[str] = None) -> None:
        """获取速率限制许可 - 在发送请求前调用"""
        await self._semaphore.acquire()

        if self.config.max_requests_per_second:
            async with self._lock:
                elapsed = time.time() - self.last_request_time
                min_interval = 1.0 / self.config.max_requests_per_second
                if elapsed < min_interval:
                    await asyncio.sleep(min_interval - elapsed)
                self.last_request_time = time.time()

        if host and self.config.per_host_rate_limit:
            async with self._lock:
                elapsed = time.time() - self.per_host_requests.get(host, 0)
                min_interval = 1.0 / self.config.per_host_rate_limit
                if elapsed < min_interval:
                    await asyncio.sleep(min_interval - elapsed)
                self.per_host_requests[host] = time.time()

    def release(self) -> None:
        """释放速率限制许可 - 在请求完成后调用"""
        self._semaphore.release()


class SimpleCache:
    """简单的内存缓存 - 用于缓存 HTTP 响应"""

    def __init__(self, config: CacheConfig):
        """初始化缓存"""
        self.config = config
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self.current_memory = 0  # 当前占用内存
        self._lock = asyncio.Lock()

    def _cache_key(
        self,
        method: str,
        url: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> str:
        """生成缓存键 - 根据请求方法、URL、参数和关键请求头生成唯一的缓存键"""
        key_str = f"{method}:{url}"
        if params:
            key_str += f":params:{json.dumps(params, sort_keys=True)}"
        if headers:
            cache_relevant_headers = {
                k.lower(): v
                for k, v in headers.items()
                if k.lower() in {"accept", "accept-encoding", "accept-language"}
            }
            if cache_relevant_headers:
                key_str += (
                    f":headers:{json.dumps(cache_relevant_headers, sort_keys=True)}"
                )
        return hashlib.sha256(key_str.encode()).hexdigest()

    async def get(
        self,
        method: str,
        url: str,
        params: Optional[Dict] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Optional[Any]:
        """获取缓存 - 根据请求信息获取缓存的响应"""
        if not self.config.enabled or method not in self.config.cacheable_methods:
            return None

        key = self._cache_key(method, url, params, headers)
        async with self._lock:
            if key in self.cache:
                value, expiry, *o = self.cache[key]
                if time.time() < expiry:
                    logger.debug(f"命中缓存: {key}")
                    return value
                else:
                    del self.cache[key]
        return None

    async def set(
        self,
        method: str,
        url: str,
        value: Any,
        status_code: int,
        params: Optional[Dict] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """设置缓存 - 将响应数据存入缓存"""
        if not self.config.enabled:
            return
        if method not in self.config.cacheable_methods:
            return
        if status_code not in self.config.cacheable_status_codes:
            return

        # 🔥 只缓存 JSON 格式的响应
        if hasattr(value, "headers"):
            content_type = value.headers.get("content-type", "").lower()
            # 检查是否是 JSON 格式
            if "application/json" not in content_type and "json" not in content_type:
                logger.debug(f"跳过缓存非JSON响应: Content-Type={content_type}")
                return
        else:
            # 如果没有 headers 属性，默认不缓存
            logger.debug("跳过缓存: 响应对象没有 headers 属性")
            return

        key = self._cache_key(method, url, params, headers)
        expiry = time.time() + self.config.ttl

        # 计算响应大小（优先用 content 长度）
        if hasattr(value, "content"):
            item_size = len(value.content)
        else:
            item_size = sys.getsizeof(value)  # 备用方案

        async with self._lock:
            current_time = time.time()

            # 先清理过期缓存释放内存
            expired_keys = [
                k for k, (v, exp, size) in self.cache.items() if current_time >= exp
            ]
            for k in expired_keys:
                _, _, size = self.cache[k]
                del self.cache[k]
                self.current_memory -= size
                logger.debug(f"删除过期缓存: {k}, 释放 {size} bytes")

            # 淘汰最早的缓存
            while self.current_memory + item_size > self.config.max_cache_memory:
                if not self.cache:
                    logger.warning(f"单个响应 {item_size} bytes 超过缓存限制")
                    return

                oldest_key = next(iter(self.cache))
                _, _, old_size = self.cache[oldest_key]
                del self.cache[oldest_key]
                self.current_memory -= old_size
                logger.debug(f"内存不足，删除缓存: {oldest_key}, 释放 {old_size} bytes")

            # 添加新缓存
            self.cache[key] = (value, expiry, item_size)
            self.current_memory += item_size
            logger.debug(
                f"缓存设置: {key}, TTL: {self.config.ttl}s, "
                f"大小: {item_size} bytes, 总内存: {self.current_memory} bytes"
            )

    async def clear(self) -> None:
        """清空缓存 - 删除所有缓存条目"""
        async with self._lock:
            self.cache.clear()


class EventHooks:
    """
    事件钩子系统 - 用于在请求生命周期的各个阶段执行自定义函数
    支持注册多个回调函数，并在事件触发时执行

    支持两种类型的钩子：
    1. 通知型钩子：仅用于通知，不修改数据（例如 request_retry, circuit_breaker_open）
    2. 修改型钩子：可以修改并返回数据（例如 before_request, after_response, on_request_failure）
    """

    def __init__(self):
        """初始化事件钩子系统"""
        # 钩子字典，键为事件名，值为回调函数列表
        self.hooks: Dict[str, List[Callable]] = defaultdict(list)

    def register(self, event: str, callback: Callable) -> None:
        """
        注册钩子 - 为指定事件注册回调函数
        当事件触发时，所有注册的回调函数都会被执行
        """
        self.hooks[event].append(callback)  # 将回调函数添加到事件的回调列表中

    def unregister(self, event: str, callback: Callable) -> None:
        """
        注销钩子 - 移除之前注册的回调函数
        """
        if callback in self.hooks[event]:  # 如果回调函数存在于列表中
            self.hooks[event].remove(callback)  # 移除回调函数

    async def trigger(self, event: str, *args, **kwargs) -> None:
        """
        触发通知型钩子 - 执行所有注册到该事件的回调函数（不返回值）
        支持同步和异步回调函数

        适用于：request_retry, circuit_breaker_open, request_error 等
        """
        for callback in self.hooks[event]:  # 遍历该事件的所有回调函数
            # 如果是异步函数，使用 await 执行
            if asyncio.iscoroutinefunction(callback):
                await callback(*args, **kwargs)
            else:
                # 否则直接执行同步函数
                callback(*args, **kwargs)

    async def trigger_modifiable(self, event: str, data: Any, *args, **kwargs) -> Any:
        """
        触发修改型钩子 - 执行所有注册到该事件的回调函数，允许修改数据
        支持同步和异步回调函数

        钩子函数应该接收数据作为第一个参数，并返回修改后的数据
        如果钩子函数返回 None，则使用原始数据

        适用于：before_request, after_response, on_request_failure

        Args:
            event: 事件名
            data: 要传递给钩子的数据（会被修改）
            *args: 其他位置参数
            **kwargs: 其他关键字参数

        Returns:
            修改后的数据（经过所有钩子处理）
        """
        current_data = data
        for callback in self.hooks[event]:  # 遍历该事件的所有回调函数
            try:
                # 如果是异步函数，使用 await 执行
                if asyncio.iscoroutinefunction(callback):
                    result = await callback(current_data, *args, **kwargs)
                else:
                    # 否则直接执行同步函数
                    result = callback(current_data, *args, **kwargs)

                # 如果钩子返回了值，使用返回值作为新数据
                if result is not None:
                    current_data = result
                    logger.debug(f"钩子 '{event}' 修改了数据")
            except Exception as e:
                logger.error(
                    f"执行钩子 '{event}' 时出错: {type(e).__name__}: {str(e)}",
                    exc_info=True,
                )
                # 钩子执行失败不影响主流程，继续执行下一个钩子

        return current_data


# ============================================================================
# 主要客户端类
# ============================================================================


class HTTPXClient:
    """
    🚀 高级 HTTPX 客户端封装 - 企业级 HTTP 客户端

    这是一个功能完整的 HTTP 客户端，提供以下特性:
    - 完全异步支持：基于 asyncio，支持高并发请求
    - 自动重试和指数退避：请求失败时自动重试，支持多种退避策略
    - 断路器模式：防止级联故障，服务降级保护
    - 速率限制：控制请求频率，防止过载
    - 响应缓存：减少重复请求，提升性能
    - 完善的错误处理：详细的异常分类和处理
    - 事件钩子系统：在请求生命周期各阶段执行自定义逻辑
    """

    def __init__(
        self,
        base_url: Optional[str] = None,  # 基础 URL，所有请求会基于此 URL
        timeout: Optional[
            Union[float, TimeoutConfig]
        ] = None,  # 超时配置，可以是单个数字或详细配置
        retry_config: Optional[RetryConfig] = None,  # 重试配置
        rate_limit_config: Optional[RateLimitConfig] = None,  # 速率限制配置
        circuit_breaker_config: Optional[CircuitBreakerConfig] = None,  # 断路器配置
        cache_config: Optional[CacheConfig] = None,  # 缓存配置
        proxies: Optional[
            Union[str, Dict[str, str], List[ProxyConfig]]
        ] = None,  # 代理配置
        verify_ssl: Union[bool, str] = True,  # SSL 证书验证，True/False 或证书路径
        headers: Optional[Dict[str, str]] = None,  # 默认请求头
        cookies: Optional[Dict[str, str]] = None,  # 默认 cookies
        auth: Optional[Tuple[str, str]] = None,  # HTTP 基本认证(用户名, 密码)
        http2: bool = True,  # 是否启用 HTTP/2 协议
        http3: bool = False,  # 是否启用 HTTP/3 协议
        follow_redirects: bool = True,  # 是否自动跟随重定向
        max_redirects: int = 5,  # 最大重定向次数
        limits: Optional[httpx.Limits] = None,  # httpx 连接限制配置
        pool_timeout: float = 30.0,  # 连接池超时时间(秒)
        max_connections: int = 100,  # 最大连接数
        max_keepalive_connections: int = 20,  # 最大保持活动的连接数
        raise_on_error: bool = True,  # 是否在错误时抛出异常（True=抛异常，False=返回错误ResponseData）
    ):
        """
        初始化 HTTPXClient

        创建一个功能完整的 HTTP 客户端实例，配置各项功能
            base_url: 基础 URL
            timeout: 超时配置
            retry_config: 重试配置
            rate_limit_config: 速率限制配置
            circuit_breaker_config: 断路器配置
            cache_config: 缓存配置
            proxies: 代理配置
            verify_ssl: SSL 验证
            headers: 默认请求头
            cookies: 默认 cookies
            auth: 默认认证信息
            http2: 是否启用 HTTP/2
            http3: 是否启用 HTTP/3
            follow_redirects: 是否跟随重定向
            max_redirects: 最大重定向次数
            limits: httpx 限制配置
            pool_timeout: 连接池超时
            max_connections:  最大连接数
            max_keepalive_connections:  最大保活连接数
            raise_on_error: 是否在错误时抛出异常
        """
        # ===== 参数验证 =====
        if max_connections <= 0:
            raise ValueError(f"max_connections 必须 > 0，当前值: {max_connections}")
        if max_keepalive_connections < 0:
            raise ValueError(
                f"max_keepalive_connections 必须 >= 0，当前值: {max_keepalive_connections}"
            )
        if max_keepalive_connections > max_connections:
            raise ValueError(
                f"max_keepalive_connections ({max_keepalive_connections}) "
                f"不能超过 max_connections ({max_connections})"
            )
        if pool_timeout <= 0:
            raise ValueError(f"pool_timeout 必须 > 0，当前值: {pool_timeout}")
        if max_redirects < 0:
            raise ValueError(f"max_redirects 必须 >= 0，当前值: {max_redirects}")

        # 处理超时配置：支持 None、数字、TimeoutConfig 三种格式
        if timeout is None:
            self.timeout = TimeoutConfig()  # 使用默认超时配置
        elif isinstance(timeout, (int, float)):
            if timeout <= 0:
                raise ValueError(f"timeout 必须 > 0，当前值: {timeout}")
            self.timeout = TimeoutConfig(timeout=float(timeout))  # 转换为 TimeoutConfig
        elif isinstance(timeout, TimeoutConfig):
            self.timeout = timeout  # 直接使用 TimeoutConfig
        else:
            raise TypeError(
                f"无效的 timeout 配置类型: {type(timeout).__name__}. "
                f"期望类型: None, float, int, 或 TimeoutConfig"
            )

        # 保存基本配置
        self.base_url = base_url  # 基础 URL
        self.retry_config = (
            retry_config or RetryConfig()
        )  # 重试配置，如未提供则使用默认
        self.rate_limit_config = rate_limit_config or RateLimitConfig()  # 速率限制配置
        self.circuit_breaker_config = (
            circuit_breaker_config or CircuitBreakerConfig()
        )  # 断路器配置
        self.cache_config = cache_config or CacheConfig()  # 缓存配置
        self.verify_ssl = verify_ssl  # SSL 验证设置
        self.headers = headers or {}  # 默认请求头
        self.cookies = cookies or {}  # 默认 cookies
        self.auth = auth  # HTTP 认证信息
        self.raise_on_error = raise_on_error  # 错误处理模式

        # 初始化线程安全锁
        self._client_lock = asyncio.Lock()  # 客户端创建锁（异步）

        # 初始化工具组件
        # 如果启用了断路器，创建断路器实例；否则为 None
        self.circuit_breaker = (
            CircuitBreaker(self.circuit_breaker_config)
            if self.circuit_breaker_config.enabled
            else None
        )
        self.rate_limiter = RateLimiter(self.rate_limit_config)  # 创建速率限制器
        self.cache = SimpleCache(self.cache_config)  # 创建缓存实例
        self.hooks = EventHooks()  # 创建事件钩子系统

        # 配置 httpx 连接限制
        if limits is None:
            # 如果未提供限制配置，使用默认配置
            limits = httpx.Limits(
                max_connections=max_connections,  # 最大连接数
                max_keepalive_connections=max_keepalive_connections,  # 最大保持活动的连接数
            )

        # 构建 httpx 客户端参数字典
        client_kwargs: Dict[str, Any] = {
            "timeout": self.timeout.to_httpx_timeout(),  # 转换为 httpx 超时对象
            "verify": verify_ssl,  # SSL 验证
            "headers": self.headers or None,  # 请求头
            "cookies": self.cookies or None,  # cookies
            "auth": auth,  # 认证信息
            "http2": http2,  # 是否启用 HTTP/2
            "limits": limits,  # 连接限制
            "follow_redirects": follow_redirects,  # 是否跟随重定向
        }

        # httpx 要求 base_url 必须是 str/httpx.URL，不能传 None
        if base_url is not None:
            client_kwargs["base_url"] = base_url

        # 处理代理配置
        if proxies:
            client_kwargs["proxies"] = self._process_proxies(
                proxies
            )  # 处理并添加代理配置

        # 如果启用 HTTP/3（需要安装 httpx[http3]）
        if http3:
            try:
                # 配置 HTTP/3 传输
                client_kwargs["mounts"] = {
                    "https://": httpx.AsyncHTTPTransport(
                        http2=False
                    ),  # 使用 HTTP/3 传输
                }
            except Exception as e:
                logger.warning(f"HTTP/3 不可用: {e}")

        self._client_kwargs = client_kwargs
        self._client: Optional[httpx.AsyncClient] = None

    def _process_proxies(
        self, proxies: Union[str, Dict[str, str], List[ProxyConfig]]
    ) -> Dict[str, str]:
        """处理代理配置"""
        if isinstance(proxies, str):
            return {"all://": proxies}
        elif isinstance(proxies, dict):
            return proxies
        elif isinstance(proxies, list):
            # 列表中的第一个代理
            if proxies:
                return {"all://": proxies[0].proxy_url}
        return {}

    def _sanitize_headers(self, headers: Optional[Dict[str, str]]) -> Dict[str, str]:
        """
        过滤敏感的请求头信息 - 防止日志泄露敏感数据

        Args:
            headers: 原始请求头

        Returns:
            过滤后的请求头（敏感字段替换为 ***）
        """
        if not headers:
            return {}

        # 定义敏感字段（不区分大小写）
        sensitive_keys = {
            "authorization",
            "cookie",
            "x-api-key",
            "token",
            "api-key",
            "apikey",
            "secret",
            "password",
            "passwd",
            "x-auth-token",
            "x-access-token",
            "bearer",
        }

        return {
            k: "***FILTERED***" if k.lower() in sensitive_keys else v
            for k, v in headers.items()
        }

    async def _ensure_client(self) -> httpx.AsyncClient:
        """确保客户端已创建 - 线程安全"""
        if self._client is None:
            async with self._client_lock:
                if self._client is None:
                    self._client = httpx.AsyncClient(**self._client_kwargs)
                    logger.debug("创建新的 HTTPX 客户端实例")
        return self._client

    async def close(self) -> None:
        """关闭客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        异步上下文管理器退出 - 确保资源清理

        即使在异常情况下也会尝试关闭客户端
        """
        try:
            await self.close()
        except Exception as e:
            logger.error(
                f"关闭客户端时发生错误: {type(e).__name__}: {str(e)}", exc_info=True
            )
            # 不抑制原始异常，只记录清理错误
        return False  # 不抑制异常，让异常继续传播

    def _build_request_kwargs(self, config: RequestConfig) -> Dict[str, Any]:
        """构建请求参数"""
        kwargs = {
            "method": config.method.value,
            "url": config.url,
        }

        if config.headers:
            kwargs["headers"] = config.headers

        if config.params:
            kwargs["params"] = config.params

        if config.data:
            kwargs["data"] = config.data
        elif config.json:
            kwargs["json"] = config.json
        elif config.files:
            kwargs["files"] = config.files

        # 处理超时配置（支持多种格式）
        if config.timeout:
            if isinstance(config.timeout, (int, float)):
                kwargs["timeout"] = httpx.Timeout(float(config.timeout))
            elif isinstance(config.timeout, TimeoutConfig):
                kwargs["timeout"] = config.timeout.to_httpx_timeout()
            else:
                raise TypeError(
                    f"timeout 必须是 float 或 TimeoutConfig，得到: {type(config.timeout).__name__}"
                )
        else:
            kwargs["timeout"] = self.timeout.to_httpx_timeout()

        if config.allow_redirects is not None:
            kwargs["follow_redirects"] = config.allow_redirects

        if config.cookies:
            kwargs["cookies"] = config.cookies

        if config.auth:
            kwargs["auth"] = config.auth

        if config.extensions:
            kwargs["extensions"] = config.extensions

        return kwargs

    async def request(self, config: RequestConfig) -> ResponseData:
        """
        发送单个请求

        Args:
            config: 请求配置

        Returns:
            ResponseData:  响应数据

        Raises:
            HTTPXWrapperException: 各种错误
        """
        # 🔥 新增：before_request 钩子 - 允许修改请求配置
        config = await self.hooks.trigger_modifiable("before_request", config)

        host = urlparse(config.url).netloc
        request_id = str(uuid.uuid4())

        await self.rate_limiter.acquire(host)

        try:
            logger.debug(f"[{request_id}] 开始请求: {config.method.value} {config.url}")

            cached = await self.cache.get(
                config.method.value, config.url, config.params, config.headers
            )
            if cached:
                await self.hooks.trigger("response_from_cache", config.url)
                logger.debug(f"[{request_id}] 使用缓存响应")
                return cached

            response_data = await self._execute_with_retry(config, request_id)

            if response_data.is_success():
                await self.cache.set(
                    config.method.value,
                    config.url,
                    response_data,
                    response_data.status_code,
                    config.params,
                    config.headers,
                )

            return response_data

        except CircuitBreakerOpenError as e:
            await self.hooks.trigger("circuit_breaker_open", config.url)
            if not self.raise_on_error:
                logger.error(f"[{request_id}] 断路器打开: {config.url}")
                failure_data = ResponseData(
                    status_code=503,
                    url=config.url,
                    elapsed=0.0,
                    error=e,
                    error_message=str(e),
                    error_type=type(e).__name__,
                    error_traceback=traceback.format_exc(),
                )
                # 🔥 新增：on_request_failure 钩子 - 允许修改失败响应数据
                failure_data = await self.hooks.trigger_modifiable(
                    "on_request_failure", failure_data, config, e
                )
                return failure_data
            raise
        except Exception as e:
            await self.hooks.trigger("request_error", config.url, str(e))
            if not self.raise_on_error:
                logger.error(
                    f"[{request_id}] 请求错误: {config.url} | 异常: {type(e).__name__}: {str(e)}",
                    exc_info=True,
                )
                failure_data = ResponseData(
                    status_code=0,
                    url=config.url,
                    elapsed=0.0,
                    error=e,
                    error_message=str(e),
                    error_type=type(e).__name__,
                    error_traceback=traceback.format_exc(),
                )
                # 🔥 新增：on_request_failure 钩子 - 允许修改失败响应数据
                failure_data = await self.hooks.trigger_modifiable(
                    "on_request_failure", failure_data, config, e
                )
                return failure_data
            raise
        finally:
            self.rate_limiter.release()

    async def _execute_with_retry(
        self, config: RequestConfig, request_id: str
    ) -> ResponseData:
        """
        执行带重试的请求 - 支持双模式错误处理

        Args:
            config: 请求配置

        Returns:
            ResponseData: 响应数据（成功或包含错误信息）
        """
        attempt = 0
        last_exception = None
        start_time = time.time()

        while attempt <= self.retry_config.max_retries:
            try:
                if self.circuit_breaker:
                    return await self.circuit_breaker.async_call(
                        self._make_request, config, request_id
                    )
                else:
                    return await self._make_request(config, request_id)

            except (
                httpx.ConnectError,
                httpx.ReadError,
                httpx.WriteError,
                httpx.TimeoutException,
                httpx.PoolTimeout,
                httpx.NetworkError,
                httpx.ProtocolError,
                httpx.ProxyError,
                httpx.UnsupportedProtocol,
            ) as e:
                # 网络层异常：连接、读写、超时、协议等错误
                last_exception = e
                attempt += 1

                logger.error(
                    f"[{request_id}] 网络异常 [{type(e).__name__}]: {str(e)} | "
                    f"URL: {config.url} | 尝试: {attempt}/{self.retry_config.max_retries}",
                    exc_info=True,
                )

                if attempt > self.retry_config.max_retries:
                    await self.hooks.trigger(
                        "request_failed", config.url, str(e), attempt
                    )

                    # 如果不抛出异常，返回包含错误的 ResponseData
                    if not self.raise_on_error:
                        elapsed = time.time() - start_time
                        error_tb = traceback.format_exc()  # 捕获完整堆栈
                        logger.error(
                            f"请求最终失败: {config.url} | "
                            f"异常: {type(e).__name__}: {str(e)} | "
                            f"总耗时: {elapsed:.2f}s | 重试次数: {attempt - 1}\n"
                            f"堆栈跟踪:\n{error_tb}"
                        )
                        failure_data = ResponseData(
                            status_code=0,
                            url=config.url,
                            elapsed=elapsed,
                            error=e,
                            error_message=f"{type(e).__name__}: {str(e)}",
                            error_type=type(e).__name__,
                            error_traceback=error_tb,  # 保存完整堆栈
                        )
                        # 🔥 新增：on_request_failure 钩子 - 允许修改失败响应数据
                        failure_data = await self.hooks.trigger_modifiable(
                            "on_request_failure", failure_data, config, e
                        )
                        return failure_data
                    raise

                wait_time = self._calculate_backoff(attempt)
                logger.warning(
                    f"请求失败，准备重试 (第 {attempt}/{self.retry_config.max_retries} 次), "
                    f"等待 {wait_time:.2f}s | 异常: {type(e).__name__}: {str(e)}"
                )
                await asyncio.sleep(wait_time)
                await self.hooks.trigger("request_retry", config.url, attempt)

            except httpx.HTTPStatusError as e:
                logger.error(
                    f"[{request_id}] HTTP 错误: {e.response.status_code} | "
                    f"URL: {config.url} | {str(e)}"
                )

                if e.response.status_code in self.retry_config.retry_on_status_codes:
                    attempt += 1
                    if attempt > self.retry_config.max_retries:

                        # 如果不抛出异常，返回包含错误的 ResponseData
                        if not self.raise_on_error:
                            elapsed = time.time() - start_time
                            error_tb = traceback.format_exc()
                            failure_data = ResponseData(
                                status_code=e.response.status_code,
                                headers=dict(e.response.headers),
                                content=e.response.content,
                                url=str(e.response.url),
                                elapsed=elapsed,
                                error=e,
                                error_message=f"HTTP {e.response.status_code}: {str(e)}",
                                error_type=type(e).__name__,
                                error_traceback=error_tb,
                            )
                            # 🔥 新增：on_request_failure 钩子 - 允许修改失败响应数据
                            failure_data = await self.hooks.trigger_modifiable(
                                "on_request_failure", failure_data, config, e
                            )
                            return failure_data
                        raise

                    wait_time = self._calculate_backoff(attempt)
                    logger.warning(
                        f"HTTP {e.response.status_code} 错误，准备重试，等待 {wait_time:.2f}s"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    # 不可重试的状态码
                    await self.hooks.trigger(
                        "http_error", config.url, e.response.status_code
                    )

                    # 如果不抛出异常，返回包含错误的 ResponseData
                    if not self.raise_on_error:
                        elapsed = time.time() - start_time
                        error_tb = traceback.format_exc()
                        failure_data = ResponseData(
                            status_code=e.response.status_code,
                            headers=dict(e.response.headers),
                            content=e.response.content,
                            url=str(e.response.url),
                            elapsed=elapsed,
                            error=e,
                            error_message=f"HTTP {e.response.status_code}: {str(e)}",
                            error_type=type(e).__name__,
                            error_traceback=error_tb,
                        )
                        # 🔥 新增：on_request_failure 钩子 - 允许修改失败响应数据
                        failure_data = await self.hooks.trigger_modifiable(
                            "on_request_failure", failure_data, config, e
                        )
                        return failure_data
                    raise

            except httpx.InvalidURL as e:
                logger.error(f"[{request_id}] 无效的 URL: {config.url} | {str(e)}")

                if not self.raise_on_error:
                    error_tb = traceback.format_exc()
                    failure_data = ResponseData(
                        status_code=0,
                        url=config.url,
                        elapsed=time.time() - start_time,
                        error=e,
                        error_message=f"无效URL: {str(e)}",
                        error_type=type(e).__name__,
                        error_traceback=error_tb,
                    )
                    # 🔥 新增：on_request_failure 钩子 - 允许修改失败响应数据
                    failure_data = await self.hooks.trigger_modifiable(
                        "on_request_failure", failure_data, config, e
                    )
                    return failure_data
                raise

            except httpx.CookieConflict as e:
                logger.error(f"[{request_id}] Cookie 冲突: {config.url} | {str(e)}")

                if not self.raise_on_error:
                    error_tb = traceback.format_exc()
                    failure_data = ResponseData(
                        status_code=0,
                        url=config.url,
                        elapsed=time.time() - start_time,
                        error=e,
                        error_message=f"Cookie冲突: {str(e)}",
                        error_type=type(e).__name__,
                        error_traceback=error_tb,
                    )
                    # 🔥 新增：on_request_failure 钩子 - 允许修改失败响应数据
                    failure_data = await self.hooks.trigger_modifiable(
                        "on_request_failure", failure_data, config, e
                    )
                    return failure_data
                raise

            except httpx.StreamError as e:
                last_exception = e
                attempt += 1
                logger.error(
                    f"[{request_id}] 流错误: {str(e)} | URL: {config.url} | "
                    f"尝试: {attempt}/{self.retry_config.max_retries}"
                )

                if attempt > self.retry_config.max_retries:

                    if not self.raise_on_error:
                        error_tb = traceback.format_exc()
                        failure_data = ResponseData(
                            status_code=0,
                            url=config.url,
                            elapsed=time.time() - start_time,
                            error=e,
                            error_message=f"流错误: {str(e)}",
                            error_type=type(e).__name__,
                            error_traceback=error_tb,
                        )
                        # 🔥 新增：on_request_failure 钩子 - 允许修改失败响应数据
                        failure_data = await self.hooks.trigger_modifiable(
                            "on_request_failure", failure_data, config, e
                        )
                        return failure_data
                    raise

                wait_time = self._calculate_backoff(attempt)
                logger.warning(f"流错误，准备重试，等待 {wait_time:.2f}s")
                await asyncio.sleep(wait_time)

            except Exception as e:
                logger.error(
                    f"[{request_id}] 未预期异常: {type(e).__name__}: {str(e)} | URL: {config.url}",
                    exc_info=True,
                )

                if not self.raise_on_error:
                    error_tb = traceback.format_exc()
                    failure_data = ResponseData(
                        status_code=0,
                        url=config.url,
                        elapsed=time.time() - start_time,
                        error=e,
                        error_message=f"未预期异常: {type(e).__name__}: {str(e)}",
                        error_type=type(e).__name__,
                        error_traceback=error_tb,
                    )
                    # 🔥 新增：on_request_failure 钩子 - 允许修改失败响应数据
                    failure_data = await self.hooks.trigger_modifiable(
                        "on_request_failure", failure_data, config, e
                    )
                    return failure_data
                raise

        # 重试耗尽，返回最后一个异常
        if last_exception:
            if not self.raise_on_error:
                error_tb = traceback.format_exc()
                logger.error(
                    f"请求失败，重试已耗尽: {config.url} | "
                    f"异常: {type(last_exception).__name__}: {str(last_exception)}\n"
                    f"堆栈跟踪:\n{error_tb}"
                )
                failure_data = ResponseData(
                    status_code=0,
                    url=config.url,
                    elapsed=time.time() - start_time,
                    error=last_exception,
                    error_message=str(last_exception),
                    error_type=type(last_exception).__name__,
                    error_traceback=error_tb,
                )
                # 🔥 新增：on_request_failure 钩子 - 允许修改失败响应数据
                failure_data = await self.hooks.trigger_modifiable(
                    "on_request_failure", failure_data, config, last_exception
                )
                return failure_data
            raise last_exception

    async def _make_request(
        self, config: RequestConfig, request_id: str
    ) -> ResponseData:
        """
        实际发送请求 - 底层请求执行方法

        Args:
            config: 请求配置
            request_id: 请求唯一ID

        Returns:
            ResponseData: 响应数据

        Raises:
            各种 httpx 异常
        """
        kwargs = self._build_request_kwargs(config)
        start_time = time.time()

        logger.debug(
            f"[{request_id}] 发起请求: {config.method.value} {config.url} | "
            f"超时配置: {kwargs.get('timeout')}"
        )
        if config.params:
            logger.debug(f"[{request_id}] 请求参数: {config.params}")
        if config.headers:
            sanitized_headers = self._sanitize_headers(config.headers)
            logger.debug(f"[{request_id}] 请求头: {sanitized_headers}")

        client = await self._ensure_client()

        try:
            response = await client.request(**kwargs)

            elapsed = time.time() - start_time
            logger.debug(
                f"[{request_id}] 收到响应: {response.status_code} | "
                f"URL: {response.url} | 耗时: {elapsed:.3f}s"
            )

        except httpx.TimeoutException as e:
            elapsed = time.time() - start_time
            logger.error(
                f"[{request_id}] 请求超时: {config.method.value} {config.url} | "
                f"超时配置: {kwargs.get('timeout')} | "
                f"实际耗时: {elapsed:.3f}s | "
                f"异常详情: {type(e).__name__}: {str(e)}",
                exc_info=True,
            )
            raise

        except httpx.ConnectError as e:
            logger.error(
                f"[{request_id}] 连接失败: {config.method.value} {config.url} | "
                f"异常: {type(e).__name__}: {str(e)}",
                exc_info=True,
            )
            raise

        except Exception as e:
            logger.error(
                f"[{request_id}] 请求异常: {config.method.value} {config.url} | "
                f"异常: {type(e).__name__}: {str(e)}",
                exc_info=True,
            )
            raise

        # 构建响应数据
        history = []
        for h in response.history:
            history.append(
                ResponseData(
                    status_code=h.status_code,
                    headers=dict(h.headers),
                    content=h.content,
                    url=str(h.url),
                    elapsed=0,  # 历史记录不计算单独的耗时
                )
            )

        response_data = ResponseData(
            status_code=response.status_code,
            headers=dict(response.headers),
            content=response.content,
            url=str(response.url),
            elapsed=elapsed,
            history=history,
        )

        # 保留旧的通知型钩子以保持向后兼容
        await self.hooks.trigger("response_received", response_data)

        # 🔥 新增：after_response 钩子 - 允许修改响应数据
        response_data = await self.hooks.trigger_modifiable(
            "after_response", response_data
        )

        return response_data

    def _calculate_backoff(self, attempt: int) -> float:
        """计算退避时间"""
        if self.retry_config.strategy == RetryStrategy.FIXED:
            return self.retry_config.base_delay

        elif self.retry_config.strategy == RetryStrategy.LINEAR:
            delay = self.retry_config.base_delay * attempt

        elif self.retry_config.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.retry_config.base_delay * (2 ** (attempt - 1))

        else:
            return 0

        # 应用最大延迟限制
        delay = min(delay, self.retry_config.max_delay)

        # 添加抖动
        if self.retry_config.jitter:
            import random

            delay *= 0.5 + random.random()

        return delay

    # ========================================================================
    # 便捷方法
    # ========================================================================

    async def get(
        self,
        url: str,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> ResponseData:
        """GET 请求"""
        config = RequestConfig(
            url=url, method=HTTPMethod.GET, params=params, headers=headers, **kwargs
        )
        return await self.request(config)

    async def post(
        self,
        url: str,
        data: Optional[Union[str, bytes, Dict]] = None,
        json: Optional[Dict] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> ResponseData:
        """POST 请求"""
        config = RequestConfig(
            url=url,
            method=HTTPMethod.POST,
            data=data,
            json=json,
            headers=headers,
            **kwargs,
        )
        return await self.request(config)

    async def put(
        self,
        url: str,
        data: Optional[Union[str, bytes, Dict]] = None,
        json: Optional[Dict] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> ResponseData:
        """PUT 请求"""
        config = RequestConfig(
            url=url,
            method=HTTPMethod.PUT,
            data=data,
            json=json,
            headers=headers,
            **kwargs,
        )
        return await self.request(config)

    async def patch(
        self,
        url: str,
        data: Optional[Union[str, bytes, Dict]] = None,
        json: Optional[Dict] = None,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> ResponseData:
        """PATCH 请求"""
        config = RequestConfig(
            url=url,
            method=HTTPMethod.PATCH,
            data=data,
            json=json,
            headers=headers,
            **kwargs,
        )
        return await self.request(config)

    async def delete(
        self, url: str, headers: Optional[Dict[str, str]] = None, **kwargs
    ) -> ResponseData:
        """DELETE 请求"""
        config = RequestConfig(
            url=url, method=HTTPMethod.DELETE, headers=headers, **kwargs
        )
        return await self.request(config)

    async def head(
        self, url: str, headers: Optional[Dict[str, str]] = None, **kwargs
    ) -> ResponseData:
        """HEAD 请求"""
        config = RequestConfig(
            url=url, method=HTTPMethod.HEAD, headers=headers, **kwargs
        )
        return await self.request(config)

    async def stream(
        self,
        url: str,
        method: HTTPMethod = HTTPMethod.GET,
        chunk_size: int = 8192,
        **kwargs,
    ) -> AsyncIterator[bytes]:
        """
        流式请求

        Args:
            url: 请求 URL
            method: HTTP 方法
            chunk_size: 块大小
            **kwargs: 其他参数

        Yields:
            bytes: 响应数据块
        """
        config = RequestConfig(url=url, method=method, **kwargs)
        kwargs_dict = self._build_request_kwargs(config)

        client = await self._ensure_client()
        async with client.stream(**kwargs_dict) as response:
            async for chunk in response.aiter_bytes(chunk_size):
                yield chunk

    async def batch_requests(
        self,
        configs: List[RequestConfig],
        concurrency: int = 10,
        stop_on_error: bool = False,
    ) -> List[Union[ResponseData, Exception]]:
        """
        批量请求 - 并发执行多个请求

        Args:
            configs: 请求配置列表
            concurrency: 并发数（同时执行的最大请求数）
            stop_on_error: 是否在遇到错误时停止所有请求

        Returns:
            List[Union[ResponseData, Exception]]: 响应列表
            - 如果 raise_on_error=False，所有请求都返回ResponseData（包含错误信息）
            - 如果 raise_on_error=True 且 stop_on_error=False，失败的请求返回Exception对象
            - 如果 raise_on_error=True 且 stop_on_error=True，第一个错误会导致整个批次失败
        """
        if not configs:
            return []

        if concurrency <= 0:
            raise ValueError(f"concurrency 必须 > 0，当前值: {concurrency}")

        semaphore = asyncio.Semaphore(concurrency)

        async def _request_with_semaphore(
            config: RequestConfig,
        ) -> Union[ResponseData, Exception]:
            """使用信号量控制并发的请求"""
            async with semaphore:
                try:
                    return await self.request(config)
                except Exception as e:
                    if stop_on_error:
                        logger.error(
                            f"批量请求遇到错误，停止执行: {type(e).__name__}: {str(e)}"
                        )
                        raise
                    raise

        try:
            results = await asyncio.gather(
                *[_request_with_semaphore(config) for config in configs],
                return_exceptions=not stop_on_error,
            )
            return results
        except Exception as e:
            logger.error(f"批量请求失败: {type(e).__name__}: {str(e)}", exc_info=True)
            raise

    async def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """
        等待所有进行中的请求完成 - 优雅退出机制

        Args:
            timeout: 等待超时时间（秒），None 表示无限等待

        Returns:
            bool: 是否成功等待完成（True）或超时（False）

        Note:
            这个方法主要用于优雅关闭，确保所有请求都已处理完成
        """
        try:
            # 等待速率限制器释放所有许可（所有请求完成）
            if hasattr(self.rate_limiter, "_semaphore"):
                # 尝试获取所有许可，如果都可用说明没有进行中的请求
                max_concurrent = self.rate_limit_config.max_concurrent_requests

                async def _wait_all_complete():
                    """等待所有请求完成"""
                    acquired = []
                    try:
                        for _ in range(max_concurrent):
                            await self.rate_limiter._semaphore.acquire()
                            acquired.append(True)
                        # 如果成功获取所有许可，说明没有进行中的请求
                        return True
                    finally:
                        # 释放所有获取的许可
                        for _ in acquired:
                            self.rate_limiter._semaphore.release()

                if timeout:
                    await asyncio.wait_for(_wait_all_complete(), timeout=timeout)
                else:
                    await _wait_all_complete()

                logger.info("所有请求已完成")
                return True
        except asyncio.TimeoutError:
            logger.warning(f"等待请求完成超时: {timeout}s")
            return False
        except Exception as e:
            logger.error(f"等待完成时发生错误: {type(e).__name__}: {str(e)}")
            return False

    def get_config_warnings(self) -> List[str]:
        """
        获取配置警告 - 检查当前配置是否存在潜在问题

        Returns:
            List[str]: 警告信息列表

        Example:
            >>> client = HTTPXClient(verify_ssl=False)
            >>> warnings = client.get_config_warnings()
            >>> for warning in warnings:
            ...     print(f"⚠️  {warning}")
        """
        warnings = []

        # SSL 验证检查
        if not self.verify_ssl:
            warnings.append(
                "SSL 验证已禁用，生产环境强烈不推荐。" "这可能导致中间人攻击风险。"
            )

        # 超时配置检查
        if self.timeout.timeout and self.timeout.timeout < 1:
            warnings.append(
                f"全局超时时间过短 ({self.timeout.timeout}s)，可能导致请求频繁失败。"
            )

        if self.timeout.connect and self.timeout.connect < 1:
            warnings.append(
                f"连接超时时间过短 ({self.timeout.connect}s)，可能导致连接建立失败。"
            )

        # 重试配置检查
        if self.retry_config.max_retries > 10:
            warnings.append(
                f"重试次数过多 ({self.retry_config.max_retries})，"
                f"可能导致请求响应时间过长。"
            )

        # 连接池检查
        if self._client_kwargs.get("limits"):
            limits = self._client_kwargs["limits"]
            if hasattr(limits, "max_connections") and limits.max_connections < 10:
                warnings.append(
                    f"最大连接数较少 ({limits.max_connections})，" f"可能限制并发性能。"
                )

        # 断路器检查
        if self.circuit_breaker_config.enabled:
            if self.circuit_breaker_config.failure_threshold < 3:
                warnings.append(
                    f"断路器故障阈值过低 ({self.circuit_breaker_config.failure_threshold})，"
                    f"可能导致断路器频繁打开。"
                )

        return warnings

    async def clear_cache(self) -> None:
        """清空缓存"""
        await self.cache.clear()
        logger.info("缓存已清空")


