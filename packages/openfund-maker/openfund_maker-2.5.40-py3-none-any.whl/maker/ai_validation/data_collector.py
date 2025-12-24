"""
数据收集器

负责收集验证所需的市场数据和技术指标。
"""

import logging
import pandas as pd
from typing import List, Optional
from datetime import datetime, timedelta

from .data_models import MarketData, OHLCV, TechnicalIndicators
from .exceptions import DataCollectionError, InsufficientDataError
from core.Exchange import Exchange

logger = logging.getLogger(__name__)


class DataCollector:
    """数据收集器"""

    def __init__(self, exchange: Optional[Exchange] = None):
        """
        初始化数据收集器

        Args:
            exchange: Exchange实例，如果为None则需要在调用时提供
        """
        self.exchange = exchange
        self._cache = {}
        self._cache_ttl = 300  # 5分钟缓存

    def collect_market_data(
        self,
        trading_pair: str,
        candle_count: int = 200,
        timeframe: str = "15m",
        exchange: Optional[Exchange] = None,
    ) -> MarketData:
        """
        收集指定交易对的市场数据

        Args:
            trading_pair: 交易对
            candle_count: K线数量
            timeframe: 时间周期，默认15分钟
            exchange: Exchange实例，如果为None则使用初始化时的exchange

        Returns:
            MarketData: 市场数据
        """
        try:
            logger.debug(
                f"开始收集市场数据: {trading_pair}, 数量: {candle_count}, 周期: {timeframe}"
            )

            # 使用提供的exchange或初始化时的exchange
            current_exchange = exchange or self.exchange
            if not current_exchange:
                raise DataCollectionError(
                    "未提供Exchange实例", trading_pair=trading_pair
                )

            # 检查缓存
            cache_key = f"{trading_pair}_{candle_count}_{timeframe}"
            cached_data = self._get_cached_data(cache_key)
            if cached_data:
                logger.debug(f"使用缓存数据: {trading_pair}")
                return cached_data

            # 收集K线数据
            candles = self._fetch_candles(
                trading_pair, candle_count, timeframe, current_exchange
            )

            if len(candles) < candle_count:
                logger.warning(
                    f"K线数据不足: {trading_pair}, 需要: {candle_count}, 实际: {len(candles)}"
                )
                if len(candles) < 50:  # 最少需要50根K线
                    raise InsufficientDataError(
                        f"K线数据不足，无法进行分析: {trading_pair}",
                        trading_pair=trading_pair,
                        required_count=candle_count,
                        actual_count=len(candles),
                    )

            # 计算技术指标
            technical_indicators = self.collect_technical_indicators(candles)

            # 创建市场数据对象
            market_data = MarketData(
                trading_pair=trading_pair,
                candles=candles,
                timestamp=datetime.now(),
                technical_indicators=technical_indicators,
            )

            # 缓存数据
            self._cache_data(cache_key, market_data)

            logger.info(f"市场数据收集完成: {trading_pair}, K线数量: {len(candles)}")
            return market_data

        except Exception as e:
            if isinstance(e, (DataCollectionError, InsufficientDataError)):
                raise
            raise DataCollectionError(
                f"收集市场数据失败: {trading_pair}, 错误: {str(e)}",
                trading_pair=trading_pair,
            )

    def _fetch_candles(
        self, trading_pair: str, count: int, timeframe: str, exchange: Exchange
    ) -> List[OHLCV]:
        """
        获取K线数据，集成现有的Exchange接口

        Args:
            trading_pair: 交易对
            count: K线数量
            timeframe: 时间周期
            exchange: Exchange实例
        """
        try:
            logger.debug(
                f"获取K线数据: {trading_pair}, 数量: {count}, 周期: {timeframe}"
            )

            # 使用现有的Exchange接口获取历史K线数据
            klines_df = exchange.get_historical_klines_df(
                symbol=trading_pair, bar=timeframe, limit=count
            )

            if klines_df.empty:
                raise DataCollectionError(f"未获取到K线数据: {trading_pair}")

            # 转换DataFrame为OHLCV对象列表
            candles = []
            for _, row in klines_df.iterrows():
                candle = OHLCV(
                    timestamp=row["timestamp"].to_pydatetime(),
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["volume"]),
                )
                candles.append(candle)

            logger.debug(f"成功获取K线数据: {trading_pair}, 实际数量: {len(candles)}")
            return candles

        except Exception as e:
            logger.error(f"获取K线数据失败: {trading_pair}, 错误: {str(e)}")
            raise DataCollectionError(
                f"获取K线数据失败: {trading_pair}, 错误: {str(e)}",
                trading_pair=trading_pair,
            )

    def collect_technical_indicators(
        self, candles: List[OHLCV], use_cache: bool = True
    ) -> TechnicalIndicators:
        """
        计算技术指标，支持缓存机制

        Args:
            candles: K线数据
            use_cache: 是否使用缓存

        Returns:
            TechnicalIndicators: 技术指标
        """
        try:
            logger.debug(f"计算技术指标，K线数量: {len(candles)}")

            if len(candles) < 20:
                logger.warning("K线数据不足，跳过技术指标计算")
                return TechnicalIndicators()

            # 生成缓存键（基于最后几根K线的哈希值）
            cache_key = None
            if use_cache:
                cache_key = self._generate_indicators_cache_key(candles)
                cached_indicators = self._get_cached_indicators(cache_key)
                if cached_indicators:
                    logger.debug("使用缓存的技术指标")
                    return cached_indicators

            # 提取价格数据
            closes = [candle.close for candle in candles]
            highs = [candle.high for candle in candles]
            lows = [candle.low for candle in candles]
            volumes = [candle.volume for candle in candles]

            # 计算各种技术指标
            indicators = TechnicalIndicators()

            # RSI
            indicators.rsi = self._calculate_rsi(closes)

            # MACD
            indicators.macd = self._calculate_macd(closes)

            # EMA
            indicators.ema = {
                "ema_12": self._calculate_ema(closes, 12),
                "ema_26": self._calculate_ema(closes, 26),
                "ema_50": self._calculate_ema(closes, 50),
            }

            # SMA
            indicators.sma = {
                "sma_20": self._calculate_sma(closes, 20),
                "sma_50": self._calculate_sma(closes, 50),
            }

            # 布林带
            indicators.bollinger_bands = self._calculate_bollinger_bands(closes)

            # ATR
            indicators.atr = self._calculate_atr(highs, lows, closes)

            # 成交量相关指标
            indicators.volume_sma = self._calculate_volume_sma(volumes)

            # 缓存计算结果
            if use_cache and cache_key:
                self._cache_indicators(cache_key, indicators)

            logger.debug("技术指标计算完成")
            return indicators

        except Exception as e:
            logger.error(f"技术指标计算失败: {str(e)}")
            return TechnicalIndicators()

    def _calculate_rsi(self, prices: List[float], period: int = 14) -> List[float]:
        """计算RSI"""
        if len(prices) < period + 1:
            return []

        deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
        gains = [delta if delta > 0 else 0 for delta in deltas]
        losses = [-delta if delta < 0 else 0 for delta in deltas]

        avg_gain = sum(gains[:period]) / period
        avg_loss = sum(losses[:period]) / period

        rsi_values = []

        for i in range(period, len(deltas)):
            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))

            rsi_values.append(rsi)

            # 更新平均值
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period

        return rsi_values

    def _calculate_macd(self, prices: List[float]) -> dict:
        """计算MACD"""
        if len(prices) < 26:
            return {"macd": [], "signal": [], "histogram": []}

        ema_12 = self._calculate_ema(prices, 12)
        ema_26 = self._calculate_ema(prices, 26)

        # MACD线
        macd_line = []
        for i in range(len(ema_26)):
            if i < len(ema_12):
                macd_line.append(ema_12[i] - ema_26[i])

        # 信号线（MACD的9日EMA）
        signal_line = self._calculate_ema(macd_line, 9)

        # 柱状图
        histogram = []
        for i in range(len(signal_line)):
            if i < len(macd_line):
                histogram.append(macd_line[i] - signal_line[i])

        return {"macd": macd_line, "signal": signal_line, "histogram": histogram}

    def _calculate_ema(self, prices: List[float], period: int) -> List[float]:
        """计算EMA"""
        if len(prices) < period:
            return []

        multiplier = 2 / (period + 1)
        ema_values = [sum(prices[:period]) / period]  # 第一个值用SMA

        for i in range(period, len(prices)):
            ema = (prices[i] * multiplier) + (ema_values[-1] * (1 - multiplier))
            ema_values.append(ema)

        return ema_values

    def _calculate_sma(self, prices: List[float], period: int) -> List[float]:
        """计算SMA"""
        if len(prices) < period:
            return []

        sma_values = []
        for i in range(period - 1, len(prices)):
            sma = sum(prices[i - period + 1 : i + 1]) / period
            sma_values.append(sma)

        return sma_values

    def _calculate_bollinger_bands(
        self, prices: List[float], period: int = 20, std_dev: float = 2
    ) -> dict:
        """计算布林带"""
        if len(prices) < period:
            return {"upper": [], "middle": [], "lower": []}

        sma_values = self._calculate_sma(prices, period)

        upper_band = []
        lower_band = []

        for i in range(len(sma_values)):
            price_slice = prices[i : i + period]
            std = (sum([(p - sma_values[i]) ** 2 for p in price_slice]) / period) ** 0.5

            upper_band.append(sma_values[i] + (std_dev * std))
            lower_band.append(sma_values[i] - (std_dev * std))

        return {"upper": upper_band, "middle": sma_values, "lower": lower_band}

    def _calculate_atr(
        self,
        highs: List[float],
        lows: List[float],
        closes: List[float],
        period: int = 14,
    ) -> List[float]:
        """计算ATR"""
        if len(highs) < period + 1:
            return []

        true_ranges = []
        for i in range(1, len(highs)):
            tr1 = highs[i] - lows[i]
            tr2 = abs(highs[i] - closes[i - 1])
            tr3 = abs(lows[i] - closes[i - 1])
            true_ranges.append(max(tr1, tr2, tr3))

        atr_values = []
        atr = sum(true_ranges[:period]) / period
        atr_values.append(atr)

        for i in range(period, len(true_ranges)):
            atr = (atr * (period - 1) + true_ranges[i]) / period
            atr_values.append(atr)

        return atr_values

    def _calculate_volume_sma(
        self, volumes: List[float], period: int = 20
    ) -> List[float]:
        """计算成交量简单移动平均"""
        if len(volumes) < period:
            return []

        volume_sma = []
        for i in range(period - 1, len(volumes)):
            sma = sum(volumes[i - period + 1 : i + 1]) / period
            volume_sma.append(sma)

        return volume_sma

    def _generate_indicators_cache_key(self, candles: List[OHLCV]) -> str:
        """生成技术指标缓存键"""
        # 使用最后10根K线的时间戳和收盘价生成哈希
        if len(candles) < 10:
            return ""

        recent_candles = candles[-10:]
        key_data = []
        for candle in recent_candles:
            key_data.append(f"{candle.timestamp.isoformat()}_{candle.close}")

        import hashlib

        key_string = "_".join(key_data)
        return f"indicators_{hashlib.md5(key_string.encode()).hexdigest()}"

    def _get_cached_indicators(self, cache_key: str) -> Optional[TechnicalIndicators]:
        """获取缓存的技术指标"""
        if not cache_key or cache_key not in self._cache:
            return None

        cached_item = self._cache[cache_key]
        if datetime.now() - cached_item["timestamp"] < timedelta(
            seconds=self._cache_ttl
        ):
            return cached_item["data"]
        else:
            del self._cache[cache_key]
            return None

    def _cache_indicators(
        self, cache_key: str, indicators: TechnicalIndicators
    ) -> None:
        """缓存技术指标"""
        if cache_key:
            self._cache[cache_key] = {"data": indicators, "timestamp": datetime.now()}
            # 清理过期缓存
            self._cleanup_cache()

    def _get_cached_data(self, cache_key: str) -> Optional[MarketData]:
        """获取缓存数据"""
        if cache_key in self._cache:
            cached_item = self._cache[cache_key]
            if datetime.now() - cached_item["timestamp"] < timedelta(
                seconds=self._cache_ttl
            ):
                return cached_item["data"]
            else:
                del self._cache[cache_key]
        return None

    def _cache_data(self, cache_key: str, data: MarketData) -> None:
        """缓存数据"""
        self._cache[cache_key] = {"data": data, "timestamp": datetime.now()}

        # 清理过期缓存
        self._cleanup_cache()

    def _cleanup_cache(self) -> None:
        """清理过期缓存"""
        current_time = datetime.now()
        expired_keys = []

        for key, item in self._cache.items():
            if current_time - item["timestamp"] > timedelta(seconds=self._cache_ttl):
                expired_keys.append(key)

        for key in expired_keys:
            del self._cache[key]

    def clear_cache(self) -> None:
        """清空所有缓存"""
        self._cache.clear()
        logger.debug("已清空数据收集器缓存")

    def get_cache_stats(self) -> dict:
        """获取缓存统计信息"""
        current_time = datetime.now()
        active_items = 0
        expired_items = 0

        for item in self._cache.values():
            if current_time - item["timestamp"] < timedelta(seconds=self._cache_ttl):
                active_items += 1
            else:
                expired_items += 1

        return {
            "total_items": len(self._cache),
            "active_items": active_items,
            "expired_items": expired_items,
            "cache_ttl_seconds": self._cache_ttl,
        }

    def set_cache_ttl(self, ttl_seconds: int) -> None:
        """设置缓存TTL"""
        if ttl_seconds > 0:
            self._cache_ttl = ttl_seconds
            logger.debug(f"缓存TTL已设置为: {ttl_seconds}秒")
        else:
            raise ValueError("缓存TTL必须大于0")

    def validate_trading_pair(
        self, trading_pair: str, exchange: Optional[Exchange] = None
    ) -> bool:
        """
        验证交易对是否有效

        Args:
            trading_pair: 交易对
            exchange: Exchange实例

        Returns:
            bool: 交易对是否有效
        """
        try:
            current_exchange = exchange or self.exchange
            if not current_exchange:
                return False

            # 尝试获取市场信息来验证交易对
            market = current_exchange.getMarket(trading_pair)
            return market is not None

        except Exception as e:
            logger.warning(f"验证交易对失败: {trading_pair}, 错误: {str(e)}")
            return False
