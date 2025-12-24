"""
AI 等高等低形态验证模块

此模块提供 AI 驱动的等高等低形态验证功能，用于在交易订单执行前
验证形态的有效性，提高交易决策的准确性。
"""

from .coordinator import AIValidationCoordinator
from .ai_client import AIValidationClient
from .decision_engine import DecisionEngine
from .fallback_strategy import FallbackStrategy, FallbackReason
from .monitor import ValidationMonitor
from .data_models import (
    MarketData,
    PatternCandidate,
    AIValidationResponse,
    ValidationResult,
    AIValidationConfig,
    AIServiceConfig,
    TradingDecision,
)
from .exceptions import (
    AIValidationError,
    DataCollectionError,
    PatternRecognitionError,
    AIServiceError,
    ConfigurationError,
)
from .config import (
    ConfigManager,
    get_config_manager,
    initialize_config,
    get_validation_config,
    get_service_config,
)

__version__ = "1.0.0"
__all__ = [
    "AIValidationCoordinator",
    "AIValidationClient",
    "DecisionEngine",
    "FallbackStrategy",
    "FallbackReason",
    "ValidationMonitor",
    "MarketData",
    "PatternCandidate",
    "AIValidationResponse",
    "ValidationResult",
    "AIValidationConfig",
    "AIServiceConfig",
    "TradingDecision",
    "AIValidationError",
    "DataCollectionError",
    "PatternRecognitionError",
    "AIServiceError",
    "ConfigurationError",
    "ConfigManager",
    "get_config_manager",
    "initialize_config",
    "get_validation_config",
    "get_service_config",
]
