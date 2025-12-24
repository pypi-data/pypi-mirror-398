# -*- coding: utf-8 -*-
from decimal import Decimal
from typing import Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """验证结果"""

    is_valid: bool
    reason: str = ""
    profit_percent: float = 0.0
    profit_ratio: float = 0.0
    risk_score: float = 0.0


class TargetValidationEngine:
    """
    目标位验证引擎
    负责验证目标位是否满足利润空间、盈亏比等要求
    """

    def __init__(self, config: Dict):
        """
        初始化验证引擎

        Args:
            config: 配置字典
        """
        self.config = config

        # 从配置中获取验证参数
        self.min_profit_percent = config.get("min_profit_percent", 2.0)
        self.min_profit_ratio = config.get("min_profit_ratio", 1.5)
        self.max_risk_percent = config.get("max_risk_percent", 3.0)

    def validate_target(
        self,
        current_price: float,
        target_price: float,
        side: str,
        entry_price: Optional[float] = None,
    ) -> ValidationResult:
        """
        验证目标位是否满足要求

        Args:
            current_price: 当前价格
            target_price: 目标价格
            side: 交易方向 ('buy' or 'sell')
            entry_price: 入场价格（可选，默认使用当前价格）

        Returns:
            ValidationResult: 验证结果
        """
        if entry_price is None:
            entry_price = current_price

        # 第一层：基础利润空间验证
        profit_validation = self._validate_profit_space(entry_price, target_price, side)
        if not profit_validation.is_valid:
            return profit_validation

        # 第二层：盈亏比验证
        ratio_validation = self._validate_profit_ratio(entry_price, target_price, side)
        if not ratio_validation.is_valid:
            return ratio_validation

        # 第三层：风险评估验证
        risk_validation = self._validate_risk_assessment(
            entry_price, target_price, side
        )
        if not risk_validation.is_valid:
            return risk_validation

        # 所有验证通过
        return ValidationResult(
            is_valid=True,
            reason="所有验证通过",
            profit_percent=profit_validation.profit_percent,
            profit_ratio=ratio_validation.profit_ratio,
            risk_score=risk_validation.risk_score,
        )

    def _validate_profit_space(
        self, entry_price: float, target_price: float, side: str
    ) -> ValidationResult:
        """
        验证利润空间是否满足最小要求

        Args:
            entry_price: 入场价格
            target_price: 目标价格
            side: 交易方向

        Returns:
            ValidationResult: 验证结果
        """
        # 计算利润百分比
        if side == "buy":
            if target_price <= entry_price:
                return ValidationResult(
                    is_valid=False, reason="多头目标价格必须高于入场价格"
                )
            profit_percent = (target_price - entry_price) / entry_price * 100
        else:  # sell
            if target_price >= entry_price:
                return ValidationResult(
                    is_valid=False, reason="空头目标价格必须低于入场价格"
                )
            profit_percent = (entry_price - target_price) / entry_price * 100

        # 检查是否满足最小利润空间要求
        if profit_percent < self.min_profit_percent:
            return ValidationResult(
                is_valid=False,
                reason=f"利润空间{profit_percent:.2f}%小于最小要求{self.min_profit_percent}%",
                profit_percent=profit_percent,
            )

        return ValidationResult(
            is_valid=True, reason="利润空间验证通过", profit_percent=profit_percent
        )

    def _validate_profit_ratio(
        self, entry_price: float, target_price: float, side: str
    ) -> ValidationResult:
        """
        验证盈亏比是否满足要求

        Args:
            entry_price: 入场价格
            target_price: 目标价格
            side: 交易方向

        Returns:
            ValidationResult: 验证结果
        """
        # 计算利润距离
        profit_distance = abs(target_price - entry_price)

        # 估算止损距离（简化计算：基于ATR或固定百分比）
        stop_loss_distance = self._estimate_stop_loss_distance(entry_price, side)

        # 计算盈亏比
        if stop_loss_distance <= 0:
            return ValidationResult(is_valid=False, reason="无法计算有效的止损距离")

        profit_ratio = profit_distance / stop_loss_distance

        # 检查是否满足最小盈亏比要求
        if profit_ratio < self.min_profit_ratio:
            return ValidationResult(
                is_valid=False,
                reason=f"盈亏比{profit_ratio:.2f}小于最小要求{self.min_profit_ratio}",
                profit_ratio=profit_ratio,
            )

        return ValidationResult(
            is_valid=True, reason="盈亏比验证通过", profit_ratio=profit_ratio
        )

    def _validate_risk_assessment(
        self, entry_price: float, target_price: float, side: str
    ) -> ValidationResult:
        """
        验证风险评估

        Args:
            entry_price: 入场价格
            target_price: 目标价格
            side: 交易方向

        Returns:
            ValidationResult: 验证结果
        """
        # 计算风险评分（基于价格波动性和市场条件）
        risk_score = self._calculate_risk_score(entry_price, target_price, side)

        # 检查风险是否在可接受范围内
        if risk_score > 0.8:  # 风险评分0-1，0.8为高风险阈值
            return ValidationResult(
                is_valid=False,
                reason=f"风险评分{risk_score:.2f}过高，超过可接受范围",
                risk_score=risk_score,
            )

        return ValidationResult(
            is_valid=True, reason="风险评估通过", risk_score=risk_score
        )

    def _estimate_stop_loss_distance(self, entry_price: float, side: str) -> float:
        """
        估算止损距离

        Args:
            entry_price: 入场价格
            side: 交易方向

        Returns:
            float: 止损距离
        """
        # 简化实现：使用固定百分比作为止损距离
        stop_loss_percent = self.config.get("stop_loss_percent", 1.5)
        return entry_price * stop_loss_percent / 100

    def _calculate_risk_score(
        self, entry_price: float, target_price: float, side: str
    ) -> float:
        """
        计算风险评分

        Args:
            entry_price: 入场价格
            target_price: 目标价格
            side: 交易方向

        Returns:
            float: 风险评分 (0-1, 越高风险越大)
        """
        # 基础风险评分
        base_risk = 0.3

        # 基于价格偏离程度的风险
        price_deviation = abs(target_price - entry_price) / entry_price * 100
        deviation_risk = min(price_deviation / 10.0, 0.5)  # 最大贡献0.5

        # 基于市场条件的风险（简化实现）
        market_risk = 0.2  # 固定市场风险

        total_risk = base_risk + deviation_risk + market_risk
        return min(total_risk, 1.0)

    def validate_multiple_targets(
        self,
        current_price: float,
        targets: list,
        side: str,
        entry_price: Optional[float] = None,
    ) -> Dict[float, ValidationResult]:
        """
        批量验证多个目标位

        Args:
            current_price: 当前价格
            targets: 目标价格列表
            side: 交易方向
            entry_price: 入场价格

        Returns:
            Dict[float, ValidationResult]: 每个目标位的验证结果
        """
        results = {}
        for target in targets:
            results[target] = self.validate_target(
                current_price, target, side, entry_price
            )
        return results

    def get_best_target(
        self, validation_results: Dict[float, ValidationResult]
    ) -> Optional[Tuple[float, ValidationResult]]:
        """
        从验证结果中选择最佳目标位

        Args:
            validation_results: 验证结果字典

        Returns:
            Optional[Tuple[float, ValidationResult]]: 最佳目标位和其验证结果
        """
        valid_targets = {
            price: result
            for price, result in validation_results.items()
            if result.is_valid
        }

        if not valid_targets:
            return None

        # 选择综合评分最高的目标位
        best_price = None
        best_score = -1

        for price, result in valid_targets.items():
            # 综合评分 = 利润百分比 * 盈亏比 * (1 - 风险评分)
            score = (
                result.profit_percent * result.profit_ratio * (1 - result.risk_score)
            )
            if score > best_score:
                best_score = score
                best_price = price

        return (best_price, valid_targets[best_price]) if best_price else None
