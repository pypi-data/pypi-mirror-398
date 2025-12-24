import logging
import logging.config
import yaml
import importlib
import importlib.metadata
import os
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.schedulers.blocking import BlockingScheduler
from datetime import datetime
from pyfiglet import Figlet
from typing import Dict, Any
from dotenv import load_dotenv
from maker.ai_validation import initialize_config, AIValidationCoordinator

def read_config_file(file_path):
    try:
        # 打开 YAML 文件
        with open(file_path, "r", encoding="utf-8") as file:
            # 读取文件内容并展开环境变量
            yaml_str = file.read()
            expanded_yaml = os.path.expandvars(yaml_str)
            # 使用 yaml.safe_load 方法解析 YAML 文件内容
            data = yaml.safe_load(expanded_yaml)
            return data
    except FileNotFoundError:
        raise Exception(f"文件 {file_path} 未找到。")
    except yaml.YAMLError as e:
        raise Exception(f"解析 {file_path} 文件时出错: {e}")


def run_bot(bot: Any, logger: logging.Logger) -> None:
    """执行机器人监控任务"""
    try:
        bot.monitor_klines()
    except Exception as e:
        logger.error(f"执行任务时发生错误: {str(e)}", exc_info=True)


def calculate_next_run_time(current_time: datetime, interval: int) -> datetime:
    """计算下一次运行时间"""
    next_run = current_time.replace(second=58, microsecond=0)
    current_minute = next_run.minute
    next_interval = ((current_minute // interval) + 1) * interval - 1

    if next_interval >= 60:
        next_interval %= 60
        next_run = next_run.replace(hour=next_run.hour + 1)

    return next_run.replace(minute=next_interval)


def setup_scheduler(bot: Any, logger: logging.Logger, interval: int) -> None:
    """设置并启动调度器"""
    scheduler = BlockingScheduler()
    next_run = calculate_next_run_time(datetime.now(), interval)

    scheduler.add_job(
        run_bot,
        IntervalTrigger(minutes=interval),
        args=[bot, logger],
        next_run_time=next_run,
    )

    try:
        logger.info(
            f"启动定时任务调度器，从 {next_run} 开始每{interval}分钟执行一次..."
        )
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("程序收到中断信号，正在退出...")
        scheduler.shutdown()

        # 清理资源
        if hasattr(bot, "cleanup"):
            try:
                bot.cleanup()
            except Exception as e:
                logger.error(f"清理资源时出错: {e}")


def create_strategy_instance(
    maker_name: str, configs: Dict[str, Any], logger: logging.Logger, exchangeKey: str
):
    """创建策略实例"""
    module = importlib.import_module(f"maker.{maker_name}")
    strategy_class = getattr(module, maker_name)
    return strategy_class(
        configs,
        configs["platform"][exchangeKey],
        configs["common"],
        logger=logger,
        exchangeKey=exchangeKey,
    )


def initialize_ai_validation(
    config_data: Dict[str, Any], logger: logging.Logger
) -> bool:
    """
    初始化AI验证系统

    Args:
        config_data: 配置数据
        logger: 日志记录器

    Returns:
        bool: 初始化是否成功
    """
    try:
        # 初始化AI验证配置
        initialize_config(config_file="maker_config.yaml", config_data=config_data)

        # 创建临时协调器实例进行健康检查
        coordinator = AIValidationCoordinator()

        if coordinator.is_enabled():
            logger.info("AI验证系统已启用")

            # 执行健康检查
            health_status = coordinator.health_check()



            if health_status["ai_service"] == "healthy":
                logger.info("AI服务连接正常")
            else:
                logger.warning(f"AI服务连接异常: {health_status['ai_service']}")
                logger.warning("系统将在降级模式下运行")

            # 显示配置信息
            config_info = health_status.get("config", {})
            logger.info(
                f"AI验证配置: "
                f"置信度阈值={config_info.get('confidence_threshold', 'N/A')}, "
                f"超时={config_info.get('timeout_seconds', 'N/A')}秒, "
                f"降级模式={config_info.get('fallback_mode', 'N/A')}"
            )

            # 关闭临时协调器
            coordinator.close()

            return True
        else:
            logger.info("AI验证系统未启用")
            return True

    except Exception as e:
        logger.error(f"AI验证系统初始化失败: {str(e)}", exc_info=True)
        logger.warning("系统将在无AI验证模式下运行")
        return False


def main():
    # 加载 .env 文件 - 尝试多个位置
    import os
    
    
    from pathlib import Path
    
    # 尝试的路径顺序：当前目录 -> 脚本目录 -> 父目录
    env_paths = [
        Path.cwd() / ".env",
        Path(__file__).parent.parent.parent.parent / ".env",  # openfund-maker/.env
        Path.cwd().parent / ".env",
    ]
    
    env_loaded = False
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            print(f"已加载环境变量文件: {env_path}")
            env_loaded = True
            break
    
    if not env_loaded:
        load_dotenv()  # 尝试默认加载
    
    # 调试：检查关键环境变量
    print(f"OPENFUND_OKX_PASSWORD: {os.getenv('OPENFUND_OKX_PASSWORD', 'NOT SET')}")
    print(f"OPENAI_URL: {os.getenv('OPENAI_URL', 'NOT SET')}")
    print(f"OPENAI_MODEL: {os.getenv('OPENAI_MODEL', 'NOT SET')}")

    # 获取包信息
    version = importlib.metadata.version("openfund-maker")
    package_name = __package__ or "openfund-maker"

    # 读取配置
    maker_config_path = "maker_config.yaml"
    config_data = read_config_file(maker_config_path)

    # 设置日志
    logging.config.dictConfig(config_data["Logger"])
    logger = logging.getLogger("openfund-maker")

    # 显示启动标题
    f = Figlet(font="standard")
    logger.info(f"\n{f.renderText('OpenFund Maker')}")

    # 获取配置信息
    common_config = config_data["common"]
    maker_name = common_config.get("actived_maker", "StrategyMaker")
    logger.info(f" ++ {package_name}.{maker_name}:{version} is doing...")
    exchangeKey = common_config.get("exchange_key", "okx")

    # 初始化AI验证系统
    ai_validation_initialized = initialize_ai_validation(config_data, logger)
    if ai_validation_initialized:
        logger.info("AI验证系统初始化完成")
    else:
        logger.warning("AI验证系统初始化失败，继续运行但不使用AI验证")

    # 创建并运行策略实例
    bot = create_strategy_instance(maker_name, config_data, logger, exchangeKey)

    # 处理调度
    schedule_config = common_config.get("schedule", {})
    if schedule_config.get("enabled", False):
        monitor_interval = int(schedule_config.get("monitor_interval", 4))
        setup_scheduler(bot, logger, monitor_interval)
    else:
        run_bot(bot, logger)


if __name__ == "__main__":
    main()
