import logging
import logging.config
import yaml
import importlib
import importlib.metadata
import os
import re
from typing import Dict, Any
from pyfiglet import Figlet
from dotenv import load_dotenv


def read_config_file(file_path):
    try:
        # 打开 YAML 文件
        with open(file_path, "r", encoding="utf-8") as file:
            # 读取文件内容并展开环境变量
            yaml_str = file.read()
            expanded_yaml = os.path.expandvars(yaml_str)
            
            # 检查是否有未替换的环境变量
            unresolved = re.findall(r'\$\{([^}]+)\}', expanded_yaml)
            if unresolved:
                print(f"Warning: 以下环境变量未设置: {', '.join(unresolved)}")
            
            # 使用 yaml.safe_load 方法解析 YAML 文件内容
            data = yaml.safe_load(expanded_yaml)
            return data
    except FileNotFoundError:
        raise Exception(f"文件 {file_path} 未找到。")
    except yaml.YAMLError as e:
        raise Exception(f"解析 {file_path} 文件时出错: {e}")


def initialize_logger(config: Dict[str, Any]) -> logging.Logger:
    """初始化日志配置并返回logger实例"""
    logging.config.dictConfig(config["Logger"])
    return logging.getLogger("openfund-taker")


def create_strategy_instance(
    taker_name: str, configs: Dict[str, Any], logger: logging.Logger, exchangeKey: str
):
    """创建策略实例"""
    module = importlib.import_module(f"taker.{taker_name}")
    strategy_class = getattr(module, taker_name)
    return strategy_class(
        configs, configs["platform"][exchangeKey], configs["common"], logger=logger
    )


def main():
    # 加载 .env 文件 - 尝试多个位置
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
        
    print(f"OPENFUND_OKX_PASSWORD: {os.getenv('OPENFUND_OKX_PASSWORD', 'NOT SET')}")

    # 获取版本信息和包名
    version = importlib.metadata.version("openfund-taker")
    package_name = __package__ or "taker"

    # 读取配置文件
    config_path = Path("taker_config.yaml")
    config_data = read_config_file(config_path)

    # 获取配置参数
    common_config = config_data["common"]
    taker_name = common_config.get("actived_taker", "StrategyTaker")

    # 初始化日志
    logger = initialize_logger(config_data)

    # 显示启动信息
    f = Figlet(font="standard")
    logger.info(f"\n{f.renderText('OpenFund Taker')}")
    logger.info(f" ++ {package_name}.{taker_name}:{version} is doing...")
    exchangeKey = common_config.get("exchange_key", "okx")
    # 创建并运行策略实例
    bot = create_strategy_instance(taker_name, config_data, logger, exchangeKey)
    bot.monitor_total_profit()


if __name__ == "__main__":
    main()
