"""
形态识别器

集成现有的等高等低识别算法，并将结果格式化为AI模型输入。
"""

import logging
from typing import List
import pandas as pd

from .data_models import (
    MarketData,
    PatternCandidate,
    AIInputData,
    PatternType,
    Point,
)
from .exceptions import PatternRecognitionError
from datetime import datetime

logger = logging.getLogger(__name__)


class PatternRecognizer:
    """形态识别器 - 集成SMCLiquidity算法识别等高等低形态"""

    def __init__(self, existing_algorithm=None):
        """
        初始化形态识别器

        Args:
            existing_algorithm: 现有的等高等低识别算法（SMCLiquidity实例）
        """
        self.algorithm = existing_algorithm

        # 如果没有提供算法实例，尝试导入并创建
        if self.algorithm is None:
            try:
                from core.smc.SMCLiquidity import SMCLiquidity

                self.algorithm = SMCLiquidity()
                logger.info("自动创建SMCLiquidity算法实例")
            except ImportError as e:
                logger.warning(f"无法导入SMCLiquidity: {e}，将使用模拟模式")
                self.algorithm = None

        logger.info("形态识别器初始化完成")

    def identify_patterns(
        self, market_data: MarketData, atr_offset: float = 0.1, lookback: int = 1, 
        existing_equal_points_df: pd.DataFrame = None
    ) -> List[PatternCandidate]:
        """
        识别等高等低形态候选（集成SMCLiquidity算法）

        Args:
            market_data: 市场数据
            atr_offset: ATR偏移量，用于计算容差（默认0.1）
            lookback: swing point验证的lookback周期（默认1）
            existing_equal_points_df: 已识别的等高等低点DataFrame（可选，如果提供则直接使用）

        Returns:
            List[PatternCandidate]: 形态候选列表
        """
        try:
            logger.debug(f"开始识别形态: {market_data.trading_pair}")

            # 如果提供了已识别的等高等低点DataFrame，直接使用
            if existing_equal_points_df is not None:
                logger.info(f"使用已识别的等高等低点数据，共 {len(existing_equal_points_df)} 行")
                patterns = self._extract_patterns_from_existing_data(existing_equal_points_df)
                logger.info(
                    f"从已有数据中提取到 {len(patterns)} 个形态候选: {market_data.trading_pair}"
                )
                return patterns

            # 如果没有算法实例，使用模拟模式
            if self.algorithm is None:
                logger.warning("未提供SMCLiquidity算法实例，使用模拟模式")
                patterns = self._generate_mock_patterns(market_data)
                logger.info(
                    f"识别到 {len(patterns)} 个形态候选（模拟模式）: {market_data.trading_pair}"
                )
                return patterns

            # 将MarketData转换为DataFrame格式
            df = self._convert_market_data_to_dataframe(market_data)

            # 计算ATR（如果还没有）
            if "atr" not in df.columns:
                df = self.algorithm.calculate_atr(df)

            # 识别流动性枢轴点
            df = self.algorithm._identify_liquidity_pivots(df, pivot_length=lookback)

            patterns = []

            # 识别等高点（bullish trend）
            try:
                high_patterns = self._identify_equal_highs(df, atr_offset, lookback)
                patterns.extend(high_patterns)
                logger.debug(f"识别到 {len(high_patterns)} 个等高点形态")
            except Exception as e:
                logger.warning(f"识别等高点时出错: {e}")

            # 识别等低点（bearish trend）
            try:
                low_patterns = self._identify_equal_lows(df, atr_offset, lookback)
                patterns.extend(low_patterns)
                logger.debug(f"识别到 {len(low_patterns)} 个等低点形态")
            except Exception as e:
                logger.warning(f"识别等低点时出错: {e}")

            logger.info(
                f"识别到 {len(patterns)} 个形态候选: {market_data.trading_pair}"
            )
            return patterns

        except Exception as e:
            logger.error(f"形态识别失败: {market_data.trading_pair}, 错误: {str(e)}")
            raise PatternRecognitionError(
                f"形态识别失败: {market_data.trading_pair}, 错误: {str(e)}"
            )



    def _extract_patterns_from_existing_data(
        self, df_equal_liquidity: pd.DataFrame
    ) -> List[PatternCandidate]:
        """从已识别的等高等低点DataFrame中提取形态候选"""
        patterns = []
        
        try:
            # 筛选有等高等低点的行
            df_with_equal_points = df_equal_liquidity[
                df_equal_liquidity.get("has_equal_points", False)
            ]
            
            if df_with_equal_points.empty:
                logger.debug("没有找到has_equal_points=True的记录")
                return patterns
            
            logger.debug(f"找到 {len(df_with_equal_points)} 个has_equal_points=True的记录")
            
            # 按高点/低点分组处理（将equal_low和extreme_low归为一组，equal_high和extreme_high归为一组）
            for point_category in ["low", "high"]:
                # 筛选包含该类别的所有记录
                category_df = df_with_equal_points[
                    df_with_equal_points["equal_points_type"].str.contains(point_category, case=False, na=False)
                ]
                
                if category_df.empty:
                    continue
                
                # 提取点位信息
                points = []
                for idx, row in category_df.iterrows():
                    timestamp = row.get("timestamp", row.name)
                    if not isinstance(timestamp, datetime):
                        timestamp = pd.to_datetime(timestamp)
                    
                    # 根据类型选择价格
                    if point_category == "high":
                        price = float(row.get("equal_points_price", row.get("high", 0)))
                    else:
                        price = float(row.get("equal_points_price", row.get("low", 0)))
                    
                    point = Point(
                        timestamp=timestamp,
                        price=price,
                        volume=float(row.get("volume", 0)),
                        index=int(idx) if isinstance(idx, int) else 0,
                    )
                    points.append(point)
                
                if len(points) >= 2:
                    # 按时间排序
                    points.sort(key=lambda p: p.timestamp)
                    
                    # 确定形态类型
                    pattern_type = PatternType.EQUAL_HIGH if point_category == "high" else PatternType.EQUAL_LOW
                    
                    # 创建形态候选
                    pattern = PatternCandidate(
                        pattern_type=pattern_type,
                        points=points,
                        confidence=0.85,  # 基于已验证数据的高置信度
                        timeframe="unknown",
                        start_time=points[0].timestamp,
                        end_time=points[-1].timestamp,
                        metadata={
                            "point_category": point_category,
                            "point_count": len(points),
                            "source": "existing_data",
                            "equal_points_price": float(category_df.iloc[0].get("equal_points_price", 0)),
                        },
                    )
                    patterns.append(pattern)
                    logger.debug(
                        f"创建形态候选: {pattern_type.value}, 包含 {len(points)} 个点"
                    )
        
        except Exception as e:
            logger.error(f"从已有数据提取形态时出错: {e}", exc_info=True)
        
        return patterns

    def _convert_market_data_to_dataframe(
        self, market_data: MarketData
    ) -> pd.DataFrame:
        """将MarketData转换为DataFrame格式供SMCLiquidity使用"""
        try:
            data = []
            for candle in market_data.candles:
                data.append(
                    {
                        "timestamp": candle.timestamp,
                        "open": float(candle.open),
                        "high": float(candle.high),
                        "low": float(candle.low),
                        "close": float(candle.close),
                        "volume": float(candle.volume),
                    }
                )

            df = pd.DataFrame(data)

            # 确保timestamp列是datetime类型
            if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
                df["timestamp"] = pd.to_datetime(df["timestamp"])

            # Keep timestamp as a column (don't set as index) because SMCLiquidity expects it as a column
            logger.debug(f"成功转换MarketData为DataFrame，共 {len(df)} 行")
            return df

        except Exception as e:
            logger.error(f"转换MarketData为DataFrame失败: {e}")
            raise PatternRecognitionError(f"数据转换失败: {e}")

    def _identify_equal_highs(
        self, df: pd.DataFrame, atr_offset: float, lookback: int
    ) -> List[PatternCandidate]:
        """识别等高点形态"""
        patterns = []

        try:
            # 使用SMCLiquidity的find_EQH_EQL方法识别等高点
            result = self.algorithm.find_EQH_EQL(
                df,
                trend=self.algorithm.BULLISH_TREND,  # 等高点对应bullish趋势
                atr_offset=atr_offset,
            )

            # 如果找到等高点
            if result.get(self.algorithm.HAS_EQ_KEY, False):
                equal_high_value = result.get(self.algorithm.EQUAL_HIGH_COL)
                equal_high_index = result.get(self.algorithm.EQUAL_HIGH_INDEX_KEY)

                if equal_high_value is not None and equal_high_index is not None:
                    # 查找所有等高点
                    equal_high_points = self._extract_equal_points_from_dataframe(
                        df, equal_high_index, point_type="high"
                    )

                    if len(equal_high_points) >= 2:
                        pattern = PatternCandidate(
                            pattern_type=PatternType.EQUAL_HIGH,
                            points=equal_high_points,
                            confidence=0.8,  # 基于SMC算法的置信度
                            timeframe="unknown",  # 可以从market_data中获取
                            start_time=equal_high_points[0].timestamp,
                            end_time=equal_high_points[-1].timestamp,
                            metadata={
                                "equal_high_value": float(equal_high_value),
                                "equal_high_index": str(equal_high_index),
                                "atr_offset": atr_offset,
                                "algorithm": "SMCLiquidity",
                            },
                        )
                        patterns.append(pattern)
                        logger.debug(
                            f"识别到等高点形态，包含 {len(equal_high_points)} 个点"
                        )

        except Exception as e:
            logger.warning(f"识别等高点时出错: {e}")

        return patterns

    def _identify_equal_lows(
        self, df: pd.DataFrame, atr_offset: float, lookback: int
    ) -> List[PatternCandidate]:
        """识别等低点形态"""
        patterns = []

        try:
            # 使用SMCLiquidity的find_EQH_EQL方法识别等低点
            result = self.algorithm.find_EQH_EQL(
                df,
                trend=self.algorithm.BEARISH_TREND,  # 等低点对应bearish趋势
                atr_offset=atr_offset,
            )

            # 如果找到等低点
            if result.get(self.algorithm.HAS_EQ_KEY, False):
                equal_low_value = result.get(self.algorithm.EQUAL_LOW_COL)
                equal_low_index = result.get(self.algorithm.EQUAL_LOW_INDEX_KEY)

                if equal_low_value is not None and equal_low_index is not None:
                    # 查找所有等低点
                    equal_low_points = self._extract_equal_points_from_dataframe(
                        df, equal_low_index, point_type="low"
                    )

                    if len(equal_low_points) >= 2:
                        pattern = PatternCandidate(
                            pattern_type=PatternType.EQUAL_LOW,
                            points=equal_low_points,
                            confidence=0.8,  # 基于SMC算法的置信度
                            timeframe="unknown",  # 可以从market_data中获取
                            start_time=equal_low_points[0].timestamp,
                            end_time=equal_low_points[-1].timestamp,
                            metadata={
                                "equal_low_value": float(equal_low_value),
                                "equal_low_index": str(equal_low_index),
                                "atr_offset": atr_offset,
                                "algorithm": "SMCLiquidity",
                            },
                        )
                        patterns.append(pattern)
                        logger.debug(
                            f"识别到等低点形态，包含 {len(equal_low_points)} 个点"
                        )

        except Exception as e:
            logger.warning(f"识别等低点时出错: {e}")

        return patterns

    def _extract_equal_points_from_dataframe(
        self, df: pd.DataFrame, equal_index, point_type: str
    ) -> List[Point]:
        """从DataFrame中提取等高/等低点"""
        points = []

        try:
            # 根据点类型选择列名
            if point_type == "high":
                equal_col = self.algorithm.EQUAL_HIGH_COL
                price_col = self.algorithm.LIQU_HIGH_COL
            else:
                equal_col = self.algorithm.EQUAL_LOW_COL
                price_col = self.algorithm.LIQU_LOW_COL

            # 查找所有标记为等点的行
            if equal_col in df.columns:
                equal_points_df = df[df[equal_col] == equal_index]

                for idx, row in equal_points_df.iterrows():
                    price_value = (
                        row[price_col]
                        if price_col in row
                        else (row["high"] if point_type == "high" else row["low"])
                    )

                    # Get timestamp from the row since it's a column, not the index
                    timestamp = row.get("timestamp", row.name)
                    if not isinstance(timestamp, datetime):
                        timestamp = pd.to_datetime(timestamp)

                    point = Point(
                        timestamp=timestamp,
                        price=float(price_value),
                        volume=float(row.get("volume", 0)),
                        index=int(idx),  # Use the integer index position
                    )
                    points.append(point)

                # 按时间排序
                points.sort(key=lambda p: p.timestamp)

        except Exception as e:
            logger.error(f"提取等点时出错: {e}", exc_info=True)

        return points

    def _generate_mock_patterns(
        self, market_data: MarketData
    ) -> List[PatternCandidate]:
        """生成模拟形态候选（用于测试）"""
        patterns = []

        if len(market_data.candles) < 10:
            return patterns

        # 模拟一个等高点形态
        candles = market_data.candles[-20:]  # 取最近20根K线

        # 找到相对高点
        high_points = []
        for i in range(2, len(candles) - 2):
            if (
                candles[i].high > candles[i - 1].high
                and candles[i].high > candles[i - 2].high
                and candles[i].high > candles[i + 1].high
                and candles[i].high > candles[i + 2].high
            ):
                high_points.append(
                    Point(
                        timestamp=candles[i].timestamp,
                        price=candles[i].high,
                        volume=candles[i].volume,
                        index=i,
                    )
                )

        # 如果找到多个高点，创建等高点形态
        if len(high_points) >= 2:
            # 检查是否为等高点（价格差异小于1%）
            for i in range(len(high_points) - 1):
                price_diff = abs(high_points[i].price - high_points[i + 1].price)
                price_avg = (high_points[i].price + high_points[i + 1].price) / 2

                if price_diff / price_avg < 0.01:  # 1%的容差
                    pattern = PatternCandidate(
                        pattern_type=PatternType.EQUAL_HIGH,
                        points=[high_points[i], high_points[i + 1]],
                        confidence=0.75,  # 模拟置信度
                        timeframe="1h",
                        start_time=high_points[i].timestamp,
                        end_time=high_points[i + 1].timestamp,
                        metadata={
                            "price_difference": price_diff,
                            "price_average": price_avg,
                            "relative_difference": price_diff / price_avg,
                        },
                    )
                    patterns.append(pattern)

        return patterns

    def format_for_ai(
        self, patterns: List[PatternCandidate], market_data: MarketData
    ) -> AIInputData:
        """
        将形态数据转换为AI模型输入格式

        实现数据标准化和特征提取，为AI模型提供结构化的输入数据

        Args:
            patterns: 形态候选列表
            market_data: 市场数据

        Returns:
            AIInputData: AI输入数据，包含标准化的市场数据、形态候选和额外特征
        """
        try:
            logger.debug("开始格式化AI输入数据")

            # 提取额外特征
            additional_features = self._extract_additional_features(market_data)

            # 为每个形态添加标准化特征
            normalized_patterns = self._normalize_pattern_features(
                patterns, market_data
            )

            # 添加形态间的关系特征
            pattern_relationship_features = self._extract_pattern_relationships(
                normalized_patterns
            )
            additional_features["pattern_relationships"] = pattern_relationship_features

            # 添加市场环境特征
            market_context_features = self._extract_market_context(market_data)
            additional_features["market_context"] = market_context_features

            # 创建AI输入数据对象
            ai_input = AIInputData(
                market_data=market_data,
                pattern_candidates=normalized_patterns,
                additional_features=additional_features,
            )

            logger.debug(
                f"AI输入数据格式化完成，包含 {len(normalized_patterns)} 个形态候选"
            )
            return ai_input

        except Exception as e:
            logger.error(f"AI输入数据格式化失败: {e}")
            raise PatternRecognitionError(f"AI输入数据格式化失败: {str(e)}")

    def _normalize_pattern_features(
        self, patterns: List[PatternCandidate], market_data: MarketData
    ) -> List[PatternCandidate]:
        """为每个形态添加标准化特征"""
        normalized_patterns = []

        for pattern in patterns:
            # 复制原始形态
            normalized_pattern = pattern

            # 计算形态的标准化特征
            pattern_features = {
                "point_count": len(pattern.points),
                "time_span_seconds": (
                    pattern.end_time - pattern.start_time
                ).total_seconds(),
                "price_range": self._calculate_pattern_price_range(pattern),
                "price_range_normalized": self._normalize_price_range(
                    pattern, market_data
                ),
                "volume_profile": self._calculate_volume_profile(pattern),
                "pattern_strength": self._calculate_pattern_strength(
                    pattern, market_data
                ),
            }

            # 将特征添加到metadata中
            normalized_pattern.metadata.update(pattern_features)
            normalized_patterns.append(normalized_pattern)

        return normalized_patterns

    def _calculate_pattern_price_range(self, pattern: PatternCandidate) -> float:
        """计算形态的价格范围"""
        if not pattern.points:
            return 0.0

        prices = [p.price for p in pattern.points]
        return max(prices) - min(prices)

    def _normalize_price_range(
        self, pattern: PatternCandidate, market_data: MarketData
    ) -> float:
        """标准化价格范围（相对于市场价格）"""
        if not pattern.points or not market_data.candles:
            return 0.0

        pattern_range = self._calculate_pattern_price_range(pattern)
        avg_price = sum(p.price for p in pattern.points) / len(pattern.points)

        if avg_price == 0:
            return 0.0

        return pattern_range / avg_price

    def _calculate_volume_profile(self, pattern: PatternCandidate) -> dict:
        """计算形态的成交量特征"""
        if not pattern.points:
            return {"avg_volume": 0.0, "total_volume": 0.0, "volume_trend": 0.0}

        volumes = [p.volume for p in pattern.points]
        total_volume = sum(volumes)
        avg_volume = total_volume / len(volumes) if volumes else 0.0

        # 计算成交量趋势（前半部分vs后半部分）
        volume_trend = 0.0
        if len(volumes) >= 2:
            mid = len(volumes) // 2
            first_half_avg = sum(volumes[:mid]) / mid if mid > 0 else 0.0
            second_half_avg = (
                sum(volumes[mid:]) / (len(volumes) - mid)
                if (len(volumes) - mid) > 0
                else 0.0
            )

            if first_half_avg > 0:
                volume_trend = (second_half_avg - first_half_avg) / first_half_avg

        return {
            "avg_volume": avg_volume,
            "total_volume": total_volume,
            "volume_trend": volume_trend,
        }

    def _calculate_pattern_strength(
        self, pattern: PatternCandidate, market_data: MarketData
    ) -> float:
        """计算形态强度（综合指标）"""
        # 基于多个因素计算形态强度：
        # 1. 点的数量（更多点 = 更强）
        # 2. 价格一致性（价格差异越小 = 更强）
        # 3. 时间跨度（适中的时间跨度 = 更强）

        if not pattern.points or len(pattern.points) < 2:
            return 0.0

        # 点数量得分（归一化到0-1）
        point_score = min(len(pattern.points) / 5.0, 1.0)  # 5个点或以上得满分

        # 价格一致性得分
        prices = [p.price for p in pattern.points]
        avg_price = sum(prices) / len(prices)
        price_std = (sum((p - avg_price) ** 2 for p in prices) / len(prices)) ** 0.5
        price_consistency_score = (
            1.0 - min(price_std / avg_price, 1.0) if avg_price > 0 else 0.0
        )

        # 时间跨度得分（假设理想时间跨度为1小时到24小时）
        time_span_hours = (pattern.end_time - pattern.start_time).total_seconds() / 3600
        if time_span_hours < 1:
            time_score = time_span_hours  # 小于1小时，线性增长
        elif time_span_hours <= 24:
            time_score = 1.0  # 1-24小时，满分
        else:
            time_score = max(
                0.5, 1.0 - (time_span_hours - 24) / 48
            )  # 超过24小时，逐渐降低

        # 综合得分（加权平均）
        strength = point_score * 0.3 + price_consistency_score * 0.5 + time_score * 0.2

        return strength

    def _extract_pattern_relationships(self, patterns: List[PatternCandidate]) -> dict:
        """提取形态间的关系特征"""
        relationships = {
            "total_patterns": len(patterns),
            "equal_high_count": sum(
                1 for p in patterns if p.pattern_type == PatternType.EQUAL_HIGH
            ),
            "equal_low_count": sum(
                1 for p in patterns if p.pattern_type == PatternType.EQUAL_LOW
            ),
            "overlapping_patterns": 0,
            "time_gaps": [],
        }

        # 检查形态重叠
        for i in range(len(patterns)):
            for j in range(i + 1, len(patterns)):
                if self._patterns_overlap(patterns[i], patterns[j]):
                    relationships["overlapping_patterns"] += 1

        # 计算形态间的时间间隔
        if len(patterns) >= 2:
            sorted_patterns = sorted(patterns, key=lambda p: p.start_time)
            for i in range(len(sorted_patterns) - 1):
                gap = (
                    sorted_patterns[i + 1].start_time - sorted_patterns[i].end_time
                ).total_seconds()
                relationships["time_gaps"].append(gap)

        return relationships

    def _patterns_overlap(
        self, pattern1: PatternCandidate, pattern2: PatternCandidate
    ) -> bool:
        """检查两个形态是否在时间上重叠"""
        return not (
            pattern1.end_time < pattern2.start_time
            or pattern2.end_time < pattern1.start_time
        )

    def _extract_market_context(self, market_data: MarketData) -> dict:
        """提取市场环境特征"""
        context = {
            "total_candles": len(market_data.candles),
            "time_range_hours": 0.0,
            "price_range": 0.0,
            "price_range_pct": 0.0,
            "avg_volume": 0.0,
            "current_price": 0.0,
            "trend_direction": "neutral",
        }

        if not market_data.candles:
            return context

        # 时间范围
        if len(market_data.candles) >= 2:
            time_range = (
                market_data.candles[-1].timestamp - market_data.candles[0].timestamp
            )
            context["time_range_hours"] = time_range.total_seconds() / 3600

        # 价格范围
        highs = [c.high for c in market_data.candles]
        lows = [c.low for c in market_data.candles]
        max_high = max(highs)
        min_low = min(lows)
        context["price_range"] = max_high - min_low

        avg_price = (max_high + min_low) / 2
        if avg_price > 0:
            context["price_range_pct"] = context["price_range"] / avg_price

        # 平均成交量
        volumes = [c.volume for c in market_data.candles]
        context["avg_volume"] = sum(volumes) / len(volumes) if volumes else 0.0

        # 当前价格
        context["current_price"] = market_data.candles[-1].close

        # 趋势方向（简单判断：首尾价格比较）
        if len(market_data.candles) >= 10:
            first_price = market_data.candles[0].close
            last_price = market_data.candles[-1].close
            price_change_pct = (
                (last_price - first_price) / first_price if first_price > 0 else 0.0
            )

            if price_change_pct > 0.02:  # 上涨超过2%
                context["trend_direction"] = "bullish"
            elif price_change_pct < -0.02:  # 下跌超过2%
                context["trend_direction"] = "bearish"
            else:
                context["trend_direction"] = "neutral"

        return context

    def _extract_additional_features(self, market_data: MarketData) -> dict:
        """提取额外特征"""
        features = {}

        if market_data.candles:
            recent_candles = market_data.candles[-10:]  # 最近10根K线

            # 价格特征
            features["price_volatility"] = self._calculate_volatility(recent_candles)
            features["volume_trend"] = self._calculate_volume_trend(recent_candles)
            features["price_trend"] = self._calculate_price_trend(recent_candles)

        return features

    def _calculate_volatility(self, candles) -> float:
        """计算价格波动率"""
        if len(candles) < 2:
            return 0.0

        returns = []
        for i in range(1, len(candles)):
            ret = (candles[i].close - candles[i - 1].close) / candles[i - 1].close
            returns.append(ret)

        if not returns:
            return 0.0

        mean_return = sum(returns) / len(returns)
        variance = sum([(r - mean_return) ** 2 for r in returns]) / len(returns)
        return variance**0.5

    def _calculate_volume_trend(self, candles) -> float:
        """计算成交量趋势"""
        if len(candles) < 2:
            return 0.0

        volumes = [c.volume for c in candles]
        first_half = volumes[: len(volumes) // 2]
        second_half = volumes[len(volumes) // 2 :]

        if not first_half or not second_half:
            return 0.0

        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)

        if avg_first == 0:
            return 0.0

        return (avg_second - avg_first) / avg_first

    def _calculate_price_trend(self, candles) -> float:
        """计算价格趋势"""
        if len(candles) < 2:
            return 0.0

        first_price = candles[0].close
        last_price = candles[-1].close

        if first_price == 0:
            return 0.0

        return (last_price - first_price) / first_price
