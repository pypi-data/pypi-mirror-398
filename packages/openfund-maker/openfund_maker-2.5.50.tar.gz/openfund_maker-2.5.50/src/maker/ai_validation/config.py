"""
AI 验证系统配置管理

负责加载、验证和管理 AI 验证系统的配置信息。
支持从 YAML/JSON 文件、环境变量和代码中加载配置。
支持配置热重载功能。
"""

import os
import json
import yaml
import logging
import threading
import time
from typing import Dict, Any, Optional, Callable
from pathlib import Path
from datetime import datetime

from .data_models import AIValidationConfig, AIServiceConfig, AIPromptConfig
from .exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file
        self._validation_config: Optional[AIValidationConfig] = None
        self._service_config: Optional[AIServiceConfig] = None
        self._prompt_config: Optional[AIPromptConfig] = None
        self._raw_config: Dict[str, Any] = {}
        self._last_modified: Optional[float] = None
        self._watch_thread: Optional[threading.Thread] = None
        self._watch_enabled: bool = False
        self._reload_callbacks: list[Callable[[], None]] = []

    def load_config(self, config_data: Optional[Dict[str, Any]] = None) -> None:
        """
        加载配置

        Args:
            config_data: 直接提供的配置数据，如果为None则从文件加载
        """
        try:
            if config_data:
                self._raw_config = config_data
            else:
                self._raw_config = self._load_from_file()

            # 合并环境变量
            self._merge_env_variables()

            # 创建配置对象
            self._create_config_objects()

            logger.info("AI验证配置加载成功")

        except Exception as e:
            raise ConfigurationError(f"配置加载失败: {str(e)}")

    def _load_from_file(self) -> Dict[str, Any]:
        """从文件加载配置，支持 YAML 和 JSON 格式"""
        if not self.config_file:
            # 尝试默认配置文件路径（优先使用主配置文件）
            default_paths = [
                "maker_config.yaml",
                "openfund-maker/maker_config.yaml",
                "ai_validation_config.yaml",
                "config/ai_validation.yaml",
                "ai_validation_config.json",
                "config/ai_validation.json",
            ]

            for path in default_paths:
                if os.path.exists(path):
                    self.config_file = path
                    break

            if not self.config_file:
                logger.warning("未找到配置文件，使用默认配置")
                return {}

        try:
            file_path = Path(self.config_file)

            # 记录文件修改时间
            self._last_modified = file_path.stat().st_mtime

            with open(self.config_file, "r", encoding="utf-8") as f:
                # 根据文件扩展名选择解析器
                if file_path.suffix.lower() in [".yaml", ".yml"]:
                    config = yaml.safe_load(f) or {}
                elif file_path.suffix.lower() == ".json":
                    config = json.load(f) or {}
                else:
                    # 尝试 YAML 解析
                    try:
                        config = yaml.safe_load(f) or {}
                    except yaml.YAMLError:
                        # 如果 YAML 失败，尝试 JSON
                        f.seek(0)
                        config = json.load(f) or {}

                logger.info(f"从文件加载配置: {self.config_file}")
                return config

        except FileNotFoundError:
            logger.warning(f"配置文件不存在: {self.config_file}")
            return {}
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            raise ConfigurationError(f"配置文件格式错误: {str(e)}")

    def _merge_env_variables(self) -> None:
        """合并环境变量配置"""
        env_mappings = {
            "AI_VALIDATION_ENABLED": ("ai_validation", "enabled"),
            "AI_VALIDATION_CONFIDENCE_THRESHOLD": (
                "ai_validation",
                "confidence_threshold",
            ),
            "AI_VALIDATION_TIMEOUT": ("ai_validation", "timeout_seconds"),
            "AI_VALIDATION_MAX_RETRIES": ("ai_validation", "max_retries"),
            "AI_VALIDATION_FALLBACK_MODE": ("ai_validation", "fallback_mode"),
            "AI_VALIDATION_DATA_CANDLES": ("ai_validation", "data_collection_candles"),
            "AI_SERVICE_ENDPOINT": ("ai_service", "endpoint_url"),
            "AI_SERVICE_API_KEY": ("ai_service", "api_key"),
            "AI_SERVICE_MODEL_VERSION": ("ai_service", "model_version"),
            "AI_SERVICE_TIMEOUT": ("ai_service", "timeout"),
            "AI_SERVICE_MAX_RETRIES": ("ai_service", "max_retries"),
        }

        for env_key, (section, config_key) in env_mappings.items():
            env_value = os.getenv(env_key)
            if env_value is not None:
                if section not in self._raw_config:
                    self._raw_config[section] = {}

                # 类型转换
                if config_key in ["enabled"]:
                    env_value = env_value.lower() in ("true", "1", "yes", "on")
                elif config_key in ["confidence_threshold"]:
                    env_value = float(env_value)
                elif config_key in [
                    "timeout_seconds",
                    "max_retries",
                    "data_collection_candles",
                    "timeout",
                ]:
                    env_value = int(env_value)

                self._raw_config[section][config_key] = env_value
                logger.debug(
                    f"从环境变量设置配置: {section}.{config_key} = {env_value}"
                )

    def _create_config_objects(self) -> None:
        """创建配置对象"""
        # AI验证配置
        validation_config_data = self._raw_config.get("ai_validation", {})
        self._validation_config = AIValidationConfig(
            enabled=validation_config_data.get("enabled", True),
            enable_htf_trend_analysis=validation_config_data.get("enable_htf_trend_analysis", True),
            confidence_threshold=validation_config_data.get(
                "confidence_threshold", 0.6
            ),
            timeout_seconds=validation_config_data.get("timeout_seconds", 5),
            max_retries=validation_config_data.get("max_retries", 3),
            fallback_mode=validation_config_data.get("fallback_mode", "skip"),
            data_collection_candles=validation_config_data.get(
                "data_collection_candles", 200
            ),
            enable_caching=validation_config_data.get("enable_caching", True),
            cache_ttl_seconds=validation_config_data.get("cache_ttl_seconds", 300),
        )

        # AI服务配置
        service_config_data = self._raw_config.get("ai_service", {})
        if not service_config_data.get("endpoint_url"):
            raise ConfigurationError(
                "AI服务端点URL未配置", config_key="ai_service.endpoint_url"
            )
        if not service_config_data.get("api_key"):
            raise ConfigurationError(
                "AI服务API密钥未配置", config_key="ai_service.api_key"
            )

        self._service_config = AIServiceConfig(
            endpoint_url=service_config_data["endpoint_url"],
            api_key=service_config_data["api_key"],
            model_version=service_config_data.get("model_version", "v1.0"),
            timeout=service_config_data.get("timeout", 5),
            max_retries=service_config_data.get("max_retries", 3),
            headers=service_config_data.get("headers", {}),
        )

        # AI提示词配置（从独立文件加载）
        prompt_config_data = self._load_prompt_config()
        self._prompt_config = AIPromptConfig(
            system_prompt=prompt_config_data.get("system_prompt", ""),
            htf_trend_analysis_prompt=prompt_config_data.get("htf_trend_analysis_prompt", ""),
        )

    def _load_prompt_config(self) -> Dict[str, Any]:
        """从独立文件加载提示词配置"""
        prompt_files = [
            "prompt_templates.yaml",
            "openfund-maker/prompt_templates.yaml",
        ]
        for path in prompt_files:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f) or {}
                        logger.info(f"从文件加载提示词配置: {path}")
                        return data.get("ai_prompt", {})
                except Exception as e:
                    logger.warning(f"加载提示词配置失败: {e}")
        return {}

    @property
    def validation_config(self) -> AIValidationConfig:
        """获取AI验证配置"""
        if self._validation_config is None:
            raise ConfigurationError("配置未加载，请先调用 load_config()")
        return self._validation_config

    @property
    def service_config(self) -> AIServiceConfig:
        """获取AI服务配置"""
        if self._service_config is None:
            raise ConfigurationError("配置未加载，请先调用 load_config()")
        return self._service_config

    @property
    def prompt_config(self) -> AIPromptConfig:
        """获取AI提示词配置"""
        if self._prompt_config is None:
            raise ConfigurationError("配置未加载，请先调用 load_config()")
        return self._prompt_config

    def get_raw_config(self) -> Dict[str, Any]:
        """获取原始配置数据"""
        return self._raw_config.copy()

    def validate_config(self) -> bool:
        """验证配置有效性"""
        try:
            # 验证配置对象是否已创建
            _ = self.validation_config
            _ = self.service_config

            # 可以添加更多验证逻辑
            logger.info("配置验证通过")
            return True

        except Exception as e:
            logger.error(f"配置验证失败: {str(e)}")
            return False

    def reload_config(self) -> None:
        """重新加载配置"""
        logger.info("重新加载配置")
        self._validation_config = None
        self._service_config = None
        self._raw_config = {}
        self.load_config()

        # 触发重载回调
        for callback in self._reload_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"配置重载回调执行失败: {str(e)}")

    def register_reload_callback(self, callback: Callable[[], None]) -> None:
        """
        注册配置重载回调函数

        Args:
            callback: 配置重载时调用的回调函数
        """
        if callback not in self._reload_callbacks:
            self._reload_callbacks.append(callback)
            logger.debug(f"注册配置重载回调: {callback.__name__}")

    def unregister_reload_callback(self, callback: Callable[[], None]) -> None:
        """
        取消注册配置重载回调函数

        Args:
            callback: 要取消的回调函数
        """
        if callback in self._reload_callbacks:
            self._reload_callbacks.remove(callback)
            logger.debug(f"取消注册配置重载回调: {callback.__name__}")

    def enable_auto_reload(self, check_interval: int = 5) -> None:
        """
        启用配置文件自动重载

        Args:
            check_interval: 检查间隔（秒）
        """
        if self._watch_enabled:
            logger.warning("配置文件监控已启用")
            return

        if not self.config_file or not os.path.exists(self.config_file):
            logger.warning("配置文件不存在，无法启用自动重载")
            return

        self._watch_enabled = True
        self._watch_thread = threading.Thread(
            target=self._watch_config_file,
            args=(check_interval,),
            daemon=True,
            name="ConfigFileWatcher",
        )
        self._watch_thread.start()
        logger.info(f"启用配置文件自动重载，检查间隔: {check_interval}秒")

    def disable_auto_reload(self) -> None:
        """禁用配置文件自动重载"""
        if not self._watch_enabled:
            return

        self._watch_enabled = False
        if self._watch_thread:
            self._watch_thread.join(timeout=2)
            self._watch_thread = None
        logger.info("禁用配置文件自动重载")

    def _watch_config_file(self, check_interval: int) -> None:
        """
        监控配置文件变化

        Args:
            check_interval: 检查间隔（秒）
        """
        logger.debug("配置文件监控线程启动")

        while self._watch_enabled:
            try:
                if self.config_file and os.path.exists(self.config_file):
                    current_mtime = os.path.getmtime(self.config_file)

                    if self._last_modified and current_mtime > self._last_modified:
                        logger.info(f"检测到配置文件变化: {self.config_file}")
                        try:
                            self.reload_config()
                            logger.info("配置文件重载成功")
                        except Exception as e:
                            logger.error(f"配置文件重载失败: {str(e)}")

                time.sleep(check_interval)

            except Exception as e:
                logger.error(f"配置文件监控错误: {str(e)}")
                time.sleep(check_interval)

        logger.debug("配置文件监控线程停止")

    def get_config_info(self) -> Dict[str, Any]:
        """
        获取配置信息摘要

        Returns:
            配置信息字典
        """
        return {
            "config_file": self.config_file,
            "last_modified": (
                datetime.fromtimestamp(self._last_modified).isoformat()
                if self._last_modified
                else None
            ),
            "auto_reload_enabled": self._watch_enabled,
            "validation_config": {
                "enabled": (
                    self._validation_config.enabled if self._validation_config else None
                ),
                "confidence_threshold": (
                    self._validation_config.confidence_threshold
                    if self._validation_config
                    else None
                ),
                "timeout_seconds": (
                    self._validation_config.timeout_seconds
                    if self._validation_config
                    else None
                ),
            },
            "service_config": {
                "endpoint_url": (
                    self._service_config.endpoint_url if self._service_config else None
                ),
                "model_version": (
                    self._service_config.model_version if self._service_config else None
                ),
            },
        }


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """获取全局配置管理器实例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def initialize_config(
    config_file: Optional[str] = None, config_data: Optional[Dict[str, Any]] = None
) -> None:
    """
    初始化全局配置

    Args:
        config_file: 配置文件路径
        config_data: 直接提供的配置数据
    """
    global _config_manager
    _config_manager = ConfigManager(config_file)
    _config_manager.load_config(config_data)


def get_validation_config() -> AIValidationConfig:
    """获取AI验证配置"""
    return get_config_manager().validation_config


def get_service_config() -> AIServiceConfig:
    """获取AI服务配置"""
    return get_config_manager().service_config


def get_prompt_config() -> AIPromptConfig:
    """获取AI提示词配置"""
    return get_config_manager().prompt_config
