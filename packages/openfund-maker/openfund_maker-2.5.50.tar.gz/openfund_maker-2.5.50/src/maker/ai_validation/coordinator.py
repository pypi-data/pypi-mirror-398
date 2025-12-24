"""
AI 验证协调器

核心组件，负责协调整个 AI 验证流程，包括数据收集、形态识别、
AI 验证和决策制定。
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional

from .data_models import (
    ValidationResult,
    TradingDecision,
    AIValidationConfig,
    AIServiceConfig,
    AIPromptConfig,
    PerformanceMetrics,
    AIValidationResponse,
)
from .exceptions import AIValidationError, ValidationTimeoutError, ConfigurationError
from .config import get_validation_config, get_service_config, get_prompt_config

logger = logging.getLogger(__name__)


class AIValidationCoordinator:
    """AI验证协调器"""

    def __init__(
        self,
        validation_config: Optional[AIValidationConfig] = None,
        service_config: Optional[AIServiceConfig] = None,
        prompt_config: Optional[AIPromptConfig] = None,
    ):
        """
        初始化协调器

        Args:
            validation_config: AI验证配置，如果为None则使用全局配置
            service_config: AI服务配置，如果为None则使用全局配置
            prompt_config: AI提示词配置，如果为None则使用全局配置
        """
        try:
            self.validation_config = validation_config or get_validation_config()
            self.service_config = service_config or get_service_config()
            self.prompt_config = prompt_config or get_prompt_config()
        except ConfigurationError:
            # 如果配置未初始化，使用默认配置
            logger.warning("使用默认配置初始化AI验证协调器")
            self.validation_config = AIValidationConfig()
            self.service_config = AIServiceConfig(
                endpoint_url="http://localhost:8000/api/v1/validate",
                api_key="default_key",
            )
            self.prompt_config = AIPromptConfig()

        # 延迟初始化组件，避免循环导入
        self._data_collector = None
        self._pattern_recognizer = None
        self._ai_client = None
        self._decision_engine = None
        self._monitor = None

        # 性能指标
        self._metrics = PerformanceMetrics()

        logger.info("AI验证协调器初始化完成")

    @property
    def data_collector(self):
        """延迟初始化数据收集器"""
        if self._data_collector is None:
            from .data_collector import DataCollector

            self._data_collector = DataCollector()
        return self._data_collector

    @property
    def pattern_recognizer(self):
        """延迟初始化形态识别器"""
        if self._pattern_recognizer is None:
            from .pattern_recognizer import PatternRecognizer

            self._pattern_recognizer = PatternRecognizer()
        return self._pattern_recognizer

    @property
    def ai_client(self):
        """延迟初始化AI客户端"""
        if self._ai_client is None:
            from .ai_client import AIValidationClient

            self._ai_client = AIValidationClient(self.service_config, prompt_config=self.prompt_config)
        return self._ai_client

    @property
    def decision_engine(self):
        """延迟初始化决策引擎"""
        if self._decision_engine is None:
            from .decision_engine import DecisionEngine

            self._decision_engine = DecisionEngine(self.validation_config)
        return self._decision_engine

    @property
    def monitor(self):
        """延迟初始化监控器"""
        if self._monitor is None:
            from .monitor import ValidationMonitor

            self._monitor = ValidationMonitor()
        return self._monitor

    def is_enabled(self) -> bool:
        """检查AI验证是否启用"""
        return self.validation_config.enabled

    def validate_pattern(
        self, trading_pair: str, strategy_signal: Dict[str, Any], 
        existing_equal_points_df=None
    ) -> ValidationResult:
        """
        执行完整的AI验证流程

        Args:
            trading_pair: 交易对
            strategy_signal: 策略信号
            existing_equal_points_df: 已识别的等高等低点DataFrame（可选）

        Returns:
            ValidationResult: 验证结果
        """
        if not self.is_enabled():
            logger.debug("AI验证已禁用，跳过验证")
            # 创建一个模拟的AI响应用于禁用状态
            mock_response = AIValidationResponse(
                confidence=1.0,
                reasoning="AI验证已禁用",
                feature_importance={},
                model_version="disabled",
                processing_time=0.0,
            )
            return ValidationResult(
                success=True,
                confidence=1.0,
                decision=TradingDecision.EXECUTE,
                ai_response=mock_response,
            )

        start_time = time.time()

        try:
            # 记录验证开始
            self.monitor.log_validation_start(trading_pair, strategy_signal)

            # 执行验证流程
            result = self._execute_validation_pipeline(
                trading_pair, strategy_signal, existing_equal_points_df
            )

            # 更新性能指标
            processing_time = time.time() - start_time
            result.processing_time = processing_time
            self._update_metrics(result)

            # 记录验证结果
            self.monitor.log_validation_result(result)

            logger.info(
                f"AI验证完成: {trading_pair}, 决策: {result.decision.value}, "
                f"置信度: {result.confidence:.3f}, 耗时: {processing_time:.3f}s"
            )

            return result

        except (TimeoutError, ValidationTimeoutError):
            error_msg = f"AI验证超时: {trading_pair}"
            logger.error(error_msg)

            result = ValidationResult(
                success=False,
                confidence=0.0,
                decision=self._get_fallback_decision(),
                error_message=error_msg,
                processing_time=time.time() - start_time,
            )

            self._update_metrics(result)
            return result

        except Exception as e:
            error_msg = f"AI验证失败: {trading_pair}, 错误: {str(e)}"
            logger.error(error_msg, exc_info=True)

            result = ValidationResult(
                success=False,
                confidence=0.0,
                decision=self._get_fallback_decision(),
                error_message=error_msg,
                processing_time=time.time() - start_time,
            )

            self._update_metrics(result)
            return result

    def _execute_validation_pipeline(
        self, trading_pair: str, strategy_signal: Dict[str, Any],
        existing_equal_points_df=None
    ) -> ValidationResult:
        """执行验证管道"""
        # 直接执行验证步骤，超时由requests库处理
        return self._run_validation_steps(trading_pair, strategy_signal, existing_equal_points_df)

    def _run_validation_steps(
        self, trading_pair: str, strategy_signal: Dict[str, Any],
        existing_equal_points_df=None
    ) -> ValidationResult:
        """
        运行验证步骤

        协调各个组件完成完整的验证流程：
        1. 收集市场数据
        2. 识别形态候选
        3. 格式化AI输入数据
        4. 调用AI验证服务
        5. 做出交易决策

        Args:
            trading_pair: 交易对
            strategy_signal: 策略信号

        Returns:
            ValidationResult: 验证结果
        """
        stage_start_time = time.time()

        try:
            # 步骤1: 收集市场数据
            logger.debug(f"步骤1: 收集市场数据 - {trading_pair}")
            market_data = self.data_collector.collect_market_data(
                trading_pair,
                self.validation_config.data_collection_candles,
                exchange=strategy_signal.get("exchange"),  # 从信号中获取exchange实例
            )

            stage_duration = time.time() - stage_start_time
            self.monitor.log_stage(
                "data_collection",
                trading_pair,
                stage_duration,
                {"candle_count": len(market_data.candles)},
            )
            logger.info(
                f"数据收集完成 - {trading_pair}, "
                f"K线数量: {len(market_data.candles)}, "
                f"耗时: {stage_duration:.3f}秒"
            )

            # 步骤2: 识别形态候选
            stage_start_time = time.time()
            logger.debug(f"步骤2: 识别形态候选 - {trading_pair}")

            # 从策略信号中获取参数（如果有）
            atr_offset = strategy_signal.get("atr_offset", 0.1)
            lookback = strategy_signal.get("lookback", 1)

            pattern_candidates = self.pattern_recognizer.identify_patterns(
                market_data, atr_offset=atr_offset, lookback=lookback,
                existing_equal_points_df=existing_equal_points_df
            )

            stage_duration = time.time() - stage_start_time
            self.monitor.log_stage(
                "pattern_recognition",
                trading_pair,
                stage_duration,
                {"pattern_count": len(pattern_candidates)},
            )
            logger.info(
                f"形态识别完成 - {trading_pair}, "
                f"候选数量: {len(pattern_candidates)}, "
                f"耗时: {stage_duration:.3f}秒"
            )

            if not pattern_candidates:
                logger.warning(f"未找到形态候选: {trading_pair}")
                decision, reason = self.decision_engine.make_decision(
                    ai_response=None,
                    original_signal=strategy_signal,
                    validation_success=False,
                    error=Exception("未找到形态候选"),
                )
                return ValidationResult(
                    success=False,
                    confidence=0.0,
                    decision=decision,
                    error_message="未找到形态候选",
                )

            # 步骤3: 格式化AI输入数据
            stage_start_time = time.time()
            logger.debug(f"步骤3: 格式化AI输入数据 - {trading_pair}")
            ai_input_data = self.pattern_recognizer.format_for_ai(
                pattern_candidates, market_data
            )

            # 将策略信号中的机会信息添加到additional_features
            if "opportunity_info" in strategy_signal:
                ai_input_data.additional_features["opportunity_info"] = strategy_signal["opportunity_info"]
                logger.debug(f"已添加机会信息到AI输入数据: {strategy_signal['opportunity_info']}")

            # 将HTF/ATF上下文和K线数据添加到additional_features
            if "htf_context" in strategy_signal:
                ai_input_data.additional_features["htf_context"] = strategy_signal["htf_context"]
                logger.debug(f"已添加HTF上下文到AI输入数据")
            if "atf_context" in strategy_signal:
                ai_input_data.additional_features["atf_context"] = strategy_signal["atf_context"]
                logger.debug(f"已添加ATF上下文到AI输入数据")
            if "htf_candles" in strategy_signal:
                ai_input_data.additional_features["htf_candles"] = strategy_signal["htf_candles"]
                logger.debug(f"已添加HTF K线数据到AI输入数据")
            if "atf_candles" in strategy_signal:
                ai_input_data.additional_features["atf_candles"] = strategy_signal["atf_candles"]
            
            # 将等高等低流动性数据添加到additional_features
            if existing_equal_points_df is not None:
                ai_input_data.additional_features["equal_liquidity_df"] = existing_equal_points_df
                logger.debug(f"已添加等高等低流动性数据到AI输入数据")
                logger.debug(f"已添加ATF K线数据到AI输入数据")

            stage_duration = time.time() - stage_start_time
            self.monitor.log_stage("data_formatting", trading_pair, stage_duration)
            logger.debug(
                f"数据格式化完成 - {trading_pair}, 耗时: {stage_duration:.3f}秒"
            )

            # 步骤4: 调用AI验证服务
            stage_start_time = time.time()
            logger.debug(f"步骤4: 调用AI验证服务 - {trading_pair}")
            ai_response = self.ai_client.validate_pattern(ai_input_data)

            stage_duration = time.time() - stage_start_time
            self.monitor.log_stage(
                "ai_validation",
                trading_pair,
                stage_duration,
                {
                    "confidence": ai_response.confidence,
                    "model_version": ai_response.model_version,
                },
            )
            logger.info(
                f"AI验证完成 - {trading_pair}, "
                f"置信度: {ai_response.confidence:.3f}, "
                f"耗时: {stage_duration:.3f}秒"
            )

            # 步骤5: 做出交易决策
            stage_start_time = time.time()
            logger.debug(f"步骤5: 做出交易决策 - {trading_pair}")
            decision, reason = self.decision_engine.make_decision(
                ai_response=ai_response,
                original_signal=strategy_signal,
                validation_success=True,
            )

            stage_duration = time.time() - stage_start_time
            self.monitor.log_stage(
                "decision_making",
                trading_pair,
                stage_duration,
                {"decision": decision.value, "reason": reason},
            )
            logger.info(
                f"决策完成 - {trading_pair}, "
                f"决策: {decision.value}, "
                f"耗时: {stage_duration:.3f}秒"
            )

            return ValidationResult(
                success=True,
                confidence=ai_response.confidence,
                decision=decision,
                ai_response=ai_response,
            )

        except Exception as e:
            # 记录错误
            self.monitor.log_error(
                error_type=type(e).__name__,
                error_message=str(e),
                trading_pair=trading_pair,
            )
            raise

    def _get_fallback_decision(self) -> TradingDecision:
        """获取降级决策"""
        if self.validation_config.fallback_mode == "execute":
            return TradingDecision.EXECUTE
        else:
            return TradingDecision.SKIP

    def _update_metrics(self, result: ValidationResult) -> None:
        """更新性能指标"""
        self._metrics.total_validations += 1

        if result.success:
            self._metrics.successful_validations += 1
        else:
            self._metrics.failed_validations += 1

        # 更新平均响应时间
        total_time = (
            self._metrics.average_response_time * (self._metrics.total_validations - 1)
            + result.processing_time
        )
        self._metrics.average_response_time = (
            total_time / self._metrics.total_validations
        )

        # 更新置信度分布
        confidence_range = self._get_confidence_range(result.confidence)
        self._metrics.confidence_distribution[confidence_range] = (
            self._metrics.confidence_distribution.get(confidence_range, 0) + 1
        )

        # 记录错误
        if not result.success and result.error_message:
            error_type = self._extract_error_type(result.error_message)
            self._metrics.error_counts[error_type] = (
                self._metrics.error_counts.get(error_type, 0) + 1
            )

    def _get_confidence_range(self, confidence: float) -> str:
        """获取置信度范围"""
        if confidence >= 0.8:
            return "high (0.8-1.0)"
        elif confidence >= 0.6:
            return "medium (0.6-0.8)"
        elif confidence >= 0.4:
            return "low (0.4-0.6)"
        else:
            return "very_low (0.0-0.4)"

    def _extract_error_type(self, error_message: str) -> str:
        """提取错误类型"""
        if "超时" in error_message or "timeout" in error_message.lower():
            return "timeout"
        elif "网络" in error_message or "network" in error_message.lower():
            return "network"
        elif "数据" in error_message or "data" in error_message.lower():
            return "data"
        elif "AI服务" in error_message or "ai service" in error_message.lower():
            return "ai_service"
        else:
            return "unknown"

    def get_metrics(self) -> PerformanceMetrics:
        """获取性能指标"""
        return self._metrics

    def reset_metrics(self) -> None:
        """重置性能指标"""
        self._metrics = PerformanceMetrics()
        logger.info("性能指标已重置")

    def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        检查协调器和各个组件的健康状态。

        Returns:
            Dict[str, Any]: 健康状态信息
        """
        health_status = {
            "coordinator": "healthy",
            "config_loaded": True,
            "enabled": self.is_enabled(),
            "ai_service": "unknown",
            "components": {
                "data_collector": (
                    "initialized" if self._data_collector else "not_initialized"
                ),
                "pattern_recognizer": (
                    "initialized" if self._pattern_recognizer else "not_initialized"
                ),
                "ai_client": "initialized" if self._ai_client else "not_initialized",
                "decision_engine": (
                    "initialized" if self._decision_engine else "not_initialized"
                ),
                "monitor": "initialized" if self._monitor else "not_initialized",
            },
            "metrics": {
                "total_validations": self._metrics.total_validations,
                "success_rate": self._metrics.success_rate,
                "failure_rate": self._metrics.failure_rate,
                "average_response_time": self._metrics.average_response_time,
            },
            "config": {
                "confidence_threshold": self.validation_config.confidence_threshold,
                "timeout_seconds": self.validation_config.timeout_seconds,
                "max_retries": self.validation_config.max_retries,
                "fallback_mode": self.validation_config.fallback_mode,
            },
        }

        try:
            # 检查AI服务健康状态
            ai_healthy = self.ai_client.health_check()
            health_status["ai_service"] = "healthy" if ai_healthy else "unhealthy"

            # 获取AI服务信息
            service_info = self.ai_client.get_service_info()
            if service_info:
                health_status["ai_service_info"] = service_info

        except Exception as e:
            health_status["ai_service"] = f"error: {str(e)}"
            logger.warning(f"AI服务健康检查失败: {str(e)}")

        return health_status

    def validate_pattern_with_exchange(
        self,
        trading_pair: str,
        strategy_signal: Dict[str, Any],
        exchange: Any,
    ) -> ValidationResult:
        """
        执行AI验证流程（带Exchange实例）

        这是一个便捷方法，直接接受Exchange实例。

        Args:
            trading_pair: 交易对
            strategy_signal: 策略信号
            exchange: Exchange实例

        Returns:
            ValidationResult: 验证结果
        """
        # 将exchange添加到策略信号中
        signal_with_exchange = strategy_signal.copy()
        signal_with_exchange["exchange"] = exchange

        return self.validate_pattern(trading_pair, signal_with_exchange)

    def get_detailed_metrics(self) -> Dict[str, Any]:
        """
        获取详细的性能指标

        Returns:
            Dict[str, Any]: 详细指标
        """
        metrics = {
            "performance": {
                "total_validations": self._metrics.total_validations,
                "successful_validations": self._metrics.successful_validations,
                "failed_validations": self._metrics.failed_validations,
                "success_rate": self._metrics.success_rate,
                "failure_rate": self._metrics.failure_rate,
                "average_response_time": self._metrics.average_response_time,
            },
            "confidence_distribution": self._metrics.confidence_distribution,
            "error_counts": self._metrics.error_counts,
            "timestamp": self._metrics.timestamp.isoformat(),
        }

        # 添加决策引擎统计
        if self._decision_engine:
            metrics["decision_statistics"] = self.decision_engine.get_statistics()

        # 添加监控器统计
        if self._monitor:
            metrics["monitor_statistics"] = self.monitor.get_statistics()

        return metrics

    def get_recent_validations(self, count: int = 10) -> list:
        """
        获取最近的验证记录

        Args:
            count: 记录数量

        Returns:
            list: 验证记录列表
        """
        if self._monitor:
            return self.monitor.get_recent_logs(count)
        return []

    def get_validations_by_trading_pair(
        self, trading_pair: str, count: int = 10
    ) -> list:
        """
        获取指定交易对的验证记录

        Args:
            trading_pair: 交易对
            count: 记录数量

        Returns:
            list: 验证记录列表
        """
        if self._monitor:
            return self.monitor.get_logs_by_trading_pair(trading_pair, count)
        return []

    def close(self) -> None:
        """
        关闭协调器，释放资源

        关闭所有组件和连接。
        """
        logger.info("正在关闭AI验证协调器...")

        try:
            # 关闭AI客户端
            if self._ai_client:
                self.ai_client.close()
                logger.debug("AI客户端已关闭")

            # 清理数据收集器缓存
            if self._data_collector:
                self.data_collector.clear_cache()
                logger.debug("数据收集器缓存已清理")

            logger.info("AI验证协调器已关闭")

        except Exception as e:
            logger.error(f"关闭协调器时发生错误: {str(e)}", exc_info=True)

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()
