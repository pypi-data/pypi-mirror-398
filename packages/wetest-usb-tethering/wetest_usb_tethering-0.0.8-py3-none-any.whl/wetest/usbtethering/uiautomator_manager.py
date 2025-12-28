import logging
import time
from typing import Optional

import uiautomator2 as u2
from adbutils import adb
from uiautomator2.exceptions import AccessibilityServiceAlreadyRegisteredError

from .exceptions import DeviceException, UIAutomatorOccupiedException

logger = logging.getLogger(__name__)


class UIAutomatorManager:
    """UIAutomator实例管理器

    用于管理设备中的uiautomator2实例，提供连接设备、处理冲突和清理实例的功能。
    当uiautomator服务被占用时，会自动清理并重试连接。
    """

    def __init__(
        self, device_serial: Optional[str] = None, max_retries: int = 3, error_handler: Optional[callable] = None
    ):
        self.device_serial = device_serial
        self.device = None
        self._connect_with_retry(max_retries, error_handler)

    def kill_ui_instance(self) -> None:
        """结束当前设备中正在进行的uiautomator实例

        通过ADB命令杀死设备上的app_process进程来清理uiautomator实例。
        注意：这会终止所有基于app_process的自动化服务。

        Raises:
            UIAutomatorOccupiedException: 清理失败时抛出
        """
        try:
            device = adb.device(self.device_serial) if self.device_serial else adb.device()
            logger.info(f"Attempting to kill uiautomator instances on {device.serial}")
            device.shell(["pkill", "-f", "app_process"])
            time.sleep(1)  # 等待进程完全退出
            output = device.shell(["ps", "|", "grep", "app_process"])
            if output and re.search(r"\d+\s+.*app_process", output):
                # 偶现 grep 内容只有标题行，不包含实际进程信息。所以需要检查是否有匹配项
                raise UIAutomatorOccupiedException(f"Uiautomator processes still running after kill:{output}")
            logger.info("Successfully killed uiautomator processes")

        except Exception as e:
            raise UIAutomatorOccupiedException(f"Failed to kill uiautomator instances: {e}")

    def _connect_with_retry(self, max_retries: int = 3, error_handler: Optional[callable] = None) -> None:
        """连接设备，处理uiautomator服务冲突并重试

        Args:
            max_retries: 最大重试次数

        Raises:
            DeviceException: 连接失败时抛出
        """
        last_exception = None
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to connect to device (attempt {attempt + 1}/{max_retries})")
                device = u2.connect(self.device_serial) if self.device_serial else u2.connect()
                logger.info(f"Successfully connected to device: {device.serial}, info: {device.device_info}")
                self.device = device
                self._patch_check_alive()
                return

            except AccessibilityServiceAlreadyRegisteredError as e:
                logger.warning(f"UIAutomator service already registered on attempt {attempt + 1}, exception: \n {e}")
                logger.info("Attempting to clear existing uiautomator instances...")
                try:
                    self.kill_ui_instance()
                except UIAutomatorOccupiedException:
                    logger.warning("Failed to clear uiautomator instances, will retry connection anyway")

            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                if error_handler:
                    error_handler(e)

        raise DeviceException(f"Failed to connect to device after {max_retries} attempts.") from last_exception

    def _patch_check_alive(self) -> None:
        """为 device._check_alive 添加 RemoteDisconnected 捕获

        本地设备 kill ui server 后，异常为 HTTPError, ui2 内部已处理
        云真机 kill ui server 后，异常为 http.client.RemoteDisconnected, 需要处理
        """
        from http.client import RemoteDisconnected
        from types import MethodType

        if getattr(self.device, "_wetest_check_alive_patched", False):
            return

        original = self.device._check_alive

        def _check_alive_with_remote(self) -> bool:
            try:
                return original()
            except RemoteDisconnected:
                return False

        # 重新绑定覆盖原方法
        self.device._check_alive = MethodType(_check_alive_with_remote, self.device)
        setattr(self.device, "_wetest_check_alive_patched", True)

    def reconnect(self) -> None:
        """断开当前连接并重新建立连接

        ui2 在执行 jsonrpc 时，会自动检查是否连接断开，若连接断开，会自动重连 (uiautomator2/core.py:310)
        因此只在明确需要 kill server 并重新连接时调用此方法
        """
        logger.info("Reconnecting to device...")
        self.kill_ui_instance()
        self._connect_with_retry()
