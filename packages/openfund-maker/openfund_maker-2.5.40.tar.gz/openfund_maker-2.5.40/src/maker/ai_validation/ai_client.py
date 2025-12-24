"""
AI验证服务客户端

负责与外部AI模型服务通信，提供HTTP客户端、连接池管理、
重试机制和健康检查功能。
"""

import logging
import time
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter

from .data_models import AIInputData, AIValidationResponse, AIServiceConfig, AIPromptConfig, DEFAULT_SYSTEM_PROMPT
from .exceptions import AIServiceError, AIServiceTimeoutError, AIServiceUnavailableError

logger = logging.getLogger(__name__)


class AIValidationClient:
    """
    AI验证服务客户端

    提供HTTP通信、连接池管理、自动重试和健康检查功能。
    支持配置超时、重试次数和连接池大小。
    """

    def __init__(
        self,
        config: AIServiceConfig,
        pool_connections: int = 10,
        pool_maxsize: int = 30,
        prompt_config: Optional[AIPromptConfig] = None,
    ):
        """
        初始化AI客户端

        Args:
            config: AI服务配置
            pool_connections: 连接池数量
            pool_maxsize: 连接池最大大小
            prompt_config: AI提示词配置
        """
        self.config = config
        self.pool_connections = pool_connections
        self.pool_maxsize = pool_maxsize
        self.prompt_config = prompt_config or AIPromptConfig()
        self.session: Optional[requests.Session] = None
        self._health_status: Optional[bool] = None
        self._last_health_check: Optional[datetime] = None
        self._health_check_interval = timedelta(seconds=30)

        logger.info(
            f"AI客户端初始化完成: {config.endpoint_url}, "
            f"连接池数量: {pool_connections}, "
            f"连接池大小: {pool_maxsize}"
        )

    def _get_session(self) -> requests.Session:
        """
        获取或创建HTTP会话

        使用连接池提高性能，配置超时和请求头。

        Returns:
            requests.Session: HTTP会话对象
        """
        if self.session is None:
            # 创建会话
            self.session = requests.Session()
            
            # 配置连接池
            adapter = HTTPAdapter(
                pool_connections=self.pool_connections,
                pool_maxsize=self.pool_maxsize,
                max_retries=0,  # 手动处理重试
            )
            self.session.mount('http://', adapter)
            self.session.mount('https://', adapter)

            # 配置请求头
            self.session.headers.update({
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.api_key}",
                "User-Agent": "OpenFund-AI-Client/1.0",
                **self.config.headers,
            })

            logger.debug("创建新的HTTP会话，连接池已配置")

        return self.session

    def validate_pattern(self, input_data: AIInputData) -> AIValidationResponse:
        """
        调用AI服务进行形态验证

        实现自动重试机制（最多3次），使用指数退避策略。
        处理超时、网络错误和服务不可用等各种错误类型。

        Args:
            input_data: AI输入数据

        Returns:
            AIValidationResponse: AI验证响应

        Raises:
            AIServiceTimeoutError: 服务超时
            AIServiceUnavailableError: 服务不可用
            AIServiceError: 其他服务错误
        """
        last_exception = None

        for attempt in range(self.config.max_retries + 1):
            try:
                logger.debug(
                    f"调用AI服务，尝试 {attempt + 1}/{self.config.max_retries + 1}"
                )

                start_time = time.time()
                response = self._make_request(input_data)
                elapsed_time = time.time() - start_time

                logger.info(
                    f"AI验证成功，置信度: {response.confidence:.3f}, "
                    f"耗时: {elapsed_time:.2f}秒"
                )
                return response

            except AIServiceTimeoutError as e:
                last_exception = e
                if attempt == self.config.max_retries:
                    logger.error(f"AI服务超时，已达到最大重试次数: {str(e)}")
                    raise

                wait_time = self._calculate_backoff(attempt)
                logger.warning(
                    f"AI服务超时，{wait_time}秒后重试 "
                    f"{attempt + 1}/{self.config.max_retries}"
                )
                time.sleep(wait_time)

            except AIServiceUnavailableError as e:
                last_exception = e
                if attempt == self.config.max_retries:
                    logger.error(f"AI服务不可用，已达到最大重试次数: {str(e)}")
                    raise

                wait_time = self._calculate_backoff(attempt)
                logger.warning(
                    f"AI服务不可用，{wait_time}秒后重试 "
                    f"{attempt + 1}/{self.config.max_retries}"
                )
                time.sleep(wait_time)

            except AIServiceError as e:
                last_exception = e
                # 对于客户端错误（4xx），不重试
                if e.status_code and 400 <= e.status_code < 500:
                    logger.error(f"AI服务客户端错误，不重试: {str(e)}")
                    raise

                if attempt == self.config.max_retries:
                    logger.error(f"AI服务错误，已达到最大重试次数: {str(e)}")
                    raise

                wait_time = self._calculate_backoff(attempt)
                logger.warning(
                    f"AI服务错误，{wait_time}秒后重试 "
                    f"{attempt + 1}/{self.config.max_retries}: {str(e)}"
                )
                time.sleep(wait_time)

            except Exception as e:
                last_exception = e
                logger.error(f"未预期的错误: {str(e)}", exc_info=True)
                if attempt == self.config.max_retries:
                    raise AIServiceError(f"AI服务调用失败: {str(e)}")

                wait_time = self._calculate_backoff(attempt)
                time.sleep(wait_time)

        # 理论上不应该到达这里，但作为保险
        if last_exception:
            raise last_exception
        raise AIServiceError("AI服务调用失败，已达到最大重试次数")

    def _calculate_backoff(self, attempt: int) -> float:
        """
        计算指数退避等待时间

        使用指数退避策略：1秒、2秒、4秒...

        Args:
            attempt: 当前重试次数（从0开始）

        Returns:
            float: 等待时间（秒）
        """
        base_delay = 1.0
        max_delay = 10.0
        delay = min(base_delay * (2**attempt), max_delay)
        return delay

    def _make_request_raw(self, request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        发起原始HTTP请求到AI服务（用于自定义请求）

        Args:
            request_data: 原始请求数据

        Returns:
            Dict: AI服务的原始响应数据，失败时返回None
        """
        session = self._get_session()

        try:
            logger.debug(f"发送原始AI请求: {self.config.endpoint_url}")

            # 构建请求头
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.api_key}"
            }

            # 发送请求
            response = session.post(
                self.config.endpoint_url,
                json=request_data,
                headers=headers,
                timeout=self.config.timeout
            )

            # 成功响应
            if response.status_code == 200:
                response_data = response.json()
                logger.debug(f"AI原始响应成功")
                return response_data
            else:
                logger.warning(f"AI服务响应错误: HTTP {response.status_code}")
                if response.text:
                    logger.debug(f"错误详情: {response.text}")
                return None

        except requests.exceptions.Timeout:
            logger.error(f"AI服务请求超时: {self.config.timeout}秒")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("AI服务连接失败")
            return None
        except Exception as e:
            logger.error(f"AI服务请求异常: {str(e)}")
            return None

    def _make_request(self, input_data: AIInputData) -> AIValidationResponse:
        """
        发起HTTP请求到AI服务

        处理各种HTTP状态码和网络错误，提供详细的错误信息。

        Args:
            input_data: AI输入数据

        Returns:
            AIValidationResponse: AI验证响应

        Raises:
            AIServiceTimeoutError: 请求超时
            AIServiceUnavailableError: 服务不可用
            AIServiceError: 其他服务错误
        """
        session = self._get_session()

        try:
            # 将输入数据转换为OpenAI格式的请求
            request_data = self._format_openai_request(input_data)

            # 打印发送给AI的提示词
            logger.info("=" * 80)
            logger.info("发送给AI的提示词:")
            logger.info("-" * 80)
            for msg in request_data.get("messages", []):
                logger.info(f"[{msg['role'].upper()}]")
                logger.info(msg['content'])
                logger.info("-" * 80)
            logger.info("=" * 80)

            logger.debug(
                f"发送AI验证请求: {self.config.endpoint_url}, "
                f"交易对: {input_data.market_data.trading_pair}"
            )

            # 记录请求开始时间
            request_start = time.time()
            
            # 发送请求
            response = session.post(
                self.config.endpoint_url,
                json=request_data,
                timeout=self.config.timeout
            )
            
            # 记录请求耗时
            request_duration = time.time() - request_start
            logger.debug(f"AI服务响应耗时: {request_duration:.2f}秒")

            # 成功响应
            if response.status_code == 200:
                response_data = response.json()
                logger.debug(f"AI完整响应数据: {response_data}")
                return self._parse_openai_response(response_data)

            # 超时相关错误
            elif response.status_code in [408, 504]:
                raise AIServiceTimeoutError(
                    f"AI服务响应超时: HTTP {response.status_code}",
                    timeout_seconds=self.config.timeout,
                )

            # 服务不可用错误（5xx）
            elif response.status_code >= 500:
                error_text = response.text
                raise AIServiceUnavailableError(
                    f"AI服务不可用: HTTP {response.status_code}",
                    status_code=response.status_code,
                    response_data={"error": error_text},
                )

            # 客户端错误（4xx）
            elif response.status_code >= 400:
                error_text = response.text
                error_message = self._parse_error_message(
                    error_text, response.status_code
                )
                raise AIServiceError(
                    error_message,
                    status_code=response.status_code,
                    response_data={"error": error_text},
                )

            # 其他状态码
            else:
                error_text = response.text
                raise AIServiceError(
                    f"AI服务返回未预期状态码: HTTP {response.status_code}",
                    status_code=response.status_code,
                    response_data={"error": error_text},
                )

        except requests.exceptions.Timeout:
            raise AIServiceTimeoutError(
                f"AI服务调用超时: {self.config.timeout}秒",
                timeout_seconds=self.config.timeout,
            )

        except requests.exceptions.ConnectionError as e:
            raise AIServiceUnavailableError(f"无法连接到AI服务: {str(e)}")

        except requests.exceptions.RequestException as e:
            raise AIServiceError(f"网络错误: {str(e)}")

        except AIServiceError:
            # 重新抛出已经处理的异常
            raise

        except Exception as e:
            logger.error(f"请求处理异常: {str(e)}", exc_info=True)
            raise AIServiceError(f"请求处理失败: {str(e)}")

    def _parse_error_message(self, error_text: str, status_code: int) -> str:
        """
        解析错误消息

        Args:
            error_text: 错误文本
            status_code: HTTP状态码

        Returns:
            str: 格式化的错误消息
        """
        error_messages = {
            400: "请求参数错误",
            401: "API密钥无效或未授权",
            403: "访问被拒绝",
            404: "AI服务端点不存在",
            429: "请求频率超限",
        }

        base_message = error_messages.get(status_code, "AI服务返回错误")
        return f"{base_message}: HTTP {status_code} - {error_text[:200]}"

    def _format_htf_atf_context(self, data_dict: Dict[str, Any]) -> str:
        """
        格式化HTF/ATF上下文信息
        
        Args:
            data_dict: 包含additional_features的数据字典
            
        Returns:
            str: 格式化后的HTF/ATF上下文文本
        """
        def get_value(d, key, default='N/A'):
            """获取值，如果为 None 则返回默认值"""
            val = d.get(key)
            return val if val is not None else default
        
        result = []
        additional = data_dict.get("additional_features", {})
        
        # HTF信息
        if "htf_context" in additional:
            htf = additional["htf_context"]
            result.append("HTF (高时间框架) 分析:")
            result.append(f"  时间框架: {get_value(htf, 'timeframe')}")
            result.append(f"  趋势方向: {get_value(htf, 'trend')}")
            result.append(f"  结构类型: {get_value(htf, 'structure_type')}")
            result.append(f"  结构最高价: {get_value(htf, 'structure_high')}")
            result.append(f"  结构最低价: {get_value(htf, 'structure_low')}")
            result.append(f"  支撑位: {get_value(htf, 'support_price')}")
            result.append(f"  阻力位: {get_value(htf, 'resistance_price')}")
            if htf.get("support_pd_array"):
                pd = htf["support_pd_array"]
                result.append(f"  支撑PDArray: {get_value(pd, 'low')} - {get_value(pd, 'high')}")
            if htf.get("resistance_pd_array"):
                pd = htf["resistance_pd_array"]
                result.append(f"  阻力PDArray: {get_value(pd, 'low')} - {get_value(pd, 'high')}")
        
        # ATF信息
        if "atf_context" in additional:
            atf = additional["atf_context"]
            result.append("\nATF (分析时间框架) 分析:")
            result.append(f"  时间框架: {get_value(atf, 'timeframe')}")
            result.append(f"  趋势方向: {get_value(atf, 'trend')}")
            result.append(f"  结构类型: {get_value(atf, 'structure_type')}")
            result.append(f"  结构最高价: {get_value(atf, 'structure_high')}")
            result.append(f"  结构最低价: {get_value(atf, 'structure_low')}")
            result.append(f"  支撑位: {get_value(atf, 'support_price')}")
            result.append(f"  阻力位: {get_value(atf, 'resistance_price')}")
            if atf.get("support_pd_array"):
                pd = atf["support_pd_array"]
                result.append(f"  支撑PDArray: {get_value(pd, 'low')} - {get_value(pd, 'high')}")
            if atf.get("resistance_pd_array"):
                pd = atf["resistance_pd_array"]
                result.append(f"  阻力PDArray: {get_value(pd, 'low')} - {get_value(pd, 'high')}")
        
        return "\n".join(result)

    def _format_htf_atf_candles(self, data_dict: Dict[str, Any]) -> str:
        """
        格式化HTF/ATF K线数据
        
        Args:
            data_dict: 包含additional_features的数据字典
            
        Returns:
            str: 格式化后的HTF/ATF K线文本
        """
        result = []
        additional = data_dict.get("additional_features", {})
        
        # HTF K线（最近10条）
        if "htf_candles" in additional:
            htf_candles = additional["htf_candles"]
            result.append("HTF K线（最近10条）:")
            for candle in htf_candles:
                result.append(
                    f"  {candle.get('timestamp', 'N/A')}: "
                    f"O{candle.get('open', 'N/A')} H{candle.get('high', 'N/A')} "
                    f"L{candle.get('low', 'N/A')} C{candle.get('close', 'N/A')} "
                    f"V{candle.get('volume', 0):.0f}"
                )
        
        # ATF K线（最近20条）
        if "atf_candles" in additional:
            atf_candles = additional["atf_candles"]
            result.append("\nATF K线（最近20条）:")
            for candle in atf_candles:
                result.append(
                    f"  {candle.get('timestamp', 'N/A')}: "
                    f"O{candle.get('open', 'N/A')} H{candle.get('high', 'N/A')} "
                    f"L{candle.get('low', 'N/A')} C{candle.get('close', 'N/A')} "
                    f"V{candle.get('volume', 0):.0f}"
                )
        
        return "\n".join(result)

    def _format_openai_request(self, input_data: AIInputData) -> Dict[str, Any]:
        """
        将输入数据格式化为OpenAI兼容的请求格式

        Args:
            input_data: AI输入数据

        Returns:
            Dict[str, Any]: OpenAI格式的请求数据
        """
        # 将市场数据和形态候选转换为文本描述
        data_dict = input_data.to_dict()

        # 使用配置中的系统提示词
        system_prompt = self.prompt_config.system_prompt

        # 构建用户消息
        user_message = f"""交易对: {data_dict['trading_pair']}

"""
        # 添加HTF/ATF上下文信息（如果存在）
        htf_atf_context = self._format_htf_atf_context(data_dict)
        if htf_atf_context:
            user_message += f"{htf_atf_context}\n\n"
            logger.debug(f"HTF/ATF上下文数据: {htf_atf_context}")
        
        # 添加HTF/ATF K线数据（如果存在）
        htf_atf_candles = self._format_htf_atf_candles(data_dict)
        if htf_atf_candles:
            user_message += f"{htf_atf_candles}\n\n"

        # 添加流动性详情（如果存在 equal_liquidity_df）
        if 'additional_features' in data_dict and 'equal_liquidity_df' in data_dict['additional_features']:
            equal_liquidity_df = data_dict['additional_features']['equal_liquidity_df']
            liquidity_text = self._format_equal_liquidity_df(equal_liquidity_df)
            if liquidity_text:
                user_message += f"""流动性详情:
{liquidity_text}

"""

        # 添加订单信息（如果存在）
        if 'additional_features' in data_dict and 'opportunity_info' in data_dict['additional_features']:
            opportunity_info = data_dict['additional_features']['opportunity_info']
            user_message += f"""订单: 下单价格{opportunity_info.get('target_level', 'N/A')}, 流动性类型{opportunity_info.get('liquidity_type', 'N/A')}, 止盈价格{opportunity_info.get('tp_target', 'N/A')}"""

        user_message += "\n\n返回JSON分析结果。"

        # 构建OpenAI格式的请求
        request_data = {
            "model": self.config.model_version,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.3,
            "max_tokens": 2000,  # 增加限制以确保完整JSON响应
        }
        
        # 只有在模型支持时才添加response_format
        # Moonshot的某些模型可能不支持这个参数
        if "gpt" in self.config.model_version.lower() or "kimi" in self.config.model_version.lower():
            request_data["response_format"] = {"type": "json_object"}
        
        return request_data

    def _format_equal_liquidity_df(self, df) -> str:
        """格式化等高等低流动性DataFrame为提示文本"""
        import pandas as pd
        
        if df is None or (isinstance(df, pd.DataFrame) and df.empty):
            return ""
        
        result = []
        # 筛选有等高等低点的行
        if 'has_equal_points' in df.columns:
            df_filtered = df[df['has_equal_points'] == True]
        else:
            df_filtered = df
        
        for idx, row in df_filtered.iterrows():
            eq_type = row.get('equal_points_type', 'N/A')
            eq_price = row.get('equal_points_price', 'N/A')
            timestamp = row.get('timestamp', idx)
            result.append(f"  {eq_type}: 价格{eq_price}, 时间{timestamp}")
        
        return "\n".join(result)

    def _format_candles_for_prompt(self, candles: List[Dict[str, Any]]) -> str:
        """格式化K线数据为提示文本（精简版本）"""
        result = []
        for candle in candles:  # 使用传入的K线数据
            result.append(
                f"{candle['timestamp']}: O{candle['open']} H{candle['high']} "
                f"L{candle['low']} C{candle['close']} V{candle['volume']:.0f}"
            )
        return "\n".join(result)

    def _parse_openai_response(
        self, response_data: Dict[str, Any]
    ) -> AIValidationResponse:
        """
        解析OpenAI格式的响应

        Args:
            response_data: OpenAI API响应数据

        Returns:
            AIValidationResponse: 解析后的验证响应

        Raises:
            AIServiceError: 解析失败
        """
        try:
            # 从OpenAI响应中提取内容
            if "choices" not in response_data or not response_data["choices"]:
                raise AIServiceError("OpenAI响应缺少choices字段")

            message = response_data["choices"][0]["message"]
            # DeepSeek reasoner模型使用reasoning_content字段
            content = message.get("reasoning_content") or message.get("content", "")
            logger.debug(f"AI原始响应内容: {content}")

            # 解析JSON内容
            import json
            import re

            try:
                parsed_content = json.loads(content)
                logger.debug(f"AI返回的JSON结果: {json.dumps(parsed_content, ensure_ascii=False)}")
            except json.JSONDecodeError as e:
                logger.warning(f"AI响应不是有效的JSON，尝试提取: {content[:200]}")
                # 尝试从markdown代码块中提取JSON
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
                if not json_match:
                    # 尝试直接查找JSON对象
                    json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
                
                if json_match:
                    try:
                        parsed_content = json.loads(json_match.group(1) if json_match.lastindex else json_match.group(0))
                        logger.info(f"从响应中提取的JSON结果: {json.dumps(parsed_content, ensure_ascii=False)}")
                    except json.JSONDecodeError:
                        parsed_content = {
                            "confidence": 0.5,
                            "reasoning": content[:200],
                            "feature_importance": {},
                            "processing_time": 0.0,
                        }
                else:
                    parsed_content = {
                        "confidence": 0.5,
                        "reasoning": content[:200],
                        "feature_importance": {},
                        "processing_time": 0.0,
                    }

            return AIValidationResponse(
                confidence=parsed_content.get("confidence", 0.0),
                reasoning=parsed_content.get("reasoning", ""),
                feature_importance=parsed_content.get("feature_importance", {}),
                model_version=self.config.model_version,
                processing_time=parsed_content.get("processing_time", 0.0),
                side=parsed_content.get("side", ""),
                raw_response=response_data,
            )
        except Exception as e:
            logger.error(f"解析OpenAI响应失败: {str(e)}", exc_info=True)
            raise AIServiceError(f"AI响应解析失败: {str(e)}")

    def health_check(self, force: bool = False) -> bool:
        """
        检查AI服务健康状态（OpenAI兼容版本）

        使用缓存机制避免频繁检查，默认缓存30秒。
        由于OpenAI API没有专门的health端点，这里通过发送一个简单的测试请求来检查。

        Args:
            force: 是否强制检查，忽略缓存

        Returns:
            bool: 服务是否健康
        """
        # 检查缓存
        if not force and self._health_status is not None and self._last_health_check:
            if datetime.now() - self._last_health_check < self._health_check_interval:
                logger.debug(f"使用缓存的健康状态: {self._health_status}")
                return self._health_status

        try:
            session = self._get_session()

            logger.debug(f"执行AI服务健康检查: {self.config.endpoint_url}")

            # 发送一个简单的测试请求
            test_request = {
                "model": self.config.model_version,
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 5,
            }

            # 使用较短的超时时间进行健康检查
            response = session.post(
                self.config.endpoint_url,
                json=test_request,
                timeout=5
            )
            
            is_healthy = response.status_code == 200

            if is_healthy:
                logger.info("AI服务健康检查通过")
            else:
                logger.warning(f"AI服务健康检查失败: HTTP {response.status_code}")

            # 更新缓存
            self._health_status = is_healthy
            self._last_health_check = datetime.now()

            return is_healthy

        except requests.exceptions.Timeout:
            logger.warning("AI服务健康检查超时")
            self._health_status = False
            self._last_health_check = datetime.now()
            return False

        except requests.exceptions.ConnectionError as e:
            logger.warning(f"AI服务健康检查连接失败: {str(e)}")
            self._health_status = False
            self._last_health_check = datetime.now()
            return False

        except Exception as e:
            logger.warning(f"AI服务健康检查失败: {str(e)}")
            self._health_status = False
            self._last_health_check = datetime.now()
            return False

    def get_service_info(self) -> Dict[str, Any]:
        """
        获取AI服务信息（OpenAI兼容版本）

        OpenAI API没有专门的info端点，返回配置信息。

        Returns:
            Dict[str, Any]: 服务信息，包括版本、状态等
        """
        return {
            "endpoint": self.config.endpoint_url,
            "model": self.config.model_version,
            "timeout": self.config.timeout,
            "max_retries": self.config.max_retries,
            "api_type": "openai_compatible",
        }

    def get_health_status(self) -> Optional[bool]:
        """
        获取缓存的健康状态

        Returns:
            Optional[bool]: 健康状态，None表示未检查过
        """
        return self._health_status

    def reset_health_cache(self) -> None:
        """重置健康检查缓存"""
        self._health_status = None
        self._last_health_check = None
        logger.debug("健康检查缓存已重置")

    def close(self):
        """
        关闭客户端，释放资源

        关闭HTTP会话和连接池。
        """
        if self.session:
            self.session.close()
            logger.info("AI客户端会话已关闭")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()
