import hashlib
import logging
import re
import subprocess
import tarfile
import time
from abc import ABC, abstractmethod
from ast import Tuple
from pathlib import Path
from typing import Any, Callable, List, Tuple

import uiautomator2 as u2

from ..exceptions import (
    DeviceException,
    DownloadException,
    FileMismatchException,
    PCHostIPException,
    SettingsAppException,
    TetheringException,
    TimeoutException,
)
from ..fastpusher_manager import FastpusherManager
from ..uiautomator_manager import UIAutomatorManager

logger = logging.getLogger(__name__)


class BaseDevice(ABC):
    """设备基类，提供通用的USB共享功能实现"""

    # 设备工具路径常量，去除 proxy
    DEVICE_TOOLS_DIR = "/data/local/tmp/wetest"
    CURL = f"{DEVICE_TOOLS_DIR}/curl_bin --noproxy '*'"
    BUSYBOX_BIN = f"{DEVICE_TOOLS_DIR}/busybox"
    WGET = f"{BUSYBOX_BIN} wget -Y off"

    def __init__(self, manager: UIAutomatorManager, timeout):
        """初始化并连接设备

        Args:
            manager: UIAutomatorManager实例
            timeout: 操作超时时间
        """
        self.ui_manager = manager
        self._fastpusher = None
        self.timeout = timeout
        logger.info(
            f"Initializing {self.__class__.__name__} with model {self.device_info.get('model', 'unknown')}. Timeout: {self.timeout}s."
        )

    @property
    def fastpusher(self) -> FastpusherManager:
        """获取FastpusherManager实例，确保只在调用时初始化"""
        if self._fastpusher is None:
            self._fastpusher = FastpusherManager(self.android_host, self.real_serial, self.timeout)
        self._fastpusher.ensure_ready(["adb", "-s", self.serial, "shell", f"{self.CURL}", "-s"])
        return self._fastpusher

    @property
    def device(self) -> u2.Device:
        """获取设备实例"""
        if not self.ui_manager.device:
            raise DeviceException("Device not connected. Please call reconnect() first.")
        return self.ui_manager.device

    @property
    def shell(self) -> Callable[..., Any]:
        """获取adb设备实例

        ui2.Device.shell 要求返回值不能为空，否则会抛出异常
        因此对于 shell 直接使用 adb_device 的shell指令
        """
        return self.device._dev.shell

    @property
    def real_serial(self) -> str:
        """获取真实设备序列号
        对于云机而言，初始化 serial 形如 11.41.56.70:5555，
        而真实 serial 需要通过 `getprop ro.serialno` 获取；
        本地接入的shell指令直接返回的 serial 与初始化 serial 相同。
        """
        return self.shell("getprop ro.serialno").strip()

    @property
    def android_host(self) -> str:
        """获取云机所在控制器的IP地址"""
        if ":" not in self.serial:
            raise PCHostIPException("Serial number does not contain ':', please check if it is a cloud device")
        return self.serial.split(":")[0]

    @property
    def pc_host_ip(self) -> str:
        """获取云机所在控制器与云机构建成的局域网中，控制器对应的IP地址"""
        return self.fastpusher.pc_host_ip

    def __getattr__(self, name):
        """自动代理到device的属性

        当调用未定义的属性时，自动转发到u2.Device实例
        e.g. device_info, info, serial

        Args:
            name: 属性名

        Returns:
            属性值

        Raises:
            AttributeError: 如果属性不存在
        """
        if hasattr(self.device, name):
            return getattr(self.device, name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def _open_usb_tethering_page(self):
        """打开到包含`USB 共享网络`开关的页面"""
        self.device.app_stop("com.android.settings")
        self.shell("am start -n com.android.settings/.TetherSettings")
        pid = self.device.app_wait("com.android.settings")
        if pid == 0:
            raise SettingsAppException("Failed to open settings app")
        self.device(textMatches=r"USB\s*(网络共享|共享网络)", className="android.widget.TextView").must_wait(
            self.timeout
        )

    @abstractmethod
    def _toggle_usb_tethering_on(self):
        """执行`开启 USB 共享`的具体操作"""
        pass

    def enable_usb_tethering(self, max_retries: int = 3) -> bool:
        """启用USB网络共享"""
        if self.is_usb_tethering_enabled():
            logger.info("USB tethering is already enabled")
            return True

        for attempt in range(max_retries):
            self.device.unlock()
            logger.info("Open USB tethering page")
            self._open_usb_tethering_page()
            self.take_screenshot(f"open_usb_tethering_page_{attempt}")

            logger.info("Toggle USB tethering on")
            self._toggle_usb_tethering_on()

            # 开启网络共享后会出现设备暂时掉线，并自动上线 (offline -> online)
            start_time = time.time()
            while not self._is_adb_connected() and time.time() - start_time < self.timeout:
                time.sleep(1)
                logger.debug(f"Waiting for connection to restore... (elapsed: {int(time.time() - start_time)}s)")
            if not self._is_adb_connected():
                raise TetheringException(f"Device did not reconnect after toggling USB tethering after {self.timeout}s")

            self.take_screenshot(f"toggle_usb_tethering_on_{attempt}")

            if self.is_usb_tethering_enabled():
                logger.info("USB tethering is enabled")
                self.device.press("home")
                return True

        raise TetheringException(f"Failed to enable USB tethering after {max_retries} attempts")

    def is_usb_tethering_enabled(self) -> bool:
        """检查USB网络共享是否已启用"""
        output = self.shell("ip addr show")

        # 使用正则表达式匹配三个关键条件：
        # 1. rndis0 接口存在
        # 2. 192.168 开头的IP地址
        # 3. UP BROADCAST RUNNING 状态
        pattern = r"rndis0:.*?<.*?UP.*?>.*?inet 192\.168\.\d+\.\d+"
        return "rndis0" in output and bool(re.search(pattern, output, re.DOTALL))

    def take_screenshot(self, filename: str = None) -> str:
        """保存设备当前屏幕截图

        Args:
            filename: 自定义文件名，默认使用当前时间戳

        Returns:
            str: 截图保存路径
        """
        if filename is None:
            filename = f"{int(time.time())}"
        screenshot_path = f"screenshots/{self.device_info.get('model', 'unknown')}/{filename}.png"
        Path(screenshot_path).parent.mkdir(parents=True, exist_ok=True)
        self.device.screenshot(screenshot_path)
        logger.info(f"Screenshot saved: {screenshot_path}")
        return screenshot_path

    def _is_adb_connected(self) -> bool:
        """检查设备 adb 连接"""
        try:
            self.device_info
            return True
        except Exception as e:
            logger.error(f"Failed to check adb connection: {e}")
            return False

    def is_connected(self):
        """检查设备 adb 与 uiautomator 连接状态"""
        return self._is_adb_connected() and self.device._check_alive()

    def reconnect(self):
        """重新连接设备"""
        return self.ui_manager.reconnect()

    def release(self) -> bool:
        """释放 uiautomator2 连接，清理 fastpusher 进程"""
        self.device.stop_uiautomator()
        logger.info("Release uiautomator2 connection")
        if self.is_connected():
            self.ui_manager.kill_ui_instance()
            logger.debug("Kill uiautomator2 instance")

        # 停止 fastpusher 进程
        if self._fastpusher is not None:
            self._fastpusher.stop()

        return self.is_connected()

    __del__ = release

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            self.release()
        except Exception as e:
            logger.exception("Failed to release uiautomator2 connection: %s", e)
        return False

    def _download_normal_file(self, local_file_path: str, device_file_path: str) -> Tuple[List[str], int]:
        """下载普通文件到设备"""
        file_size = Path(local_file_path).stat().st_size
        download_url = self.fastpusher.get_download_url(local_file_path)
        cmd = [
            "adb",
            "-s",
            self.serial,
            "shell",
            f"{self.CURL}",
            "-o",
            device_file_path,
            download_url,
        ]
        return cmd, file_size

    def _download_tar_file(self, local_file_path: str, device_file_path: str) -> Tuple[List[str], int]:
        """下载tar文件并解压到设备"""
        total_size = 0
        try:
            with tarfile.open(local_file_path, "r") as tf:
                members = tf.getmembers()
                total_size = sum(m.size for m in members if m.isfile())
        except Exception as e:
            raise FileMismatchException(f"Failed to read local tar metadata, please check the file integrity") from e

        try:
            subprocess.run(
                ["adb", "-s", self.serial, "shell", f'mkdir -p "{device_file_path}"'],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            raise DownloadException("Failed to create target directory on device") from e

        download_url = self.fastpusher.get_download_url(local_file_path)
        cmd = [
            "adb",
            "-s",
            self.serial,
            "shell",
            f"{self.BUSYBOX_BIN} time",
            self.WGET,
            download_url,
            f'-O- | {self.BUSYBOX_BIN} tar x --overwrite -C "{device_file_path}"',
        ]
        return cmd, total_size

    def _get_download_progress(self, device_file_path: str, auto_extract: bool) -> int:
        """获取下载进度"""
        if auto_extract:
            try:
                device_file_size_str = self.shell(
                    f'{self.BUSYBOX_BIN} find "{device_file_path}" -type f '
                    f"-exec {self.BUSYBOX_BIN} stat -c %s {{}} \\; | "
                    f"{self.BUSYBOX_BIN} awk '{{s+=$1}} END {{print s}}'"
                ).strip()
                return int(device_file_size_str) if device_file_size_str.isdigit() else 0
            except Exception as e:
                raise DownloadException("Failed to get extracted size") from e
        else:
            try:
                cmd = f"[ -f '{device_file_path}' ] && stat -c %s '{device_file_path}' || echo 0"
                device_file_size_str = self.shell(cmd).strip()
                return int(device_file_size_str) if device_file_size_str.isdigit() else 0
            except Exception as e:
                raise DownloadException(f"Failed to get downloaded size") from e

    def _verify_extracted_file(self, expected_size: int, device_file_path: str) -> int:
        """验证解压后的文件"""
        device_file_size_str = self.shell(
            f'{self.BUSYBOX_BIN} find "{device_file_path}" -type f '
            f"-exec {self.BUSYBOX_BIN} stat -c %s {{}} \\; | "
            f"{self.BUSYBOX_BIN} awk '{{s+=$1}} END {{print s}}'"
        ).strip()
        device_file_size = int(device_file_size_str) if device_file_size_str.isdigit() else 0

        if expected_size != device_file_size:
            device_preview = ""
            try:
                device_preview = self.shell(
                    f'{self.BUSYBOX_BIN} ls -lR "{device_file_path}" | ' f"{self.BUSYBOX_BIN} head -n 50"
                )
            except Exception as e:
                logger.debug(f"Failed to read device file content: {e}")

            raise FileMismatchException(
                f"File size mismatch: local= {expected_size} bytes, device= {device_file_size} bytes. "
                f"Device file preview (first 50 lines): {device_preview!r}"
            )

        logger.info(f"Extracted file size verified: local={expected_size} bytes, device={device_file_size} bytes")
        return device_file_size

    def _verify_normal_file(self, local_file_path: str, device_file_path: str) -> int:
        """验证普通下载文件"""
        expected_size = Path(local_file_path).stat().st_size

        device_file_size = int(self.shell(f"stat -c %s {device_file_path}").strip())
        if expected_size != device_file_size:
            device_preview = ""
            try:
                device_preview = self.shell(f"cut -b 1-4096 {device_file_path}")
            except Exception as e:
                logger.debug(f"Failed to read device file content: {e}")

            raise FileMismatchException(
                f"File size mismatch: local={expected_size} bytes, device={device_file_size} bytes. "
                f"Device file preview (first 4KB): {device_preview!r}"
            )
        logger.info(f"Downloaded file size verified: local={expected_size} bytes, device={device_file_size} bytes")

        with open(local_file_path, "rb") as f:
            local_md5 = hashlib.md5(f.read()).hexdigest()
        device_md5 = self.shell(f"md5sum {device_file_path}").split()[0].strip()
        if local_md5 != device_md5:
            raise FileMismatchException(f"File MD5 mismatch: local={local_md5}, device={device_md5}")
        logger.info(f"File MD5 verified: local={local_md5}, device={device_md5}")
        return device_file_size

    def download_file(
        self, local_file_path: str, device_file_path: str, extract: bool = True, timeout: int = 30 * 60
    ) -> int:
        """往设备下载文件:

        Args:
            local_file_path: 容器内待下载的文件路径
            device_file_path: 保存到设备上的文件路径。如果不指定，则默认对.tar进行解压后保存，其他文件则直接保存到指定路径
            extract: 是否对.tar文件进行解压，默认True
            timeout: 下载超时时间（单位：秒），默认30分钟

        Returns:
            int: 成功下载到设备中的文件大小（单位：字节）
        """
        if not self.is_usb_tethering_enabled():
            self.enable_usb_tethering()

        auto_extract = extract and local_file_path.endswith(".tar")

        if not Path(local_file_path).is_file():
            raise FileNotFoundError(f"Local file not found: {local_file_path}")
        cmd, file_size = (
            self._download_tar_file(local_file_path, device_file_path)
            if auto_extract
            else self._download_normal_file(local_file_path, device_file_path)
        )
        if file_size == 0:
            raise FileMismatchException(f"Local file is empty: {local_file_path}")

        # 即使异常退出，return code 也会是0，所以查看日志是否有错误信息，不能将 stdout/ stderr 重定向到 /dev/null
        proc = subprocess.Popen(cmd)
        logger.debug(f"Download command (subprocess): {' '.join(cmd)}, pid: {proc.pid}")
        start_time = time.time()
        timed_out = False
        try:
            while proc.poll() is None:
                downloaded_size = self._get_download_progress(device_file_path, auto_extract)
                percent = round(downloaded_size * 100 / file_size, 2)
                logger.info(f"Download progress: {percent}% ({downloaded_size}/{file_size} bytes)")

                if downloaded_size >= file_size:
                    break

                if time.time() - start_time >= timeout:
                    logger.warning(f"Download timed out after {timeout} seconds, exiting progress loop")
                    timed_out = True
                    break

                time.sleep(60)
        finally:
            # 超时退出的情况，需要强制终止进程
            if proc.poll() is None:
                try:
                    proc.terminate()
                    time.sleep(0.5)
                    if proc.poll() is None:
                        proc.kill()
                except Exception as e:
                    logger.error(f"Failed to terminate download subprocess: {e}")

        if timed_out:
            raise TimeoutException(f"Download timed out after {timeout} seconds")

        device_file_size = (
            self._verify_extracted_file(file_size, device_file_path)
            if auto_extract
            else self._verify_normal_file(local_file_path, device_file_path)
        )

        duration = int(time.time() - start_time)
        speed_mb_s = round(device_file_size / max(duration, 1) / 1024 / 1024, 2)
        logger.info(f"Download completed in {duration} seconds, ~{speed_mb_s} MB/s")

        return device_file_size
