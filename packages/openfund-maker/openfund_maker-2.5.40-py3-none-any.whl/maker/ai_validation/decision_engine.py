"""
决策引擎

基于AI验证结果做出交易决策。
"""

import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

from .data_models import (
    AIValidationResponse,
    TradingDecision,
    AIValidationConfig,
    ValidationResult,
)
from .exceptions import AIValidationError, AIServiceError
from .fallback_strategy import FallbackStrategy, FallbackReason

logger = logging.getLogger(__name__)


class DecisionEngine:
    """
    决策引擎

    基于AI验证结果和配置的置信度阈值做出交易决策。
    支持多种决策策略和降级模式。
    """

    def __init__(self, config: AIValidationConfig):
        """
        初始化决策引擎

        Args:
            config: AI验证配置
        """
        self.config = config
        self.fallback_strategy = FallbackStrategy(config)
        self._decision_count = 0
        self._execute_count = 0
        self._skip_count = 0
        self._fallback_count = 0

        logger.info(
            f"决策引擎初始化完成 - "
            f"置信度阈值: {config.confidence_threshold}, "
            f"降级模式: {config.fallback_mode}"
        )

    def make_decision(
        self,
        ai_response: Optional[AIValidationResponse],
        original_signal: Dict[str, Any],
        validation_success: bool = True,
        error: Optional[Exception] = None,
    ) -> Tuple[TradingDecision, str]:
        """
        基于验证结果做出交易决策

        Args:
            ai_response: AI验证响应，可能为None（验证失败时）
            original_signal: 原始策略信号
            validation_success: 验证是否成功
            error: 验证失败时的错误信息

        Returns:
            Tuple[TradingDecision, str]: (交易决策, 决策原因)
        """
        self._decision_count += 1

        try:
            # 如果验证失败，使用降级策略
            if not validation_success or ai_response is None:
                return self._handle_validation_failure(error)

            # 基于置信度做决策
            confidence = ai_response.confidence
            decision, reason = self._evaluate_confidence(confidence, ai_response)

            # 更新统计
            if decision == TradingDecision.EXECUTE:
                self._execute_count += 1
            elif decision == TradingDecision.SKIP:
                self._skip_count += 1

            # 记录详细信息
            self._log_decision_details(decision, reason, ai_response, original_signal)

            return decision, reason

        except Exception as e:
            logger.error(f"决策制定过程发生异常: {str(e)}", exc_info=True)
            return self._get_fallback_decision("决策过程异常")

    def _evaluate_confidence(
        self, confidence: float, ai_response: AIValidationResponse
    ) -> Tuple[TradingDecision, str]:
        """
        评估置信度并做出决策

        Args:
            confidence: AI置信度
            ai_response: AI响应

        Returns:
            Tuple[TradingDecision, str]: (决策, 原因)
        """
        threshold = self.config.confidence_threshold
        confidence_level = self.get_confidence_level_description(confidence)

        logger.debug(
            f"评估置信度 - 值: {confidence:.3f}, 阈值: {threshold:.3f}, "
            f"等级: {confidence_level}"
        )

        if confidence >= threshold:
            decision = TradingDecision.EXECUTE
            reason = (
                f"AI置信度 {confidence:.3f} 达到阈值 {threshold:.3f}，"
                f"建议执行交易。{confidence_level}"
            )
        else:
            decision = TradingDecision.SKIP
            reason = (
                f"AI置信度 {confidence:.3f} 低于阈值 {threshold:.3f}，"
                f"建议跳过交易。{confidence_level}"
            )

        return decision, reason

    def _handle_validation_failure(
        self, error: Optional[Exception]
    ) -> Tuple[TradingDecision, str]:
        """
        处理验证失败的情况

        Args:
            error: 错误信息

        Returns:
            Tuple[TradingDecision, str]: (降级决策, 原因)
        """
        if error is None:
            error = Exception("未知错误")

        logger.warning(f"AI验证失败，使用降级策略 - 错误: {str(error)}")

        # 使用降级策略处理器
        decision, reason, fallback_reason = self.fallback_strategy.handle_failure(
            error=error, context={"decision_count": self._decision_count}
        )

        self._fallback_count += 1

        return decision, reason

    def _get_fallback_decision(self, reason: str = "") -> Tuple[TradingDecision, str]:
        """
        获取降级决策

        Args:
            reason: 触发降级的原因

        Returns:
            Tuple[TradingDecision, str]: (降级决策, 完整原因)
        """
        if self.config.fallback_mode == "execute":
            decision = TradingDecision.EXECUTE
            full_reason = f"降级模式: 执行交易。{reason}"
            logger.info(f"使用降级策略 - 执行交易: {reason}")
        else:
            decision = TradingDecision.SKIP
            full_reason = f"降级模式: 跳过交易。{reason}"
            logger.info(f"使用降级策略 - 跳过交易: {reason}")

        return decision, full_reason

    def _log_decision_details(
        self,
        decision: TradingDecision,
        reason: str,
        ai_response: AIValidationResponse,
        original_signal: Dict[str, Any],
    ) -> None:
        """
        记录决策详细信息

        Args:
            decision: 交易决策
            reason: 决策原因
            ai_response: AI响应
            original_signal: 原始信号
        """
        logger.info(f"交易决策: {decision.value}")
        logger.info(f"决策原因: {reason}")

        # 记录AI推理信息
        if ai_response.reasoning:
            logger.debug(f"AI推理: {ai_response.reasoning}")

        # 记录特征重要性（前5个）
        if ai_response.feature_importance:
            # 只保留数值类型的特征
            numeric_features = {k: v for k, v in ai_response.feature_importance.items() 
                               if isinstance(v, (int, float))}
            if numeric_features:
                top_features = sorted(
                    numeric_features.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )[:5]
                logger.debug(f"重要特征: {top_features}")

        # 记录模型信息
        logger.debug(
            f"模型版本: {ai_response.model_version}, "
            f"处理时间: {ai_response.processing_time:.3f}秒"
        )

        # 记录原始信号信息
        if original_signal:
            signal_type = original_signal.get("type", "unknown")
            signal_pair = original_signal.get("trading_pair", "unknown")
            logger.debug(f"原始信号 - 类型: {signal_type}, 交易对: {signal_pair}")

    def should_execute_trade(self, confidence: float) -> bool:
        """
        判断是否应该执行交易

        Args:
            confidence: 置信度

        Returns:
            bool: 是否执行交易
        """
        return confidence >= self.config.confidence_threshold

    def evaluate_validation_result(
        self, result: ValidationResult, original_signal: Dict[str, Any]
    ) -> Tuple[TradingDecision, str]:
        """
        评估完整的验证结果并做出决策

        这是一个便捷方法，直接接受ValidationResult对象

        Args:
            result: 验证结果
            original_signal: 原始策略信号

        Returns:
            Tuple[TradingDecision, str]: (交易决策, 决策原因)
        """
        return self.make_decision(
            ai_response=result.ai_response,
            original_signal=original_signal,
            validation_success=result.success,
            error=None if result.success else Exception(result.error_message),
        )

    def get_confidence_level_description(self, confidence: float) -> str:
        """
        获取置信度等级描述

        Args:
            confidence: 置信度值

        Returns:
            str: 置信度等级描述
        """
        if confidence >= 0.8:
            return "高置信度 (0.8-1.0): 强烈建议执行交易"
        elif confidence >= 0.6:
            return "中等置信度 (0.6-0.8): 可以执行交易但需谨慎"
        elif confidence >= 0.4:
            return "低置信度 (0.4-0.6): 建议暂缓交易"
        else:
            return "极低置信度 (0.0-0.4): 不建议执行交易"

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取决策统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = {
            "total_decisions": self._decision_count,
            "execute_count": self._execute_count,
            "skip_count": self._skip_count,
            "fallback_count": self._fallback_count,
            "execute_rate": (
                self._execute_count / self._decision_count
                if self._decision_count > 0
                else 0.0
            ),
            "skip_rate": (
                self._skip_count / self._decision_count
                if self._decision_count > 0
                else 0.0
            ),
            "fallback_rate": (
                self._fallback_count / self._decision_count
                if self._decision_count > 0
                else 0.0
            ),
        }

        # 添加降级策略统计
        stats["fallback_statistics"] = self.fallback_strategy.get_fallback_statistics()

        return stats

    def reset_statistics(self) -> None:
        """重置统计信息"""
        self._decision_count = 0
        self._execute_count = 0
        self._skip_count = 0
        self._fallback_count = 0
        self.fallback_strategy.reset_statistics()
        logger.info("决策统计信息已重置")

    def mark_service_available(self) -> None:
        """标记AI服务恢复可用"""
        self.fallback_strategy.mark_service_available()

    def is_service_likely_down(self) -> bool:
        """
        判断AI服务是否可能处于不可用状态

        Returns:
            bool: 服务是否可能不可用
        """
        return self.fallback_strategy.is_service_likely_down()
