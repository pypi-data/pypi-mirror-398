"""
验证监控器

负责记录验证过程的详细信息、收集性能指标和提供监控数据。
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict

from .data_models import ValidationResult, PerformanceMetrics

logger = logging.getLogger(__name__)


class ValidationMonitor:
    """
    验证监控器

    记录验证过程的各个阶段、收集性能指标和统计信息。
    """

    def __init__(self):
        """初始化监控器"""
        self._validation_logs = []
        self._max_log_entries = 1000  # 最多保留1000条日志

        # 阶段性能指标
        self._stage_metrics = defaultdict(
            lambda: {
                "total_count": 0,
                "total_duration": 0.0,
                "min_duration": float("inf"),
                "max_duration": 0.0,
                "error_count": 0,
            }
        )

        # 性能指标
        self._performance_metrics = PerformanceMetrics()

        logger.info("验证监控器初始化完成")

    def log_validation_start(
        self, trading_pair: str, strategy_signal: Dict[str, Any]
    ) -> None:
        """
        记录验证开始

        Args:
            trading_pair: 交易对
            strategy_signal: 策略信号
        """
        log_entry = {
            "timestamp": datetime.now(),
            "event": "validation_start",
            "trading_pair": trading_pair,
            "strategy_signal": strategy_signal,
        }

        self._add_log_entry(log_entry)

        logger.debug(
            f"验证开始 - 交易对: {trading_pair}, "
            f"信号类型: {strategy_signal.get('type', 'unknown')}"
        )

    def log_validation_result(self, result: ValidationResult) -> None:
        """
        记录验证结果

        Args:
            result: 验证结果
        """
        log_entry = {
            "timestamp": result.timestamp,
            "event": "validation_result",
            "success": result.success,
            "confidence": result.confidence,
            "decision": result.decision.value,
            "processing_time": result.processing_time,
            "error_message": result.error_message,
        }

        # 如果有AI响应，记录详细信息
        if result.ai_response:
            log_entry["ai_response"] = {
                "confidence": result.ai_response.confidence,
                "reasoning": result.ai_response.reasoning,
                "model_version": result.ai_response.model_version,
                "processing_time": result.ai_response.processing_time,
            }

        self._add_log_entry(log_entry)

        logger.info(
            f"验证结果 - 成功: {result.success}, "
            f"置信度: {result.confidence:.3f}, "
            f"决策: {result.decision.value}, "
            f"耗时: {result.processing_time:.3f}秒"
        )

    def log_stage(
        self,
        stage_name: str,
        trading_pair: str,
        duration: float,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        记录验证流程的某个阶段

        Args:
            stage_name: 阶段名称
            trading_pair: 交易对
            duration: 阶段耗时（秒）
            details: 额外详情
        """
        log_entry = {
            "timestamp": datetime.now(),
            "event": "stage_complete",
            "stage": stage_name,
            "trading_pair": trading_pair,
            "duration": duration,
            "details": details or {},
        }

        self._add_log_entry(log_entry)

        # 更新阶段性能指标
        self._update_stage_metrics(stage_name, duration, success=True)

        logger.debug(f"阶段完成 - {stage_name}: {trading_pair}, 耗时: {duration:.3f}秒")

    def log_error(
        self,
        error_type: str,
        error_message: str,
        trading_pair: Optional[str] = None,
        stage: Optional[str] = None,
    ) -> None:
        """
        记录错误

        Args:
            error_type: 错误类型
            error_message: 错误消息
            trading_pair: 交易对（可选）
            stage: 发生错误的阶段（可选）
        """
        log_entry = {
            "timestamp": datetime.now(),
            "event": "error",
            "error_type": error_type,
            "error_message": error_message,
            "trading_pair": trading_pair,
            "stage": stage,
        }

        self._add_log_entry(log_entry)

        # 如果指定了阶段，更新该阶段的错误计数
        if stage:
            self._stage_metrics[stage]["error_count"] += 1

        logger.error(
            f"验证错误 - 类型: {error_type}, "
            f"交易对: {trading_pair}, "
            f"阶段: {stage}, "
            f"消息: {error_message}"
        )

    def _add_log_entry(self, log_entry: Dict[str, Any]) -> None:
        """
        添加日志条目

        Args:
            log_entry: 日志条目
        """
        self._validation_logs.append(log_entry)

        # 限制日志数量
        if len(self._validation_logs) > self._max_log_entries:
            self._validation_logs = self._validation_logs[-self._max_log_entries :]

    def get_recent_logs(self, count: int = 10) -> list:
        """
        获取最近的日志

        Args:
            count: 日志数量

        Returns:
            list: 日志列表
        """
        return self._validation_logs[-count:] if self._validation_logs else []

    def get_logs_by_trading_pair(self, trading_pair: str, count: int = 10) -> list:
        """
        获取指定交易对的日志

        Args:
            trading_pair: 交易对
            count: 日志数量

        Returns:
            list: 日志列表
        """
        filtered_logs = [
            log
            for log in self._validation_logs
            if log.get("trading_pair") == trading_pair
        ]
        return filtered_logs[-count:] if filtered_logs else []

    def get_error_logs(self, count: int = 10) -> list:
        """
        获取错误日志

        Args:
            count: 日志数量

        Returns:
            list: 错误日志列表
        """
        error_logs = [
            log for log in self._validation_logs if log.get("event") == "error"
        ]
        return error_logs[-count:] if error_logs else []

    def _update_stage_metrics(
        self, stage_name: str, duration: float, success: bool = True
    ) -> None:
        """
        更新阶段性能指标

        Args:
            stage_name: 阶段名称
            duration: 耗时（秒）
            success: 是否成功
        """
        metrics = self._stage_metrics[stage_name]
        metrics["total_count"] += 1
        metrics["total_duration"] += duration
        metrics["min_duration"] = min(metrics["min_duration"], duration)
        metrics["max_duration"] = max(metrics["max_duration"], duration)

        if not success:
            metrics["error_count"] += 1

    def get_stage_metrics(self, stage_name: Optional[str] = None) -> Dict[str, Any]:
        """
        获取阶段性能指标

        Args:
            stage_name: 阶段名称，如果为None则返回所有阶段的指标

        Returns:
            Dict[str, Any]: 阶段性能指标
        """
        if stage_name:
            if stage_name not in self._stage_metrics:
                return {}

            metrics = self._stage_metrics[stage_name]
            avg_duration = (
                metrics["total_duration"] / metrics["total_count"]
                if metrics["total_count"] > 0
                else 0.0
            )

            return {
                "stage": stage_name,
                "total_count": metrics["total_count"],
                "average_duration": avg_duration,
                "min_duration": (
                    metrics["min_duration"]
                    if metrics["min_duration"] != float("inf")
                    else 0.0
                ),
                "max_duration": metrics["max_duration"],
                "total_duration": metrics["total_duration"],
                "error_count": metrics["error_count"],
                "success_rate": (
                    (metrics["total_count"] - metrics["error_count"])
                    / metrics["total_count"]
                    if metrics["total_count"] > 0
                    else 0.0
                ),
            }

        # 返回所有阶段的指标
        all_metrics = {}
        for stage, metrics in self._stage_metrics.items():
            avg_duration = (
                metrics["total_duration"] / metrics["total_count"]
                if metrics["total_count"] > 0
                else 0.0
            )

            all_metrics[stage] = {
                "total_count": metrics["total_count"],
                "average_duration": avg_duration,
                "min_duration": (
                    metrics["min_duration"]
                    if metrics["min_duration"] != float("inf")
                    else 0.0
                ),
                "max_duration": metrics["max_duration"],
                "total_duration": metrics["total_duration"],
                "error_count": metrics["error_count"],
                "success_rate": (
                    (metrics["total_count"] - metrics["error_count"])
                    / metrics["total_count"]
                    if metrics["total_count"] > 0
                    else 0.0
                ),
            }

        return all_metrics

    def get_performance_metrics(self) -> PerformanceMetrics:
        """
        获取性能指标

        Returns:
            PerformanceMetrics: 性能指标对象
        """
        # 从日志中重新计算性能指标
        total_validations = sum(
            1
            for log in self._validation_logs
            if log.get("event") == "validation_result"
        )

        successful_validations = sum(
            1
            for log in self._validation_logs
            if log.get("event") == "validation_result" and log.get("success")
        )

        # 计算平均响应时间
        processing_times = [
            log.get("processing_time", 0)
            for log in self._validation_logs
            if log.get("event") == "validation_result" and log.get("processing_time")
        ]
        avg_response_time = (
            sum(processing_times) / len(processing_times) if processing_times else 0.0
        )

        # 统计置信度分布
        confidence_distribution = defaultdict(int)
        for log in self._validation_logs:
            if log.get("event") == "validation_result":
                confidence = log.get("confidence", 0.0)
                range_key = self._get_confidence_range(confidence)
                confidence_distribution[range_key] += 1

        # 统计错误类型
        error_counts = defaultdict(int)
        for log in self._validation_logs:
            if log.get("event") == "error":
                error_type = log.get("error_type", "unknown")
                error_counts[error_type] += 1

        return PerformanceMetrics(
            total_validations=total_validations,
            successful_validations=successful_validations,
            failed_validations=total_validations - successful_validations,
            average_response_time=avg_response_time,
            confidence_distribution=dict(confidence_distribution),
            error_counts=dict(error_counts),
            timestamp=datetime.now(),
        )

    def _get_confidence_range(self, confidence: float) -> str:
        """
        获取置信度范围

        Args:
            confidence: 置信度值

        Returns:
            str: 置信度范围标签
        """
        if confidence >= 0.8:
            return "high (0.8-1.0)"
        elif confidence >= 0.6:
            return "medium (0.6-0.8)"
        elif confidence >= 0.4:
            return "low (0.4-0.6)"
        else:
            return "very_low (0.0-0.4)"

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        total_validations = sum(
            1
            for log in self._validation_logs
            if log.get("event") == "validation_result"
        )

        successful_validations = sum(
            1
            for log in self._validation_logs
            if log.get("event") == "validation_result" and log.get("success")
        )

        total_errors = sum(
            1 for log in self._validation_logs if log.get("event") == "error"
        )

        # 计算平均处理时间
        processing_times = [
            log.get("processing_time", 0)
            for log in self._validation_logs
            if log.get("event") == "validation_result" and log.get("processing_time")
        ]
        avg_processing_time = (
            sum(processing_times) / len(processing_times) if processing_times else 0.0
        )

        # 统计决策分布
        decision_counts = defaultdict(int)
        for log in self._validation_logs:
            if log.get("event") == "validation_result":
                decision = log.get("decision")
                if decision:
                    decision_counts[decision] += 1

        # 统计错误类型分布
        error_type_counts = defaultdict(int)
        for log in self._validation_logs:
            if log.get("event") == "error":
                error_type = log.get("error_type")
                if error_type:
                    error_type_counts[error_type] += 1

        # 添加阶段性能指标
        stage_metrics = self.get_stage_metrics()

        return {
            "total_logs": len(self._validation_logs),
            "total_validations": total_validations,
            "successful_validations": successful_validations,
            "failed_validations": total_validations - successful_validations,
            "total_errors": total_errors,
            "success_rate": (
                successful_validations / total_validations
                if total_validations > 0
                else 0.0
            ),
            "average_processing_time": avg_processing_time,
            "decision_distribution": dict(decision_counts),
            "error_type_distribution": dict(error_type_counts),
            "stage_metrics": stage_metrics,
        }

    def get_stage_performance_summary(self) -> Dict[str, Any]:
        """
        获取阶段性能摘要

        Returns:
            Dict[str, Any]: 阶段性能摘要，包括最慢和最快的阶段
        """
        stage_metrics = self.get_stage_metrics()

        if not stage_metrics:
            return {
                "total_stages": 0,
                "slowest_stage": None,
                "fastest_stage": None,
                "total_processing_time": 0.0,
            }

        # 找出最慢和最快的阶段
        slowest_stage = max(
            stage_metrics.items(), key=lambda x: x[1]["average_duration"]
        )

        fastest_stage = min(
            stage_metrics.items(), key=lambda x: x[1]["average_duration"]
        )

        # 计算总处理时间
        total_time = sum(
            metrics["total_duration"] for metrics in stage_metrics.values()
        )

        return {
            "total_stages": len(stage_metrics),
            "slowest_stage": {
                "name": slowest_stage[0],
                "average_duration": slowest_stage[1]["average_duration"],
                "max_duration": slowest_stage[1]["max_duration"],
            },
            "fastest_stage": {
                "name": fastest_stage[0],
                "average_duration": fastest_stage[1]["average_duration"],
                "min_duration": fastest_stage[1]["min_duration"],
            },
            "total_processing_time": total_time,
            "stage_breakdown": {
                stage: {
                    "percentage": (
                        (metrics["total_duration"] / total_time * 100)
                        if total_time > 0
                        else 0.0
                    ),
                    "average_duration": metrics["average_duration"],
                }
                for stage, metrics in stage_metrics.items()
            },
        }

    def get_time_series_metrics(self, time_window_minutes: int = 60) -> Dict[str, Any]:
        """
        获取时间序列指标

        Args:
            time_window_minutes: 时间窗口（分钟）

        Returns:
            Dict[str, Any]: 时间序列指标
        """
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)

        # 过滤时间窗口内的日志
        recent_logs = [
            log
            for log in self._validation_logs
            if log.get("timestamp", datetime.min) >= cutoff_time
        ]

        if not recent_logs:
            return {
                "time_window_minutes": time_window_minutes,
                "total_validations": 0,
                "validations_per_minute": 0.0,
                "average_response_time": 0.0,
                "success_rate": 0.0,
            }

        # 统计验证次数
        validation_logs = [
            log for log in recent_logs if log.get("event") == "validation_result"
        ]

        total_validations = len(validation_logs)
        successful_validations = sum(1 for log in validation_logs if log.get("success"))

        # 计算平均响应时间
        processing_times = [
            log.get("processing_time", 0)
            for log in validation_logs
            if log.get("processing_time")
        ]
        avg_response_time = (
            sum(processing_times) / len(processing_times) if processing_times else 0.0
        )

        return {
            "time_window_minutes": time_window_minutes,
            "total_validations": total_validations,
            "validations_per_minute": total_validations / time_window_minutes,
            "average_response_time": avg_response_time,
            "success_rate": (
                successful_validations / total_validations
                if total_validations > 0
                else 0.0
            ),
            "total_errors": sum(
                1 for log in recent_logs if log.get("event") == "error"
            ),
        }

    def get_detailed_performance_report(self) -> Dict[str, Any]:
        """
        获取详细的性能报告

        Returns:
            Dict[str, Any]: 详细性能报告
        """
        return {
            "overview": self.get_statistics(),
            "stage_metrics": self.get_stage_metrics(),
            "stage_summary": self.get_stage_performance_summary(),
            "recent_activity": {
                "last_hour": self.get_time_series_metrics(60),
                "last_15_minutes": self.get_time_series_metrics(15),
            },
            "performance_metrics": self.get_performance_metrics().__dict__,
        }

    def reset_stage_metrics(self) -> None:
        """重置阶段性能指标"""
        self._stage_metrics.clear()
        logger.info("阶段性能指标已重置")

    def clear_logs(self) -> None:
        """清空所有日志"""
        self._validation_logs.clear()
        logger.info("验证日志已清空")

    def reset_all_metrics(self) -> None:
        """重置所有指标和日志"""
        self._validation_logs.clear()
        self._stage_metrics.clear()
        self._performance_metrics = PerformanceMetrics()
        logger.info("所有监控指标和日志已重置")

    def set_max_log_entries(self, max_entries: int) -> None:
        """
        设置最大日志条目数

        Args:
            max_entries: 最大条目数
        """
        if max_entries > 0:
            self._max_log_entries = max_entries
            # 如果当前日志超过新的限制，进行裁剪
            if len(self._validation_logs) > max_entries:
                self._validation_logs = self._validation_logs[-max_entries:]
            logger.info(f"最大日志条目数已设置为: {max_entries}")
        else:
            raise ValueError("最大日志条目数必须大于0")

    def export_metrics_to_dict(self) -> Dict[str, Any]:
        """
        导出所有指标为字典格式

        Returns:
            Dict[str, Any]: 包含所有指标的字典
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "statistics": self.get_statistics(),
            "stage_metrics": self.get_stage_metrics(),
            "stage_summary": self.get_stage_performance_summary(),
            "performance_metrics": self.get_performance_metrics().__dict__,
            "recent_logs": self.get_recent_logs(20),
            "error_logs": self.get_error_logs(10),
        }
