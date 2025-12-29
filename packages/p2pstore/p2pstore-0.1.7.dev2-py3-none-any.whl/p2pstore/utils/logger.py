"""
Logger Utils 模块.

该模块提供了日志管理工具 `LoggerManager`。
负责统一配置和获取日志记录器，支持文件轮转日志（不输出到控制台，避免污染宿主程序日志）。

环境变量配置：
- P2PSTORE_LOG_LEVEL: 全局日志等级 (DEBUG, INFO, WARNING, ERROR, CRITICAL)，默认 INFO
- P2PSTORE_LOG_LEVEL_{MODULE}: 模块级别日志等级，如 P2PSTORE_LOG_LEVEL_ZMQ_CLIENT=DEBUG
- P2PSTORE_ENABLE_CONSOLE: 是否输出到控制台 (1 启用, 默认禁用)，避免作为库使用时污染宿主日志
- P2PSTORE_DISABLE_LOG: 完全禁用日志 (1 启用)，不创建任何文件和输出

示例：
    export P2PSTORE_LOG_LEVEL=DEBUG                    # 全局 DEBUG
    export P2PSTORE_LOG_LEVEL_ZMQ_CLIENT=DEBUG         # 只有 zmq-client 为 DEBUG
    export P2PSTORE_ENABLE_CONSOLE=1                   # 开发调试时启用控制台输出
    export P2PSTORE_DISABLE_LOG=1                      # 完全禁用所有日志
"""

import logging
import os
import queue
from datetime import datetime
from logging.handlers import QueueHandler, QueueListener, TimedRotatingFileHandler
from pathlib import Path
from typing import Dict


class LoggerManager:
    """日志管理器, 负责创建和配置日志记录器."""

    _loggers: Dict[str, logging.Logger] = {}
    _log_dir: Path | None = None  # 延迟初始化，使用运行时的工作目录
    _default_level: int = logging.INFO  # 默认日志级别
    _sub_dir: str | None = None  # 子目录（用于区分不同的 Client）
    _client_id: str | None = None  # 当前客户端 ID（用于日志格式）
    _env_initialized: bool = False  # 标记是否已从环境变量初始化

    # 异步日志：每个 logger 一个队列和监听器
    _queue_listeners: Dict[str, QueueListener] = {}

    @classmethod
    def _get_log_dir(cls) -> Path:
        """获取日志目录（延迟计算，使用运行时的工作目录）"""
        if cls._log_dir is None:
            base_dir = Path.cwd() / "p2pstorelog"

            # 优化：增加分层结构 p2pstorelog/{日期}/{任务组}/{ClientID}
            # 1. 按日期归档，避免长期运行堆积
            date_str = datetime.now().strftime("%Y-%m-%d")

            # 2. 按任务分组，解决每天多次重启的问题
            # 使用 %H%M (分钟级) 聚合同一批启动的 8 个 Client
            time_str = datetime.now().strftime("%H%M")
            pod_index = os.environ.get("POD_INDEX", "unknown").strip()
            group_name = f"pod_{pod_index}_{time_str}"

            # 3. 组合路径
            log_root = base_dir / date_str / group_name

            if cls._sub_dir:
                cls._log_dir = log_root / cls._sub_dir
            else:
                cls._log_dir = log_root
        return cls._log_dir

    @classmethod
    def set_sub_dir(cls, sub_dir: str) -> None:
        """设置日志子目录（必须在创建任何 logger 之前调用）

        Args:
            sub_dir: 子目录名称，通常是 8 位随机字符串
        """
        cls._sub_dir = sub_dir
        cls._client_id = sub_dir  # 同时设置 client_id，用于日志格式
        cls._log_dir = None  # 重置，强制重新计算

    @classmethod
    def _ensure_dir(cls) -> None:
        cls._get_log_dir().mkdir(parents=True, exist_ok=True)

    @classmethod
    def _parse_log_level(cls, level_str: str) -> int:
        """解析日志等级字符串为 logging 常量

        Args:
            level_str: 日志等级字符串 (不区分大小写)

        Returns:
            int: logging 等级常量，无效值返回 INFO
        """
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "WARN": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }
        return level_map.get(level_str.upper(), logging.INFO)

    @classmethod
    def _init_from_env(cls) -> None:
        """从环境变量初始化默认日志等级（仅执行一次）"""
        if cls._env_initialized:
            return
        cls._env_initialized = True

        # 读取全局日志等级
        global_level = os.environ.get("P2PSTORE_LOG_LEVEL", "").strip()
        if global_level:
            cls._default_level = cls._parse_log_level(global_level)
            # 输出到 stderr，避免污染日志文件
            print(
                f"[LoggerManager] 从环境变量设置全局日志等级: {logging.getLevelName(cls._default_level)}",
                flush=True,
            )

    @classmethod
    def _get_module_level(cls, logger_name: str) -> int | None:
        """获取模块级别的日志等级（从环境变量）

        Args:
            logger_name: logger 名称，如 'zmq-client', 'p2p-client'

        Returns:
            int | None: 模块级日志等级，未设置则返回 None
        """
        # 将 logger 名称转换为环境变量格式
        # 例如: 'zmq-client' -> 'P2PSTORE_LOG_LEVEL_ZMQ_CLIENT'
        env_suffix = logger_name.upper().replace("-", "_").replace(".", "_")
        env_var = f"P2PSTORE_LOG_LEVEL_{env_suffix}"

        level_str = os.environ.get(env_var, "").strip()
        if level_str:
            level = cls._parse_log_level(level_str)
            print(
                f"[LoggerManager] p2pstore 从环境变量 {env_var} 设置 '{logger_name}' 日志等级: {logging.getLevelName(level)}",
                flush=True,
            )
            return level
        return None

    @classmethod
    def setup_logger(
        cls,
        name: str,
        level: int | None = None,
        include_thread: bool = True,
    ) -> logging.Logger:
        """
        获取或创建日志记录器.

        Args:
            name: 日志名称.
            level: 日志级别，优先级：参数 > 环境变量(模块) > 环境变量(全局) > _default_level.
            include_thread: 是否在日志中包含线程名.

        Returns:
            logging.Logger: 配置好的日志记录器.
        """
        if name in cls._loggers:
            return cls._loggers[name]

        # 检查是否完全禁用日志
        if os.environ.get("P2PSTORE_DISABLE_LOG", "0") == "1":
            print(f"P2PSTORE_DISABLE_LOG=1,不输出任何日志")
            logger = logging.getLogger(name)
            logger.setLevel(logging.CRITICAL + 100)  # 设置超高级别
            logger.propagate = False
            logger.addHandler(logging.NullHandler())  # 只添加 NullHandler
            cls._loggers[name] = logger
            return logger

        # 首次调用时从环境变量初始化
        cls._init_from_env()

        # 优先级：参数 > 环境变量(模块) > 环境变量(全局) > _default_level
        if level is not None:
            effective_level = level
        else:
            module_level = cls._get_module_level(name)
            effective_level = (
                module_level if module_level is not None else cls._default_level
            )

        cls._ensure_dir()
        logger = logging.getLogger(name)

        # 避免重复配置：如果 logger 已有 handler，直接返回（防止重复输出）
        if logger.handlers:
            cls._loggers[name] = logger
            return logger

        logger.setLevel(effective_level)
        logger.propagate = False

        # 构建日志格式，如果设置了 client_id 则包含在日志中
        client_prefix = f"[{cls._client_id}] " if cls._client_id else ""
        if include_thread:
            fmt = (
                "%(asctime)s - %(threadName)s - "
                f"{client_prefix}%(name)s - %(levelname)s - "
                "%(filename)s:%(lineno)d - %(message)s"
            )
        else:
            fmt = f"%(asctime)s - {client_prefix}%(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"

        # 不指定 datefmt，默认格式为 "%Y-%m-%d %H:%M:%S,333" (包含毫秒)
        formatter = logging.Formatter(fmt)

        log_file = cls._get_log_dir() / f"{name}.log"
        print(
            f"[LoggerManager] Creating p2pstore log file at: {log_file.absolute()}",
            flush=True,
        )

        # 使用异步日志队列，避免 logging 锁竞争导致死锁
        # 每个 logger 独立的队列和监听器
        log_queue = queue.Queue(-1)  # 无限队列

        # 创建实际的文件 handler（由后台线程处理）
        file_handler = TimedRotatingFileHandler(
            filename=str(log_file),
            when="midnight",
            backupCount=7,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(effective_level)

        # 创建 QueueListener 并启动后台线程
        queue_listener = QueueListener(
            log_queue, file_handler, respect_handler_level=True
        )
        queue_listener.start()
        cls._queue_listeners[name] = queue_listener

        # Logger 使用 QueueHandler，日志写入队列（非阻塞）
        queue_handler = QueueHandler(log_queue)
        logger.addHandler(queue_handler)

        # 控制台输出默认关闭，避免作为库使用时污染宿主程序日志
        # 开发调试时可通过 export P2PSTORE_ENABLE_CONSOLE=1 启用
        enable_console = os.environ.get("P2PSTORE_ENABLE_CONSOLE", "0") == "1"
        if enable_console:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(effective_level)
            logger.addHandler(console_handler)

        cls._loggers[name] = logger
        return logger

    @classmethod
    def shutdown(cls) -> None:
        """
        关闭日志系统，停止所有异步队列监听器.

        应该在程序退出时调用，确保所有日志都已写入磁盘。
        """
        for name, listener in cls._queue_listeners.items():
            print(f"[LoggerManager] 停止日志队列监听器: {name}", flush=True)
            listener.stop()
        cls._queue_listeners.clear()

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        获取 logger 的便捷方法（setup_logger 的别名）.

        Args:
            name: 日志名称.

        Returns:
            logging.Logger: 配置好的日志记录器.
        """
        return cls.setup_logger(name)

    @classmethod
    def set_level(cls, level: str | int) -> None:
        """
        设置所有日志记录器的级别.

        Args:
            level: 日志级别，可以是字符串 ('DEBUG', 'INFO', 'WARNING', 'ERROR')
                   或 logging 常量 (logging.DEBUG, logging.INFO 等)

        Example:
            LoggerManager.set_level("DEBUG")
            LoggerManager.set_level(logging.WARNING)
        """
        numeric_level: int
        if isinstance(level, str):
            numeric_level = getattr(logging, level.upper(), logging.INFO)
        else:
            numeric_level = level

        cls._default_level = numeric_level

        # 更新所有已创建的 logger
        for logger in cls._loggers.values():
            logger.setLevel(numeric_level)
            for handler in logger.handlers:
                handler.setLevel(numeric_level)
