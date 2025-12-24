"""
验证日志记录器

负责记录验证过程的详细信息，提供结构化日志记录功能。
支持多种日志级别和输出格式，便于问题排查和数据分析。
"""

import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from .data_models import ValidationResult, TradingDecision

logger = logging.getLogger(__name__)


class ValidationLogger:
    """
    验证日志记录器

    提供结构化的验证日志记录功能，记录验证过程的详细信息。
    """

    def __init__(
        self,
        log_file_path: Optional[str] = None,
        enable_file_logging: bool = True,
        enable_json_logging: bool = False,
    ):
        """
        初始化日志记录器

        Args:
            log_file_path: 日志文件路径，如果为None则使用默认路径
            enable_file_logging: 是否启用文件日志
            enable_json_logging: 是否启用JSON格式日志
        """
        self.enable_file_logging = enable_file_logging
        self.enable_json_logging = enable_json_logging

        # 设置日志文件路径
        if log_file_path:
            self.log_file_path = Path(log_file_path)
        else:
            self.log_file_path = Path("log/ai_validation.log")

        # 设置JSON日志文件路径
        self.json_log_file_path = self.log_file_path.with_suffix(".json")

        # 确保日志目录存在
        if self.enable_file_logging:
            self.log_file_path.parent.mkdir(parents=True, exist_ok=True)

        # 配置文件日志处理器
        if self.enable_file_logging:
            self._setup_file_handler()

        logger.info("验证日志记录器初始化完成")

    def _setup_file_handler(self) -> None:
        """设置文件日志处理器"""
        try:
            # 创建文件处理器
            file_handler = logging.FileHandler(
                self.log_file_path, mode="a", encoding="utf-8"
            )
            file_handler.setLevel(logging.DEBUG)

            # 设置日志格式
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            file_handler.setFormatter(formatter)

            # 添加到logger
            validation_logger = logging.getLogger("ai_validation")
            validation_logger.addHandler(file_handler)
            validation_logger.setLevel(logging.DEBUG)

        except Exception as e:
            logger.error(f"设置文件日志处理器失败: {str(e)}")

    def log_validation_start(
        self, trading_pair: str, strategy_signal: Dict[str, Any]
    ) -> None:
        """
        记录验证开始

        Args:
            trading_pair: 交易对
            strategy_signal: 策略信号
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "event": "validation_start",
            "trading_pair": trading_pair,
            "strategy_signal": {
                "type": strategy_signal.get("type", "unknown"),
                "direction": strategy_signal.get("direction", "unknown"),
                "price": strategy_signal.get("price"),
                "timeframe": strategy_signal.get("timeframe"),
            },
        }

        # 记录到标准日志
        logger.info(
            f"[验证开始] 交易对: {trading_pair}, "
            f"信号类型: {strategy_signal.get('type', 'unknown')}, "
            f"方向: {strategy_signal.get('direction', 'unknown')}"
        )

        # 记录到JSON日志
        if self.enable_json_logging:
            self._write_json_log(log_data)

    def log_validation_result(self, result: ValidationResult) -> None:
        """
        记录验证结果

        Args:
            result: 验证结果
        """
        log_data = {
            "timestamp": result.timestamp.isoformat(),
            "event": "validation_result",
            "success": result.success,
            "confidence": result.confidence,
            "decision": result.decision.value,
            "processing_time": result.processing_time,
            "error_message": result.error_message,
        }

        # 如果有AI响应，添加详细信息
        if result.ai_response:
            log_data["ai_response"] = {
                "confidence": result.ai_response.confidence,
                "reasoning": result.ai_response.reasoning,
                "model_version": result.ai_response.model_version,
                "processing_time": result.ai_response.processing_time,
                "feature_importance": result.ai_response.feature_importance,
            }

        # 记录到标准日志
        if result.success:
            logger.info(
                f"[验证成功] 置信度: {result.confidence:.3f}, "
                f"决策: {result.decision.value}, "
                f"耗时: {result.processing_time:.3f}秒"
            )
        else:
            logger.warning(
                f"[验证失败] 决策: {result.decision.value}, "
                f"错误: {result.error_message}, "
                f"耗时: {result.processing_time:.3f}秒"
            )

        # 记录到JSON日志
        if self.enable_json_logging:
            self._write_json_log(log_data)

    def log_decision(self, decision: TradingDecision, reasoning: str) -> None:
        """
        记录交易决策

        Args:
            decision: 交易决策
            reasoning: 决策理由
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "event": "trading_decision",
            "decision": decision.value,
            "reasoning": reasoning,
        }

        # 记录到标准日志
        logger.info(f"[交易决策] 决策: {decision.value}, 理由: {reasoning}")

        # 记录到JSON日志
        if self.enable_json_logging:
            self._write_json_log(log_data)

    def log_performance_metrics(self, metrics: Dict[str, Any]) -> None:
        """
        记录性能指标

        Args:
            metrics: 性能指标字典
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "event": "performance_metrics",
            "metrics": metrics,
        }

        # 记录到标准日志
        logger.info(
            f"[性能指标] 总验证数: {metrics.get('total_validations', 0)}, "
            f"成功率: {metrics.get('success_rate', 0):.2%}, "
            f"平均响应时间: {metrics.get('average_response_time', 0):.3f}秒"
        )

        # 记录到JSON日志
        if self.enable_json_logging:
            self._write_json_log(log_data)

    def log_data_collection(
        self, trading_pair: str, candle_count: int, duration: float
    ) -> None:
        """
        记录数据收集过程

        Args:
            trading_pair: 交易对
            candle_count: K线数量
            duration: 耗时（秒）
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "event": "data_collection",
            "trading_pair": trading_pair,
            "candle_count": candle_count,
            "duration": duration,
        }

        logger.debug(
            f"[数据收集] 交易对: {trading_pair}, "
            f"K线数量: {candle_count}, "
            f"耗时: {duration:.3f}秒"
        )

        if self.enable_json_logging:
            self._write_json_log(log_data)

    def log_pattern_recognition(
        self, trading_pair: str, pattern_count: int, duration: float
    ) -> None:
        """
        记录形态识别过程

        Args:
            trading_pair: 交易对
            pattern_count: 识别到的形态数量
            duration: 耗时（秒）
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "event": "pattern_recognition",
            "trading_pair": trading_pair,
            "pattern_count": pattern_count,
            "duration": duration,
        }

        logger.debug(
            f"[形态识别] 交易对: {trading_pair}, "
            f"形态数量: {pattern_count}, "
            f"耗时: {duration:.3f}秒"
        )

        if self.enable_json_logging:
            self._write_json_log(log_data)

    def log_ai_validation(
        self, trading_pair: str, confidence: float, duration: float
    ) -> None:
        """
        记录AI验证过程

        Args:
            trading_pair: 交易对
            confidence: 置信度
            duration: 耗时（秒）
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "event": "ai_validation",
            "trading_pair": trading_pair,
            "confidence": confidence,
            "duration": duration,
        }

        logger.debug(
            f"[AI验证] 交易对: {trading_pair}, "
            f"置信度: {confidence:.3f}, "
            f"耗时: {duration:.3f}秒"
        )

        if self.enable_json_logging:
            self._write_json_log(log_data)

    def log_error(
        self,
        error_type: str,
        error_message: str,
        trading_pair: Optional[str] = None,
        stage: Optional[str] = None,
        stack_trace: Optional[str] = None,
    ) -> None:
        """
        记录错误信息

        Args:
            error_type: 错误类型
            error_message: 错误消息
            trading_pair: 交易对（可选）
            stage: 发生错误的阶段（可选）
            stack_trace: 堆栈跟踪（可选）
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "event": "error",
            "error_type": error_type,
            "error_message": error_message,
            "trading_pair": trading_pair,
            "stage": stage,
            "stack_trace": stack_trace,
        }

        # 记录到标准日志
        error_msg = f"[错误] 类型: {error_type}, 消息: {error_message}"
        if trading_pair:
            error_msg += f", 交易对: {trading_pair}"
        if stage:
            error_msg += f", 阶段: {stage}"

        logger.error(error_msg)

        # 记录到JSON日志
        if self.enable_json_logging:
            self._write_json_log(log_data)

    def log_fallback(
        self, trading_pair: str, reason: str, fallback_decision: TradingDecision
    ) -> None:
        """
        记录降级处理

        Args:
            trading_pair: 交易对
            reason: 降级原因
            fallback_decision: 降级决策
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "event": "fallback",
            "trading_pair": trading_pair,
            "reason": reason,
            "fallback_decision": fallback_decision.value,
        }

        logger.warning(
            f"[降级处理] 交易对: {trading_pair}, "
            f"原因: {reason}, "
            f"决策: {fallback_decision.value}"
        )

        if self.enable_json_logging:
            self._write_json_log(log_data)

    def log_cache_hit(self, trading_pair: str, cache_key: str) -> None:
        """
        记录缓存命中

        Args:
            trading_pair: 交易对
            cache_key: 缓存键
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "event": "cache_hit",
            "trading_pair": trading_pair,
            "cache_key": cache_key,
        }

        logger.debug(f"[缓存命中] 交易对: {trading_pair}, 键: {cache_key}")

        if self.enable_json_logging:
            self._write_json_log(log_data)

    def log_cache_miss(self, trading_pair: str, cache_key: str) -> None:
        """
        记录缓存未命中

        Args:
            trading_pair: 交易对
            cache_key: 缓存键
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "event": "cache_miss",
            "trading_pair": trading_pair,
            "cache_key": cache_key,
        }

        logger.debug(f"[缓存未命中] 交易对: {trading_pair}, 键: {cache_key}")

        if self.enable_json_logging:
            self._write_json_log(log_data)

    def _write_json_log(self, log_data: Dict[str, Any]) -> None:
        """
        写入JSON格式日志

        Args:
            log_data: 日志数据
        """
        try:
            with open(self.json_log_file_path, "a", encoding="utf-8") as f:
                json.dump(log_data, f, ensure_ascii=False)
                f.write("\n")
        except Exception as e:
            logger.error(f"写入JSON日志失败: {str(e)}")

    def get_log_file_path(self) -> str:
        """
        获取日志文件路径

        Returns:
            str: 日志文件路径
        """
        return str(self.log_file_path)

    def get_json_log_file_path(self) -> str:
        """
        获取JSON日志文件路径

        Returns:
            str: JSON日志文件路径
        """
        return str(self.json_log_file_path)

    def rotate_logs(self, max_size_mb: int = 100) -> None:
        """
        轮转日志文件

        当日志文件超过指定大小时，进行轮转。

        Args:
            max_size_mb: 最大文件大小（MB）
        """
        try:
            # 检查文本日志文件大小
            if self.log_file_path.exists():
                size_mb = self.log_file_path.stat().st_size / (1024 * 1024)
                if size_mb > max_size_mb:
                    # 重命名旧文件
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_path = self.log_file_path.with_suffix(f".{timestamp}.log")
                    self.log_file_path.rename(backup_path)
                    logger.info(f"日志文件已轮转: {backup_path}")

            # 检查JSON日志文件大小
            if self.enable_json_logging and self.json_log_file_path.exists():
                size_mb = self.json_log_file_path.stat().st_size / (1024 * 1024)
                if size_mb > max_size_mb:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_path = self.json_log_file_path.with_suffix(
                        f".{timestamp}.json"
                    )
                    self.json_log_file_path.rename(backup_path)
                    logger.info(f"JSON日志文件已轮转: {backup_path}")

        except Exception as e:
            logger.error(f"日志轮转失败: {str(e)}")
