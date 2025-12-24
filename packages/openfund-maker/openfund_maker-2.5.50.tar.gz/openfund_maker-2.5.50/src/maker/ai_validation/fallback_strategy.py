"""
降级策略处理

处理AI服务不可用、超时和其他失败场景的降级策略。
提供多种降级模式和智能决策能力。
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum

from .data_models import TradingDecision, AIValidationConfig
from .exceptions import (
    AIServiceError,
    AIServiceTimeoutError,
    AIServiceUnavailableError,
    ValidationTimeoutError,
)

logger = logging.getLogger(__name__)


class FallbackReason(Enum):
    """降级原因枚举"""

    AI_SERVICE_UNAVAILABLE = "ai_service_unavailable"
    AI_SERVICE_TIMEOUT = "ai_service_timeout"
    VALIDATION_TIMEOUT = "validation_timeout"
    NETWORK_ERROR = "network_error"
    DATA_COLLECTION_ERROR = "data_collection_error"
    PATTERN_RECOGNITION_ERROR = "pattern_recognition_error"
    UNKNOWN_ERROR = "unknown_error"


class FallbackStrategy:
    """
    降级策略处理器

    根据不同的失败场景和配置，决定如何处理交易决策。
    支持多种降级模式和智能决策。
    """

    def __init__(self, config: AIValidationConfig):
        """
        初始化降级策略处理器

        Args:
            config: AI验证配置
        """
        self.config = config
        self._fallback_history: list = []
        self._service_unavailable_count = 0
        self._last_service_check = None
        self._service_down_since = None

        logger.info(f"降级策略初始化完成 - 模式: {config.fallback_mode}")

    def handle_failure(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
    ) -> tuple[TradingDecision, str, FallbackReason]:
        """
        处理失败场景

        Args:
            error: 发生的错误
            context: 上下文信息

        Returns:
            tuple[TradingDecision, str, FallbackReason]: (决策, 原因, 降级原因类型)
        """
        # 识别错误类型
        fallback_reason = self._identify_error_type(error)

        # 记录降级事件
        self._record_fallback_event(fallback_reason, error, context)

        # 根据错误类型和配置做出决策
        decision, reason = self._make_fallback_decision(fallback_reason, error, context)

        logger.warning(
            f"触发降级策略 - 原因: {fallback_reason.value}, "
            f"决策: {decision.value}, 详情: {reason}"
        )

        return decision, reason, fallback_reason

    def _identify_error_type(self, error: Exception) -> FallbackReason:
        """
        识别错误类型

        Args:
            error: 错误对象

        Returns:
            FallbackReason: 降级原因
        """
        if isinstance(error, AIServiceUnavailableError):
            return FallbackReason.AI_SERVICE_UNAVAILABLE
        elif isinstance(error, AIServiceTimeoutError):
            return FallbackReason.AI_SERVICE_TIMEOUT
        elif isinstance(error, ValidationTimeoutError):
            return FallbackReason.VALIDATION_TIMEOUT
        elif isinstance(error, AIServiceError):
            # 检查是否是网络错误
            if "network" in str(error).lower() or "connection" in str(error).lower():
                return FallbackReason.NETWORK_ERROR
            return FallbackReason.AI_SERVICE_UNAVAILABLE
        else:
            return FallbackReason.UNKNOWN_ERROR

    def _make_fallback_decision(
        self,
        fallback_reason: FallbackReason,
        error: Exception,
        context: Optional[Dict[str, Any]],
    ) -> tuple[TradingDecision, str]:
        """
        根据降级原因做出决策

        Args:
            fallback_reason: 降级原因
            error: 错误对象
            context: 上下文信息

        Returns:
            tuple[TradingDecision, str]: (决策, 原因说明)
        """
        # 基础降级模式
        base_decision = self._get_base_fallback_decision()

        # 根据不同的失败原因调整决策
        if fallback_reason == FallbackReason.AI_SERVICE_UNAVAILABLE:
            return self._handle_service_unavailable(base_decision, error)
        elif fallback_reason == FallbackReason.AI_SERVICE_TIMEOUT:
            return self._handle_service_timeout(base_decision, error)
        elif fallback_reason == FallbackReason.VALIDATION_TIMEOUT:
            return self._handle_validation_timeout(base_decision, error)
        elif fallback_reason == FallbackReason.NETWORK_ERROR:
            return self._handle_network_error(base_decision, error)
        else:
            return self._handle_unknown_error(base_decision, error)

    def _get_base_fallback_decision(self) -> TradingDecision:
        """
        获取基础降级决策

        Returns:
            TradingDecision: 基础决策
        """
        if self.config.fallback_mode == "execute":
            return TradingDecision.EXECUTE
        else:
            return TradingDecision.SKIP

    def _handle_service_unavailable(
        self, base_decision: TradingDecision, error: Exception
    ) -> tuple[TradingDecision, str]:
        """
        处理AI服务不可用

        Args:
            base_decision: 基础决策
            error: 错误对象

        Returns:
            tuple[TradingDecision, str]: (决策, 原因)
        """
        self._service_unavailable_count += 1

        if self._service_down_since is None:
            self._service_down_since = datetime.now()

        # 如果服务长时间不可用，可能需要更保守的策略
        downtime = datetime.now() - self._service_down_since
        if downtime > timedelta(minutes=5):
            # 服务长时间不可用，采用保守策略
            decision = TradingDecision.SKIP
            reason = (
                f"AI服务已不可用 {downtime.total_seconds():.0f} 秒，"
                f"采用保守策略跳过交易。错误: {str(error)}"
            )
            logger.warning(f"AI服务长时间不可用: {downtime}")
        else:
            decision = base_decision
            reason = (
                f"AI服务暂时不可用，使用降级模式 '{self.config.fallback_mode}'。"
                f"错误: {str(error)}"
            )

        return decision, reason

    def _handle_service_timeout(
        self, base_decision: TradingDecision, error: Exception
    ) -> tuple[TradingDecision, str]:
        """
        处理AI服务超时

        Args:
            base_decision: 基础决策
            error: 错误对象

        Returns:
            tuple[TradingDecision, str]: (决策, 原因)
        """
        timeout_seconds = getattr(error, "timeout_seconds", self.config.timeout_seconds)

        decision = base_decision
        reason = (
            f"AI服务响应超时 ({timeout_seconds}秒)，"
            f"使用降级模式 '{self.config.fallback_mode}'。"
        )

        return decision, reason

    def _handle_validation_timeout(
        self, base_decision: TradingDecision, error: Exception
    ) -> tuple[TradingDecision, str]:
        """
        处理验证流程超时

        Args:
            base_decision: 基础决策
            error: 错误对象

        Returns:
            tuple[TradingDecision, str]: (决策, 原因)
        """
        timeout_seconds = getattr(error, "timeout_seconds", self.config.timeout_seconds)

        decision = base_decision
        reason = (
            f"验证流程超时 ({timeout_seconds}秒)，"
            f"使用降级模式 '{self.config.fallback_mode}'。"
        )

        return decision, reason

    def _handle_network_error(
        self, base_decision: TradingDecision, error: Exception
    ) -> tuple[TradingDecision, str]:
        """
        处理网络错误

        Args:
            base_decision: 基础决策
            error: 错误对象

        Returns:
            tuple[TradingDecision, str]: (决策, 原因)
        """
        decision = base_decision
        reason = (
            f"网络连接错误，使用降级模式 '{self.config.fallback_mode}'。"
            f"错误: {str(error)}"
        )

        return decision, reason

    def _handle_unknown_error(
        self, base_decision: TradingDecision, error: Exception
    ) -> tuple[TradingDecision, str]:
        """
        处理未知错误

        Args:
            base_decision: 基础决策
            error: 错误对象

        Returns:
            tuple[TradingDecision, str]: (决策, 原因)
        """
        decision = base_decision
        reason = (
            f"发生未知错误，使用降级模式 '{self.config.fallback_mode}'。"
            f"错误类型: {type(error).__name__}, 详情: {str(error)}"
        )

        return decision, reason

    def _record_fallback_event(
        self,
        fallback_reason: FallbackReason,
        error: Exception,
        context: Optional[Dict[str, Any]],
    ) -> None:
        """
        记录降级事件

        Args:
            fallback_reason: 降级原因
            error: 错误对象
            context: 上下文信息
        """
        event = {
            "timestamp": datetime.now(),
            "reason": fallback_reason.value,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
        }

        self._fallback_history.append(event)

        # 只保留最近100条记录
        if len(self._fallback_history) > 100:
            self._fallback_history = self._fallback_history[-100:]

    def mark_service_available(self) -> None:
        """标记服务恢复可用"""
        if self._service_down_since is not None:
            downtime = datetime.now() - self._service_down_since
            logger.info(f"AI服务恢复可用，停机时长: {downtime}")

        self._service_unavailable_count = 0
        self._service_down_since = None
        self._last_service_check = datetime.now()

    def is_service_likely_down(self) -> bool:
        """
        判断服务是否可能处于不可用状态

        Returns:
            bool: 服务是否可能不可用
        """
        # 如果最近有多次服务不可用记录，认为服务可能处于故障状态
        if self._service_unavailable_count >= 3:
            return True

        # 如果服务已经不可用超过1分钟
        if self._service_down_since is not None:
            downtime = datetime.now() - self._service_down_since
            if downtime > timedelta(minutes=1):
                return True

        return False

    def get_fallback_statistics(self) -> Dict[str, Any]:
        """
        获取降级统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        # 统计各种降级原因的次数
        reason_counts = {}
        for event in self._fallback_history:
            reason = event["reason"]
            reason_counts[reason] = reason_counts.get(reason, 0) + 1

        return {
            "total_fallbacks": len(self._fallback_history),
            "service_unavailable_count": self._service_unavailable_count,
            "service_down_since": self._service_down_since,
            "last_service_check": self._last_service_check,
            "is_service_likely_down": self.is_service_likely_down(),
            "reason_distribution": reason_counts,
            "recent_events": (
                self._fallback_history[-10:] if self._fallback_history else []
            ),
        }

    def reset_statistics(self) -> None:
        """重置统计信息"""
        self._fallback_history.clear()
        self._service_unavailable_count = 0
        self._service_down_since = None
        self._last_service_check = None
        logger.info("降级策略统计信息已重置")
