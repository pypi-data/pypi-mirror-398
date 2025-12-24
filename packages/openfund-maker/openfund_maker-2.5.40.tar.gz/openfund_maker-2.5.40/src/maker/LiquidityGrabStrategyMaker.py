# -*- coding: utf-8 -*-
import traceback
import pandas as pd
import asyncio
from datetime import datetime, timedelta
from typing import override
from cachetools import TTLCache
from core.smc.TF import TF
from maker.StrategyMaker import StrategyMaker
from core.smc.AdaptiveTargetFinder import AdaptiveTargetFinder
from maker.TargetValidationEngine import TargetValidationEngine
from core.smc.TechnicalAnalysisIntegrator import TechnicalAnalysisIntegrator
from maker.ai_validation import AIValidationCoordinator, TradingDecision


class LiquidityGrabStrategyMaker(StrategyMaker):
    """
    流动性抓取形态策略Maker端
    基于Smart Money Concepts的流动性抓取策略，核心逻辑是识别市场中因"等低等高流动性"聚集形成的潜在转折点
    """

    def __init__(
        self, config, platform_config, common_config, logger=None, exchangeKey="okx"
    ):
        super().__init__(config, platform_config, common_config, logger, exchangeKey)
        self.logger = logger
        cache_ttl = common_config.get("cache_ttl", 60)

        # 缓存系统
        self.htf_cache = TTLCache(maxsize=100, ttl=int(cache_ttl * 60))
        self.atf_cache = TTLCache(maxsize=100, ttl=int(cache_ttl * 60))
        self.liquidity_cache = TTLCache(maxsize=100, ttl=600)  # 流动性缓存，10分钟TTL

        # 首次触及追踪器
        self.first_touch_tracker = {}

        # 流动性强度追踪
        self.liquidity_strength = {}

        # AI验证结果缓存 - 记录已验证的等高等低点位
        self.ai_validation_cache = {}

        # 初始化自适应目标位组件
        try:
            self.adaptive_target_finder = AdaptiveTargetFinder(self, config)
            self.target_validation_engine = TargetValidationEngine(
                config.get("liquidity_grab_strategy", {})
            )
            self.technical_analysis_integrator = TechnicalAnalysisIntegrator(self)
            self.logger.info("自适应目标位组件初始化成功")
        except Exception as e:
            self.logger.warning(f"自适应目标位组件初始化失败: {e}")
            # 回退到无自适应功能模式
            self.adaptive_target_finder = None
            self.target_validation_engine = None
            self.technical_analysis_integrator = None
            # 发送通知
            self.send_feishu_notification(
                "系统", f"自适应目标位功能初始化失败，回退到基础模式: {e}"
            )

        # 初始化AI验证协调器
        try:
            self.ai_validation_coordinator = AIValidationCoordinator()
            if not self.ai_validation_coordinator.is_enabled():
                self.logger.info("AI验证系统初始化成功但未启用")
        except Exception as e:
            self.logger.warning(f"AI验证系统初始化失败: {e}")
            self.ai_validation_coordinator = None
            # 发送通知
            self.send_feishu_notification(
                "系统", f"AI验证系统初始化失败，将跳过AI验证: {e}"
            )

    @override
    def reset_all_cache(self, symbol):
        """重置所有缓存"""
        super().reset_all_cache(symbol)
        self.htf_cache.pop(symbol, None)
        self.atf_cache.pop(symbol, None)
        self.liquidity_cache.pop(symbol, None)
        self.first_touch_tracker.pop(symbol, None)
        self.liquidity_strength.pop(symbol, None)
        self.ai_validation_cache.pop(symbol, None)

    @override
    def process_pair(self, symbol, pair_config):
        """
        流动性抓取策略核心处理逻辑
        HTF定方向→ATF找机会→LTF抓时机
        """
        self.logger.info("-" * 60)

        try:
            # 检查是否有持仓
            if self.fetch_position(symbol=symbol):
                self.reset_all_cache(symbol)
                self.logger.info(f"{symbol} : 有持仓合约，不进行下单。")
                return

            precision = self.get_precision_length(symbol)
            liquidity_strategy = pair_config.get("liquidity_grab_strategy", {})

            # 获取策略配置
            htf = str(pair_config.get("htf", "4h"))
            atf = str(pair_config.get("atf", "15m"))
            ltf = str(pair_config.get("ltf", "1m"))
            open_body_break = bool(pair_config.get("open_body_break", True))

            self.logger.info(
                f"{symbol} : 流动性抓取策略 {htf}|{atf}|{ltf} open_body_break={open_body_break}"
            )

            market_price = self.get_market_price(symbol=symbol)

            # Step 1: HTF确认趋势与核心支撑/阻力位
            htf_result = self._analyze_htf_trend_and_levels(
                symbol, htf, open_body_break, liquidity_strategy, precision
            )
            if not htf_result:
                return

            # Step 2: ATF识别等高等低流动性聚集区
            atf_result = self._analyze_atf_liquidity_zones(
                symbol,
                atf,
                htf_result,
                open_body_break,
                liquidity_strategy,
                precision,
                market_price,
            )
            if not atf_result:
                return

            # Step 3: LTF精准入场时机
            ltf_result = self._analyze_ltf_entry_timing(
                symbol,
                ltf,
                htf_result,
                atf_result,
                open_body_break,
                market_price,
                precision,
            )
            if not ltf_result:
                return

            # Step 4: 验证首次触及条件
            if not self._validate_first_touch_condition(
                symbol,
                atf_result.confluence_result["target_level"],
                atf_result.confluence_result["support_resistance_type"],
                liquidity_strategy,
            ):
                self.logger.info(f"{symbol} : 不满足首次触及条件，等待...")
                return

            # Step 5: AI验证
            entry_price = self.toDecimal(ltf_result["entry_price"])
            if not self._perform_ai_validation(
                symbol,
                htf,
                htf_result,
                atf_result,
                ltf_result,
                entry_price,
                liquidity_strategy,
                precision,
            ):
                return

            # Step 6: 执行下单
            self._execute_liquidity_grab_order(
                symbol, ltf_result, atf_result, market_price, pair_config, precision
            )

        except Exception as e:
            error_message = f"程序异常退出: {str(e)}"
            self.logger.error(f"{error_message}\n{traceback.format_exc()}")
            traceback.print_exc()
            self.send_feishu_notification(symbol, error_message)
        except KeyboardInterrupt:
            self.logger.info("程序收到中断信号，开始退出...")
        finally:
            self.logger.info("=" * 60 + "\n")

    def _analyze_htf_trend_and_levels(
        self, symbol, htf, open_body_break, strategy, precision
    ):
        """Step 1: HTF确认趋势与核心支撑/阻力位"""
        step = "1"
        htf_cache_key = f"{symbol}_{htf}"

        if htf_cache_key not in self.htf_cache:
            # HTF数据分析
            htf_df = self.get_historical_klines_df_by_cache(symbol=symbol, tf=htf)
            htf_struct = self.build_struct(
                symbol=symbol, data=htf_df, is_struct_body_break=open_body_break
            )
            htf_latest_struct = self.get_latest_struct(
                symbol=symbol, data=htf_struct, is_struct_body_break=open_body_break
            )

            if htf_latest_struct is None:
                self.logger.info(f"{symbol} : {step}.1 HTF {htf} 未形成结构，等待...")
                return None
            else:
                self.logger.info(f"{symbol} : {step}.1 HTF {htf} 形成结构. ")

            # 1.2 识别关键支撑阻力位
            range_of_the_ob = float(strategy.get("range_of_the_ob", 0.6))
            htf_OBs_df = self.find_OBs(
                symbol=symbol,
                struct=htf_struct,
                is_struct_body_break=open_body_break,
                atr_multiplier=range_of_the_ob,
            )
            htf_support_resistance = self.get_support_resistance_from_OBs(
                symbol=symbol, obs_df=htf_OBs_df, struct_df=htf_struct
            )

            if htf_support_resistance is None:
                self.logger.info(
                    f"{symbol} : {step}.2. HTF {htf} 未找到支撑位和阻力位。"
                )
                return None

            htf_support_price = htf_support_resistance.get(self.SUPPORT_PRICE_KEY)
            htf_resistance_price = htf_support_resistance.get(self.RESISTANCE_PRICE_KEY)
            htf_support_OB = htf_support_resistance.get(self.SUPPORT_OB_KEY)
            htf_resistance_OB = htf_support_resistance.get(self.RESISTANCE_OB_KEY)

            self.logger.info(
                f"{symbol} : {step}.2. HTF {htf} 支撑位={htf_support_price:.{precision}f}, 阻力位={htf_resistance_price:.{precision}f}"
            )

            # 1.3 检查利润空间
            min_profit_percent = self.toDecimal(strategy.get("min_profit_percent", 4))
            profit_percent = self.toDecimal(
                abs(
                    (htf_resistance_price - htf_support_price) / htf_support_price * 100
                )
            )

            if profit_percent < min_profit_percent:
                self.logger.info(
                    f"{symbol} : {step}.3. HTF {htf} 利润空间{profit_percent:.2f}% < {min_profit_percent}%，等待..."
                )
                return None

            # 使用AI分析HTF趋势和后续交易方向
            htf_trend, htf_side = self._analyze_htf_trend_with_ai(
                symbol, htf, htf_df, htf_latest_struct
            )

            enable_htf_ai = (
                self.ai_validation_coordinator
                and self.ai_validation_coordinator.validation_config.enable_htf_trend_analysis
            )
            analysis_method = "AI分析" if enable_htf_ai else "传统分析"
            self.logger.info(
                f"{symbol} : {step}.4. HTF {htf} {analysis_method} - 趋势: {htf_trend}, 交易方向: {htf_side}"
            )

            # 构建HTF缓存
            tf_HTF = TF(TF.HTF, htf, htf_side, htf_trend)
            tf_HTF.resistance_price = htf_resistance_price
            tf_HTF.support_price = htf_support_price
            tf_HTF.struct = htf_latest_struct
            tf_HTF.support_OB = htf_support_OB
            tf_HTF.resistance_OB = htf_resistance_OB

            self.htf_cache[htf_cache_key] = tf_HTF
            self.logger.info(f"{symbol} : {step}.4. HTF {htf} 缓存构建成功")

        return self.htf_cache[htf_cache_key]

    def _analyze_htf_trend_with_ai(
        self,
        symbol,
        htf,
        htf_df,
        htf_latest_struct,
        support_price=None,
        resistance_price=None,
    ):
        """使用AI分析HTF趋势方向和交易方向

        Args:
            symbol: 交易对
            htf: 高时间框架
            htf_df: HTF K线数据
            htf_latest_struct: HTF最新结构
            support_price: 支撑价格
            resistance_price: 阻力价格

        Returns:
            tuple: (趋势方向, 交易方向) - (BULLISH_TREND/BEARISH_TREND, BUY_SIDE/SELL_SIDE)
        """
        # 检查HTF趋势AI分析开关
        enable_htf_trend_analysis = (
            self.ai_validation_coordinator
            and self.ai_validation_coordinator.validation_config.enable_htf_trend_analysis
        )
        
        # 如果AI验证未启用或HTF趋势分析未启用，使用传统方法
        if not (
            self.ai_validation_coordinator
            and self.ai_validation_coordinator.is_enabled()
            and enable_htf_trend_analysis
        ):
            trend = htf_latest_struct[self.STRUCT_DIRECTION_COL]
            side = (
                self.BUY_SIDE
                if trend.upper() == self.BULLISH_TREND.upper()
                else self.SELL_SIDE
            )
            return trend, side

        try:
            # 获取最近16条K线数据
            recent_candles = (
                htf_df.tail(16).to_dict("records") if htf_df is not None else []
            )

            if len(recent_candles) < 16:
                self.logger.warning(f"{symbol}: HTF K线数据不足16条，使用传统方法")
                trend = htf_latest_struct[self.STRUCT_DIRECTION_COL]
                side = (
                    self.BUY_SIDE
                    if trend.upper() == self.BULLISH_TREND.upper()
                    else self.SELL_SIDE
                )
                return trend, side

            # 构建AI提示词（包含支撑阻力位和交易方向分析要求）
            prompt = self._build_htf_trend_analysis_prompt(
                symbol,
                htf,
                recent_candles,
                htf_latest_struct,
                support_price,
                resistance_price,
            )

            # 调用AI服务
            ai_response = self._call_ai_for_trend_analysis(prompt)

            if ai_response:
                ai_trend = ai_response.get("trend", "").upper()
                ai_side = ai_response.get("side", "").lower()

                # 验证AI返回的趋势和交易方向
                if ai_trend in ["BULLISH", "BEARISH"] and ai_side in ["buy", "sell"]:
                    self.logger.info(
                        f"{symbol}: AI分析结果 - 趋势: {ai_trend}, 交易方向: {ai_side.upper()}, "
                        f"置信度: {ai_response.get('confidence', 0):.3f}"
                    )
                    return ai_trend, ai_side
                else:
                    self.logger.warning(
                        f"{symbol}: AI返回无效结果 - 趋势: {ai_trend}, 方向: {ai_side}"
                    )

        except Exception as e:
            self.logger.error(f"{symbol}: AI趋势分析失败: {str(e)}")

        # 降级到传统方法
        self.logger.info(f"{symbol}: 使用传统方法分析HTF趋势")
        trend = htf_latest_struct[self.STRUCT_DIRECTION_COL]
        side = (
            self.BUY_SIDE
            if trend.upper() == self.BULLISH_TREND.upper()
            else self.SELL_SIDE
        )
        return trend, side

    def _build_htf_trend_analysis_prompt(
        self,
        symbol,
        htf,
        recent_candles,
        htf_latest_struct,
        support_price=None,
        resistance_price=None,
    ):
        """构建HTF趋势分析的AI提示词"""
        from maker.ai_validation.config import get_prompt_config

        # 格式化K线数据
        candle_data = []
        for i, candle in enumerate(recent_candles):
            candle_info = {
                "index": i + 1,
                "timestamp": candle.get("timestamp", ""),
                "open": float(candle.get("open", 0)),
                "high": float(candle.get("high", 0)),
                "low": float(candle.get("low", 0)),
                "close": float(candle.get("close", 0)),
                "volume": float(candle.get("volume", 0)),
            }
            candle_data.append(candle_info)

        # 获取结构信息
        struct_timestamp = htf_latest_struct.get(self.TIMESTAMP_COL, "")
        struct_type_raw = htf_latest_struct.get(self.STRUCT_COL, "UNKNOWN")

        # 提取结构类型，去掉趋势方向前缀
        if "_" in str(struct_type_raw):
            struct_type = str(struct_type_raw).split("_")[
                -1
            ]  # 取最后部分，如BOS、CHoCH、SMS
        else:
            struct_type = str(struct_type_raw)

        # 构建支撑阻力位信息
        support_resistance_info = ""
        if support_price is not None:
            support_resistance_info += f"- 关键支撑位: {support_price:.4f}\n"
        if resistance_price is not None:
            support_resistance_info += f"- 关键阻力位: {resistance_price:.4f}\n"

        # 从配置获取提示词模板并填充变量
        prompt_config = get_prompt_config()
        prompt = prompt_config.htf_trend_analysis_prompt.format(
            symbol=symbol,
            htf=htf,
            candle_data=self._format_candle_data_for_prompt(candle_data),
            struct_type=struct_type,
            struct_timestamp=struct_timestamp,
            support_resistance_info=support_resistance_info,
        )
        return prompt

    def _format_candle_data_for_prompt(self, candle_data):
        """格式化K线数据用于AI提示词"""
        formatted_lines = []
        for candle in candle_data:
            line = f"#{candle['index']:2d} | {candle['timestamp']} | O:{candle['open']:8.4f} H:{candle['high']:8.4f} L:{candle['low']:8.4f} C:{candle['close']:8.4f} V:{candle['volume']:10.2f}"
            formatted_lines.append(line)
        return "\n".join(formatted_lines)

    def _call_ai_for_trend_analysis(self, prompt):
        """调用AI服务进行趋势分析"""
        try:
            # 使用现有的AI客户端
            if (
                hasattr(self.ai_validation_coordinator, "ai_client")
                and self.ai_validation_coordinator.ai_client
            ):
                # 记录发送的提示词
                self.logger.info("=" * 80)
                self.logger.info("HTF趋势分析 - 发送给AI的提示词:")
                self.logger.info("-" * 80)
                self.logger.info(prompt)
                self.logger.info("=" * 80)

                # 构建请求数据 - 使用DeepSeek模型
                request_data = {
                    "model": "deepseek-chat",
                    "messages": [
                        {
                            "role": "system",
                            "content": "你是一位专业的金融分析师，专门分析加密货币市场趋势。",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1000,
                }

                # 发送请求
                response = self.ai_validation_coordinator.ai_client._make_request_raw(
                    request_data
                )

                if response and "choices" in response and len(response["choices"]) > 0:
                    content = response["choices"][0]["message"]["content"]

                    # 记录AI原始返回内容
                    self.logger.debug("=" * 80)
                    self.logger.debug("HTF趋势分析 - AI原始返回内容:")
                    self.logger.debug("-" * 80)
                    self.logger.debug(content)
                    self.logger.debug("=" * 80)

                    # 尝试解析JSON响应
                    import json

                    try:
                        # 清理可能的代码块标记
                        cleaned_content = content.strip()
                        if cleaned_content.startswith("```json"):
                            cleaned_content = cleaned_content[7:]  # 移除 ```json
                        if cleaned_content.endswith("```"):
                            cleaned_content = cleaned_content[:-3]  # 移除 ```
                        cleaned_content = cleaned_content.strip()

                        parsed_response = json.loads(cleaned_content)
                        return parsed_response
                    except json.JSONDecodeError:
                        # 如果不是JSON格式，尝试提取趋势信息
                        if "BULLISH" in content.upper():
                            return {"trend": "BULLISH", "confidence": 0.7}
                        elif "BEARISH" in content.upper():
                            return {"trend": "BEARISH", "confidence": 0.7}

        except Exception as e:
            self.logger.error(f"AI趋势分析调用失败: {str(e)}")

        return None

    def _analyze_atf_liquidity_zones(
        self,
        symbol,
        atf,
        htf_result,
        open_body_break,
        strategy,
        precision,
        market_price,
    ):
        """Step 2: ATF识别等高等低流动性聚集区"""
        step = "2"
        atf_cache_key = f"{symbol}_{atf}"

        if atf_cache_key not in self.atf_cache:
            # 获取ATF数据
            htf_support_timestamp = (
                htf_result.support_OB.get(self.TIMESTAMP_COL)
                if htf_result.support_OB
                else None
            )
            htf_resistance_timestamp = (
                htf_result.resistance_OB.get(self.TIMESTAMP_COL)
                if htf_result.resistance_OB
                else None
            )

            if htf_support_timestamp and htf_resistance_timestamp:
                min_timestamp = min(htf_support_timestamp, htf_resistance_timestamp)
                atf_start_timestamp = (
                    pd.Timestamp(min_timestamp) - pd.Timedelta(atf)
                ).strftime("%Y-%m-%d %H:%M:%S+08:00")
                atf_df = self.get_historical_klines_df(
                    symbol=symbol, tf=atf, after=atf_start_timestamp
                )
            else:
                atf_df = self.get_historical_klines_df_by_cache(symbol=symbol, tf=atf)

            atf_struct = self.build_struct(
                symbol=symbol, data=atf_df, is_struct_body_break=open_body_break
            )
            atf_latest_struct = self.get_latest_struct(
                symbol=symbol, data=atf_struct, is_struct_body_break=open_body_break
            )

            if atf_latest_struct is None:
                self.logger.info(f"{symbol} : {step}.1. ATF {atf} 未形成结构，等待...")
                return None

            atf_trend = atf_latest_struct[self.STRUCT_DIRECTION_COL]
            atf_side = (
                self.BUY_SIDE if atf_trend == self.BULLISH_TREND else self.SELL_SIDE
            )

            # 2.1 验证ATF与HTF趋势一致性
            enable_check_htf_side = bool(strategy.get("enable_check_htf_side", True))
            if enable_check_htf_side:
                if htf_result.side != atf_side:
                    self.logger.info(
                        f"{symbol} : {step}.1. ATF {atf} 趋势{atf_side} 与 HTF 趋势{htf_result.side} 不一致，等待..."
                    )
                    return None
                self.logger.info(
                    f"{symbol} : {step}.1. ATF {atf} 趋势{atf_side} 与 HTF 趋势一致"
                )

            # 2.2 计算ATF支撑阻力位（先计算，用于筛选满足利润空间的流动性）
            range_of_the_ob = float(strategy.get("range_of_the_ob", 0.6))
            atf_OBs_df = self.find_OBs(
                symbol=symbol,
                struct=atf_struct,
                is_struct_body_break=open_body_break,
                atr_multiplier=range_of_the_ob,
            )
            atf_support_resistance = self.get_support_resistance_from_OBs(
                symbol=symbol, obs_df=atf_OBs_df, struct_df=atf_struct
            )
            atf_support_price = (
                atf_support_resistance.get(self.SUPPORT_PRICE_KEY)
                if atf_support_resistance
                else None
            )
            atf_resistance_price = (
                atf_support_resistance.get(self.RESISTANCE_PRICE_KEY)
                if atf_support_resistance
                else None
            )

            # 2.3 识别等高等低流动性（基于HTF方向，筛选满足利润空间的）
            trader_side = (
                self.BULLISH_TREND
                if htf_result.side == self.BUY_SIDE
                else self.BEARISH_TREND
            )
            # 根据交易方向确定目标价格：多头用支撑位，空头用阻力位
            target_price = (
                atf_support_price
                if trader_side == self.BULLISH_TREND
                else atf_resistance_price
            )

            liquidity_result, df_equal_liquidity = (
                self._identify_equal_highs_lows_liquidity(
                    symbol, atf_df, trader_side, strategy, target_price
                )
            )
            liquidity_source = "ATF"
            if not liquidity_result:
                self.logger.info(
                    f"{symbol} : {step}.3. ATF {atf} 未找到满足利润空间的等高等低流动性，尝试在HTF中寻找"
                )
                # 回退到HTF寻找流动性
                htf_df = self.get_historical_klines_df_by_cache(
                    symbol=symbol, tf=htf_result.tf_value
                )
                if htf_df is not None:
                    liquidity_result, df_equal_liquidity = (
                        self._identify_equal_highs_lows_liquidity(
                            symbol, htf_df, trader_side, strategy, target_price
                        )
                    )
                    if liquidity_result:
                        liquidity_source = "HTF"
                        self.logger.info(
                            f"{symbol} : {step}.3. HTF {htf_result.tf_value} 找到满足利润空间的等高等低流动性"
                        )
                if not liquidity_result:
                    self.logger.info(
                        f"{symbol} : {step}.3. ATF和HTF均未找到满足利润空间的等高等低流动性"
                    )
                    return None

            self.logger.info(
                f"{symbol} : {step}.3 {liquidity_source} 发现{liquidity_result[self.EQUAL_POINTS_TYPE_COL]}流动性，价格={liquidity_result[self.EQUAL_POINTS_PRICE_COL]}"
            )

            # 2.4 验证支撑/阻力位与流动性的配合（使用ATF周期的支撑阻力位）

            confluence_result = self._validate_support_resistance_confluence(
                symbol,
                atf_support_price,
                atf_resistance_price,
                liquidity_result,
                trader_side,
                precision,
                strategy,
            )
            if not confluence_result:
                return None

            # 2.4 验证市场价格在支撑/阻力位的ATR范围内
            liquidity_type = confluence_result["liquidity_type"]
            # 计算ATR
            from core.smc.SMCBase import SMCBase

            atr_df = SMCBase.calculate_atr(atf_df)
            current_atr = self.toDecimal(atr_df[SMCBase.ATR_COL].iloc[-1])

            if liquidity_type in (self.EQUAL_HIGH_TYPE, "extreme_high"):
                # 等高流动性（做多）：市场价格应在ATF支撑位的ATR范围内
                if atf_support_price is None:
                    self.logger.info(f"{symbol} : {step}.4. ATF未找到支撑位，等待")
                    return None
                price_diff = abs(market_price - atf_support_price)
                if price_diff > current_atr:
                    self.logger.info(
                        f"{symbol} : {step}.4. 等高流动性但市场价格{market_price:.{precision}f}距离ATF支撑位{atf_support_price:.{precision}f}超出ATR范围({current_atr:.{precision}f})，等待"
                    )
                    return None
                else:
                    self.logger.info(
                        f"{symbol} : {step}.4. 等高流动性，市场价格{market_price:.{precision}f}在ATF支撑位{atf_support_price:.{precision}f}的ATR范围内，继续"
                    )
            else:
                # 等低流动性（做空）：市场价格应在ATF阻力位的ATR范围内
                if atf_resistance_price is None:
                    self.logger.info(f"{symbol} : {step}.4. ATF未找到阻力位，等待")
                    return None
                price_diff = abs(market_price - atf_resistance_price)
                if price_diff > current_atr:
                    self.logger.info(
                        f"{symbol} : {step}.4. 等低流动性但市场价格{market_price:.{precision}f}距离ATF阻力位{atf_resistance_price:.{precision}f}超出ATR范围({current_atr:.{precision}f})，等待"
                    )
                    return None
                else:
                    self.logger.info(
                        f"{symbol} : {step}.4. 等低流动性，市场价格{market_price:.{precision}f}在ATF阻力位{atf_resistance_price:.{precision}f}的ATR范围内，继续"
                    )

            # 构建ATF缓存
            tf_ATF = TF(TF.ATF, atf, atf_side, atf_trend)
            tf_ATF.struct = atf_latest_struct
            tf_ATF.liquidity_result = liquidity_result
            tf_ATF.confluence_result = confluence_result
            tf_ATF.df_equal_liquidity = df_equal_liquidity

            self.atf_cache[atf_cache_key] = tf_ATF
            self.logger.info(f"{symbol} : {step}.5. ATF {atf} 流动性分析完成")

        return self.atf_cache[atf_cache_key]

    def _identify_equal_highs_lows_liquidity(
        self, symbol, data, trend, strategy, target_price=None
    ) -> tuple:
        """识别等高等低流动性

        Args:
            target_price: 目标价格（支撑位或阻力位），用于筛选满足利润空间的流动性

        Returns:
            tuple: (liquidity_result, df_equal_liquidity) 或 (None, None)
        """
        atr_offset = self.toDecimal(strategy.get("liquidity_atr_offset", 0.1))
        min_profit_percent = strategy.get("min_profit_percent", 4)

        # 使用SMCLiquidity查找等高等低
        df_equal_liquidity = self.find_EQH_EQL(
            symbol=symbol, data=data, trend=trend, atr_offset=atr_offset
        )
        # 找到流动性
        mask = df_equal_liquidity[self.HAS_EQUAL_POINTS_COL]
        if len(df_equal_liquidity[mask]) == 0:
            # self.logger.info(f"{symbol} : 未找到等高等低流动性，继续等待...")
            return None, None
        else:
            # 打印等高等低流动性的关键信息用于调试
            debug_columns = [
                self.TIMESTAMP_COL,
                self.EQUAL_POINTS_PRICE_COL,
                self.EQUAL_POINTS_TYPE_COL,
                self.EXTREME_VALUE_COL,
                self.ATR_TOLERANCE_COL,
                self.HAS_EQUAL_POINTS_COL,
            ]
            self.logger.debug(
                f"df_equal_liquidity=\n{df_equal_liquidity[debug_columns].to_string()}"
            )

        liquidity_result = self._get_equal_liquidity(
            df_equal_liquidity, trend, target_price, min_profit_percent
        )
        return liquidity_result, df_equal_liquidity

    def _get_equal_liquidity(
        self, df_equal_liquidity, trend, target_price=None, min_profit_percent=None
    ):
        """获取满足利润空间要求且时间最新的流动性

        Args:
            df_equal_liquidity: 等高等低流动性DataFrame
            trend: 趋势方向
            target_price: 目标价格（支撑位或阻力位），用于计算利润空间
            min_profit_percent: 最小利润百分比要求
        """
        # 筛选有等高点的行
        df_with_equal_points = df_equal_liquidity[
            df_equal_liquidity[self.HAS_EQUAL_POINTS_COL]
        ]

        if df_with_equal_points.empty:
            return None

        # 如果提供了利润空间要求，筛选满足条件的流动性
        if target_price is not None and min_profit_percent is not None:
            target_price = self.toDecimal(target_price)
            min_profit_percent = self.toDecimal(min_profit_percent)

            valid_rows = []
            for idx, row in df_with_equal_points.iterrows():
                liquidity_price = self.toDecimal(row[self.EQUAL_POINTS_PRICE_COL])
                profit_distance = abs(liquidity_price - target_price)
                profit_percent = profit_distance / target_price * 100
                if profit_percent >= min_profit_percent:
                    valid_rows.append(idx)

            if valid_rows:
                # 从满足条件的流动性中选择时间最新的
                target_row = df_with_equal_points.loc[valid_rows[-1]]
            else:
                # 没有满足利润空间的，返回None
                return None
        else:
            # 没有利润要求时，选择时间最近的一组
            target_row = df_with_equal_points.iloc[-1]

        return {
            self.TIMESTAMP_COL: target_row[self.TIMESTAMP_COL],
            self.EQUAL_POINTS_PRICE_COL: target_row[self.EQUAL_POINTS_PRICE_COL],
            self.EQUAL_POINTS_TYPE_COL: target_row[self.EQUAL_POINTS_TYPE_COL],
            "trend": trend,
            "equal_liquidity": target_row,
        }

    def _validate_support_resistance_confluence(
        self,
        symbol,
        atf_support_price,
        atf_resistance_price,
        liquidity_result,
        trader_side,
        precision,
        strategy,
    ):
        """验证支撑/阻力位与流动性的配合（使用ATF周期的支撑阻力位）"""
        step = "2.3"

        if trader_side == self.BUY_SIDE:
            # 多头：需要支撑位+等高流动性配合
            if atf_support_price is None:
                self.logger.info(
                    f"{symbol} : {step}.1. ATF未找到支撑位，无法验证多头机会"
                )
                return None
            support_price = atf_support_price
            liquidity_price = liquidity_result[self.EQUAL_POINTS_PRICE_COL]
            liquidity_type = liquidity_result[self.EQUAL_POINTS_TYPE_COL]
            has_equal_points = liquidity_result.get("equal_liquidity", {}).get(
                self.HAS_EQUAL_POINTS_COL, False
            )

            # 接受equal_high或者extreme_high(当has_equal_points=True时)
            is_valid_high_liquidity = liquidity_type == self.EQUAL_HIGH_TYPE or (
                liquidity_type == "extreme_high" and has_equal_points
            )

            if not is_valid_high_liquidity:
                self.logger.info(
                    f"{symbol} : {step}.2. 多头需要等高流动性，但找到的是{liquidity_type}(has_equal_points={has_equal_points})"
                )
                return None

            target_level = support_price
            tp_target = liquidity_price
            support_resistance_type = self.SUPPORT_TYPE

            self.logger.info(
                f"{symbol} : {step}.3. 多头机会: ATF支撑位={support_price:.{precision}f}, 等高流动性={liquidity_price:.{precision}f}(类型={liquidity_type})"
            )

        else:
            # 空头：需要阻力位+等低流动性配合
            if atf_resistance_price is None:
                self.logger.info(
                    f"{symbol} : {step}.1. ATF未找到阻力位，无法验证空头机会"
                )
                return None
            resistance_price = atf_resistance_price
            liquidity_price = liquidity_result[self.EQUAL_POINTS_PRICE_COL]
            liquidity_type = liquidity_result[self.EQUAL_POINTS_TYPE_COL]
            has_equal_points = liquidity_result.get("equal_liquidity", {}).get(
                self.HAS_EQUAL_POINTS_COL, False
            )

            # 接受equal_low或者extreme_low(当has_equal_points=True时)
            is_valid_low_liquidity = liquidity_type == self.EQUAL_LOW_TYPE or (
                liquidity_type == "extreme_low" and has_equal_points
            )

            if not is_valid_low_liquidity:
                self.logger.info(
                    f"{symbol} : {step}.2. 空头需要等低流动性，但找到的是{liquidity_type}(has_equal_points={has_equal_points})"
                )
                return None

            target_level = resistance_price
            tp_target = liquidity_price
            support_resistance_type = self.RESISTANCE_TYPE

            self.logger.info(
                f"{symbol} : {step}.3. 空头机会: ATF阻力位={resistance_price:.{precision}f}, 等低流动性={liquidity_price:.{precision}f}(类型={liquidity_type})"
            )

        # 利润空间验证
        min_profit_percent = self.toDecimal(strategy.get("min_profit_percent", 4))
        profit_distance = abs(self.toDecimal(tp_target) - self.toDecimal(target_level))
        profit_percent = profit_distance / self.toDecimal(target_level) * 100

        if profit_percent < min_profit_percent:
            self.logger.info(
                f"{symbol} : {step}.4. 利润空间验证不通过：利润率={profit_percent:.2f}% < {min_profit_percent}%"
            )
            return None

        self.logger.info(
            f"{symbol} : {step}.4. 利润空间验证通过, 利润率={profit_percent:.2f}%"
        )

        return {
            "target_level": target_level,
            "tp_target": tp_target,
            "support_resistance_type": support_resistance_type,
            "liquidity_type": liquidity_type,
            "side": trader_side,
            "profit_distance": profit_distance,
        }

    def _analyze_ltf_entry_timing(
        self,
        symbol,
        ltf,
        htf_result,
        atf_result,
        open_body_break,
        market_price,
        precision,
    ):
        """Step 3: LTF精准入场时机"""
        step = "3"

        # 获取LTF数据
        ltf_df = self.get_historical_klines_df(symbol=symbol, tf=ltf)
        ltf_struct = self.build_struct(
            symbol=symbol, data=ltf_df, is_struct_body_break=open_body_break
        )
        ltf_latest_struct = self.get_latest_struct(
            symbol=symbol, data=ltf_struct, is_struct_body_break=open_body_break
        )

        if ltf_latest_struct is None:
            self.logger.info(f"{symbol} : {step}.1. LTF {ltf} 未形成结构，等待...")
            return None

        ltf_trend = ltf_latest_struct[self.STRUCT_DIRECTION_COL]
        ltf_side = self.BUY_SIDE if ltf_trend == self.BULLISH_TREND else self.SELL_SIDE

        self.logger.info(f"{symbol} : {step}.1. LTF {ltf} 趋势: {ltf_trend}")

        # 3.1 检查价格是否接近目标位置
        target_level = self.toDecimal(atf_result.confluence_result["target_level"])
        market_price = self.toDecimal(market_price)
        tolerance_pct = self.toDecimal(0.5)  # 0.5%容差
        price_diff_pct = abs(market_price - target_level) / target_level * 100

        if price_diff_pct > tolerance_pct:
            self.logger.info(
                f"{symbol} : {step}.2. 当前价格{market_price:.{precision}f}距离目标位{target_level:.{precision}f}太远({price_diff_pct:.2f}%)"
            )

            # 尝试自适应目标位搜索
            if self.adaptive_target_finder:
                try:
                    adaptive_result = self.adaptive_target_finder.find_adaptive_target(
                        symbol=symbol,
                        current_price=float(market_price),
                        original_target=float(target_level),
                        side=atf_result.confluence_result["side"],
                        htf_result=htf_result,
                        atf_result=atf_result,
                        precision=precision,
                    )

                    if adaptive_result.success:
                        # 更新目标位
                        new_target_level = self.toDecimal(
                            adaptive_result.new_target_price
                        )
                        atf_result.confluence_result["target_level"] = new_target_level
                        atf_result.confluence_result["adaptive_adjustment"] = True
                        atf_result.confluence_result["adjustment_reason"] = (
                            adaptive_result.adjustment_reason
                        )

                        self.logger.info(
                            f"{symbol} : {step}.2.1. 自适应目标位调整成功: "
                            f"{float(target_level):.{precision}f} -> {adaptive_result.new_target_price:.{precision}f}"
                        )

                        # 更新target_level为新的目标位
                        target_level = new_target_level
                        price_diff_pct = (
                            abs(market_price - target_level) / target_level * 100
                        )
                    else:
                        self.logger.info(
                            f"{symbol} : {step}.2.2. 自适应目标位搜索失败: {adaptive_result.adjustment_reason}"
                        )
                        return None

                except Exception as e:
                    self.logger.error(
                        f"{symbol} : {step}.2.3. 自适应目标位搜索异常: {e}"
                    )
                    # 发送异常通知
                    self.send_feishu_notification(symbol, f"自适应目标位搜索异常: {e}")
                    # 回退到等待模式
                    return None
            else:
                self.logger.info(
                    f"{symbol} : {step}.2.4. 自适应目标位功能不可用，回退到等待模式"
                )
                return None

        # 3.2 检查LTF结构反转信号
        expected_side = atf_result.confluence_result["side"]
        if ltf_side != expected_side:
            self.logger.info(
                f"{symbol} : {step}.3. LTF结构{ltf_side}与预期方向{expected_side}不符，等待..."
            )
            return None

        # 3.3 寻找PDArray入场点
        ltf_PDArrays_df = self.find_PDArrays(
            symbol=symbol,
            struct=ltf_struct,
            side=ltf_side,
            is_struct_body_break=open_body_break,
        )
        if len(ltf_PDArrays_df) == 0:
            self.logger.info(f"{symbol} : {step}.4. LTF {ltf} 未找到PDArray，等待...")
            return None

        # 选择最新的PDArray
        ltf_latest_PDArray = ltf_PDArrays_df.iloc[-1]

        # 检查当前价格是否在PDArray范围内
        if not (
            ltf_latest_PDArray[self.PD_LOW_COL]
            <= market_price
            <= ltf_latest_PDArray[self.PD_HIGH_COL]
        ):
            self.logger.info(
                f"{symbol} : {step}.5. 当前价格{market_price:.{precision}f}不在PDArray范围内"
            )
            return None

        self.logger.info(f"{symbol} : {step}.6. LTF {ltf} 入场条件满足")

        return {
            "ltf_side": ltf_side,
            "ltf_trend": ltf_trend,
            "ltf_struct": ltf_latest_struct,
            "entry_pdarray": ltf_latest_PDArray,
            "entry_price": ltf_latest_PDArray[self.PD_MID_COL],
        }

    def _validate_first_touch_condition(
        self, symbol, target_level, support_resistance_type, strategy
    ):
        """验证首次触及条件"""
        max_candle_interval = int(strategy.get("max_candle_interval", 200))

        if symbol not in self.first_touch_tracker:
            self.first_touch_tracker[symbol] = {}

        level_key = f"{support_resistance_type}_{target_level}"
        touch_history = self.first_touch_tracker[symbol]

        if level_key in touch_history:
            last_touch_time = touch_history[level_key]
            # FIXME:如果距离上次触及超过200个K线，可以重置
            if (
                datetime.now() - last_touch_time
            ).total_seconds() > 15 * max_candle_interval:
                del touch_history[level_key]
            else:
                return False

        # 标记为已触及
        touch_history[level_key] = datetime.now()
        return True

    def _perform_ai_validation(
        self,
        symbol,
        htf,
        htf_result,
        atf_result,
        ltf_result,
        entry_price,
        strategy,
        precision,
    ):
        """Step 5: AI验证等高等低形态

        Returns:
            True: 验证通过或未启用
            False: 验证建议跳过
        """
        step = "5"

        if not (
            self.ai_validation_coordinator
            and self.ai_validation_coordinator.is_enabled()
        ):
            self.logger.debug(f"{symbol} : {step}. AI验证未启用，跳过验证")
            return True

        liquidity_result = atf_result.liquidity_result
        confluence_result = atf_result.confluence_result
        liquidity_price = liquidity_result[self.EQUAL_POINTS_PRICE_COL]
        liquidity_type = liquidity_result[self.EQUAL_POINTS_TYPE_COL]
        liquidity_key = f"{liquidity_type}_{liquidity_price:.{precision}f}"

        # 初始化symbol的缓存
        if symbol not in self.ai_validation_cache:
            self.ai_validation_cache[symbol] = {}

        # 检查是否已经验证过相同的点位
        if liquidity_key in self.ai_validation_cache[symbol]:
            cached_validation = self.ai_validation_cache[symbol][liquidity_key]
            self.logger.info(
                f"{symbol} : {step}. 使用缓存的AI验证结果 - 决策: {cached_validation['decision'].value}"
            )
            if cached_validation["decision"] == TradingDecision.SKIP:
                return False
            elif cached_validation["decision"] == TradingDecision.EXECUTE:
                confluence_result["ai_validation"] = cached_validation.get(
                    "ai_validation"
                )
                return True
            else:  # FALLBACK
                return (
                    self.ai_validation_coordinator.validation_config.fallback_mode
                    != "skip"
                )

        # 执行新的AI验证
        self.logger.info(f"{symbol} : {step}. 开始AI验证等高等低形态")

        # 构建HTF/ATF上下文
        htf_context = self.build_timeframe_context(
            timeframe=htf_result.tf_value,
            trend=htf_result.trend,
            struct=htf_result.struct,
            support_price=htf_result.support_price,
            resistance_price=htf_result.resistance_price,
            support_pd_array=getattr(htf_result, "support_OB", None),
            resistance_pd_array=getattr(htf_result, "resistance_OB", None),
        )
        atf_context = self.build_timeframe_context(
            timeframe=atf_result.tf_value,
            trend=atf_result.trend,
            struct=atf_result.struct,
        )

        # 获取K线数据
        htf_df = self.get_historical_klines_df_by_cache(
            symbol=symbol, tf=htf_result.tf_value
        )
        atf_df = self.get_historical_klines_df_by_cache(
            symbol=symbol, tf=atf_result.tf_value
        )
        htf_candles = htf_df.tail(10).to_dict("records") if htf_df is not None else []
        atf_candles = atf_df.tail(20).to_dict("records") if atf_df is not None else []

        # 准备策略信号数据
        strategy_signal = {
            "type": "equal_highs_lows",
            "trading_pair": symbol,
            "direction": ltf_result["ltf_side"],
            "price": liquidity_price,
            "timeframe": atf_result.tf_value,
            "pattern_type": liquidity_type,
            "trend": atf_result.trend,
            "exchange": self.exchange,
            "atr_offset": strategy.get("liquidity_atr_offset", 0.1),
            "lookback": 1,
            "htf_context": htf_context,
            "atf_context": atf_context,
            "htf_candles": htf_candles,
            "atf_candles": atf_candles,
            "opportunity_info": {
                "target_level": float(entry_price),
                "tp_target": confluence_result["tp_target"],
                "liquidity_type": confluence_result["liquidity_type"],
                "profit_distance": confluence_result["profit_distance"],
            },
        }

        # 执行AI验证
        validation_result = self.ai_validation_coordinator.validate_pattern(
            symbol,
            strategy_signal,
            existing_equal_points_df=atf_result.df_equal_liquidity,
        )

        # 缓存验证结果
        cache_entry = {
            "decision": validation_result.decision,
            "timestamp": datetime.now(),
        }

        if validation_result.decision == TradingDecision.SKIP:
            if validation_result.ai_response:
                self.logger.info(
                    f"{symbol} : {step}. AI验证建议跳过交易\n"
                    f"  置信度: {validation_result.confidence:.3f}\n"
                    f"  推理过程: {validation_result.ai_response.reasoning}"
                )
            self.send_feishu_notification(
                symbol,
                f"AI验证建议跳过交易\n"
                f"形态类型: {liquidity_type}\n"
                f"下单价格: {entry_price:.{precision}f}\n"
                f"置信度: {validation_result.confidence:.3f}\n"
                f"原因: {validation_result.ai_response.reasoning if validation_result.ai_response else validation_result.error_message}",
            )
            self.ai_validation_cache[symbol][liquidity_key] = cache_entry
            return False
        elif validation_result.decision == TradingDecision.EXECUTE:
            self.logger.info(
                f"{symbol} : {step}. AI验证通过 - 置信度: {validation_result.confidence:.3f}"
            )
            ai_validation_info = {
                "confidence": validation_result.confidence,
                "reasoning": (
                    validation_result.ai_response.reasoning
                    if validation_result.ai_response
                    else None
                ),
                "model_version": (
                    validation_result.ai_response.model_version
                    if validation_result.ai_response
                    else None
                ),
            }
            confluence_result["ai_validation"] = ai_validation_info
            cache_entry["ai_validation"] = ai_validation_info
            self.ai_validation_cache[symbol][liquidity_key] = cache_entry
            return True
        else:  # FALLBACK
            self.logger.warning(f"{symbol} : {step}. AI验证失败，使用降级策略")
            self.ai_validation_cache[symbol][liquidity_key] = cache_entry
            return (
                self.ai_validation_coordinator.validation_config.fallback_mode != "skip"
            )

    def _execute_liquidity_grab_order(
        self, symbol, ltf_result, atf_result, market_price, pair_config, precision
    ):
        """执行流动性抓取下单"""
        step = "6"

        entry_price = self.toDecimal(ltf_result["entry_price"])
        order_side = ltf_result["ltf_side"]

        # 检查价格变化
        latest_order_price = self.toDecimal(self.place_order_prices.get(symbol, 0))
        if entry_price == latest_order_price:
            self.logger.info(
                f"{symbol} : {step}. 下单价格{entry_price:.{precision}f}未变化，跳过"
            )
            return

        # 取消现有订单并下新单
        self.cancel_all_orders(symbol=symbol)
        self.place_order(
            symbol=symbol, price=entry_price, side=order_side, pair_config=pair_config
        )
        self.place_order_prices[symbol] = entry_price

        # 准备飞书通知消息
        notification_msg = (
            f"流动性抓取{order_side}单已下\n"
            f"价格: {entry_price:.{precision}f}\n"
            f"形态类型: {atf_result.liquidity_result[self.EQUAL_POINTS_TYPE_COL]}\n"
            f"流动性价格: {atf_result.liquidity_result[self.EQUAL_POINTS_PRICE_COL]:.{precision}f}"
        )

        # 如果有AI验证信息，添加到通知中
        ai_validation = atf_result.confluence_result.get("ai_validation")
        if ai_validation:
            notification_msg += (
                f"\n\nAI验证信息:\n"
                f"置信度: {ai_validation['confidence']:.3f}\n"
                f"模型版本: {ai_validation.get('model_version', 'N/A')}\n"
                f"分析: {ai_validation.get('reasoning', 'N/A')}"
            )

        # 发送飞书通知
        self.send_feishu_notification(symbol, notification_msg)

        self.logger.info(
            f"{symbol} : {step}. 流动性抓取{order_side}单已下，价格={entry_price:.{precision}f}"
        )

    def cleanup(self):
        """清理资源，关闭AI验证协调器"""
        if self.ai_validation_coordinator:
            try:
                self.ai_validation_coordinator.close()
                self.logger.info("AI验证协调器已关闭")
            except Exception as e:
                self.logger.error(f"关闭AI验证协调器时出错: {e}")
