"""
AI 验证系统的异常类定义

定义了系统中可能出现的各种异常类型，用于错误处理和调试。
"""


class AIValidationError(Exception):
    """AI验证系统基础异常类"""

    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class DataCollectionError(AIValidationError):
    """数据收集异常"""

    def __init__(self, message: str, trading_pair: str = None, **kwargs):
        kwargs.pop('error_code', None)  # Remove error_code from kwargs to avoid conflict
        super().__init__(message, error_code="DATA_COLLECTION_ERROR", **kwargs)
        self.trading_pair = trading_pair


class PatternRecognitionError(AIValidationError):
    """形态识别异常"""

    def __init__(self, message: str, pattern_type: str = None, **kwargs):
        kwargs.pop('error_code', None)  # Remove error_code from kwargs to avoid conflict
        super().__init__(message, error_code="PATTERN_RECOGNITION_ERROR", **kwargs)
        self.pattern_type = pattern_type


class AIServiceError(AIValidationError):
    """AI服务调用异常"""

    def __init__(
        self,
        message: str,
        status_code: int = None,
        response_data: dict = None,
        **kwargs,
    ):
        kwargs.pop('error_code', None)  # Remove error_code from kwargs to avoid conflict
        super().__init__(message, error_code="AI_SERVICE_ERROR", **kwargs)
        self.status_code = status_code
        self.response_data = response_data or {}


class AIServiceTimeoutError(AIServiceError):
    """AI服务超时异常"""

    def __init__(
        self, message: str = "AI服务调用超时", timeout_seconds: int = None, **kwargs
    ):
        kwargs.pop('error_code', None)  # Remove error_code from kwargs to avoid conflict
        super().__init__(message, error_code="AI_SERVICE_TIMEOUT", **kwargs)
        self.timeout_seconds = timeout_seconds


class AIServiceUnavailableError(AIServiceError):
    """AI服务不可用异常"""

    def __init__(self, message: str = "AI服务不可用", **kwargs):
        kwargs.pop('error_code', None)  # Remove error_code from kwargs to avoid conflict
        super().__init__(message, error_code="AI_SERVICE_UNAVAILABLE", **kwargs)


class ConfigurationError(AIValidationError):
    """配置异常"""

    def __init__(self, message: str, config_key: str = None, **kwargs):
        kwargs.pop('error_code', None)  # Remove error_code from kwargs to avoid conflict
        super().__init__(message, error_code="CONFIGURATION_ERROR", **kwargs)
        self.config_key = config_key


class ValidationTimeoutError(AIValidationError):
    """验证超时异常"""

    def __init__(
        self, message: str = "验证流程超时", timeout_seconds: int = None, **kwargs
    ):
        kwargs.pop('error_code', None)  # Remove error_code from kwargs to avoid conflict
        super().__init__(message, error_code="VALIDATION_TIMEOUT", **kwargs)
        self.timeout_seconds = timeout_seconds


class InsufficientDataError(DataCollectionError):
    """数据不足异常"""

    def __init__(
        self,
        message: str,
        required_count: int = None,
        actual_count: int = None,
        **kwargs,
    ):
        kwargs.pop('error_code', None)  # Remove error_code from kwargs to avoid conflict
        super().__init__(message, error_code="INSUFFICIENT_DATA", **kwargs)
        self.required_count = required_count
        self.actual_count = actual_count


class InvalidPatternError(PatternRecognitionError):
    """无效形态异常"""

    def __init__(self, message: str, pattern_data: dict = None, **kwargs):
        kwargs.pop('error_code', None)  # Remove error_code from kwargs to avoid conflict
        super().__init__(message, error_code="INVALID_PATTERN", **kwargs)
        self.pattern_data = pattern_data or {}


class CacheError(AIValidationError):
    """缓存异常"""

    def __init__(self, message: str, cache_key: str = None, **kwargs):
        kwargs.pop('error_code', None)  # Remove error_code from kwargs to avoid conflict
        super().__init__(message, error_code="CACHE_ERROR", **kwargs)
        self.cache_key = cache_key
