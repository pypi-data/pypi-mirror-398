import logging
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Optional


class TetheringLogger:
    """日志管理器"""

    def __init__(self, package_name: str = __package__):
        self.package_name = package_name
        self._logger = None
        self._setup_logger()

    def _setup_logger(self):
        """设置日志器"""
        self._logger = logging.getLogger(self.package_name)
        self._logger.setLevel(logging.DEBUG)

        # 避免重复添加handler
        if self._logger.handlers:
            return

        log_format = "%(asctime)s - %(name)s - %(funcName)s - %(lineno)d - %(levelname)s - %(message)s"
        formatter = logging.Formatter(log_format)

        # 控制台handler（始终添加）
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)

    @property
    def logger(self):
        """获取日志器实例"""
        return self._logger

    def __getattr__(self, name):
        """自动代理到logger的属性和方法

        当调用未定义的属性时，自动转发到logging.Logger实例
        e.g. debug, info, warning, error, critical, exception, setLevel

        Args:
            name: 属性名

        Returns:
            属性值或方法

        Raises:
            AttributeError: 如果属性不存在
        """
        if hasattr(self._logger, name):
            return getattr(self._logger, name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def enable_file_logging(self, log_dir: Optional[str] = None, file_level: int = logging.DEBUG):
        """为当前logger启用文件日志"""
        # 检查是否已经有文件handler
        for handler in self._logger.handlers:
            if isinstance(handler, TimedRotatingFileHandler):
                return

        if log_dir is None:
            log_dir = Path.cwd() / "tethering_logs"
        else:
            log_dir = Path(log_dir)

        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"{self.package_name}-{datetime.now().strftime('%Y%m%d')}.log"

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(funcName)s - %(lineno)d - %(levelname)s - %(message)s"
        )

        file_handler = TimedRotatingFileHandler(
            str(log_path),
            when="midnight",
            interval=1,
            backupCount=7,
            encoding="utf-8",
        )
        file_handler.setLevel(file_level)
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)

    def disable_console_logging(self):
        """禁用控制台日志"""
        handlers_to_remove = [
            h
            for h in self._logger.handlers
            if isinstance(h, logging.StreamHandler) and not isinstance(h, TimedRotatingFileHandler)
        ]
        for handler in handlers_to_remove:
            self._logger.removeHandler(handler)

    def disable_file_logging(self):
        """禁用文件日志"""
        handlers_to_remove = [h for h in self._logger.handlers if isinstance(h, TimedRotatingFileHandler)]
        for handler in handlers_to_remove:
            self._logger.removeHandler(handler)
