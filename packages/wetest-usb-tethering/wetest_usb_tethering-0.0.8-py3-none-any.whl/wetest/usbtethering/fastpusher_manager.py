import json
import logging
import os
import socket
import stat
import subprocess
import time
from pathlib import Path
from typing import List, Optional

import requests

from .exceptions import DeviceException, PCHostIPException

logger = logging.getLogger(__name__)


class FastpusherManager:
    """fastpusher 进程管理器

    负责启动/停止 fastpusher，并维护其运行状态。
    默认从 `src/wetest/usbtethering/resources/fastpusher_linux_x86` 寻找二进制。
    """

    def __init__(self, android_host: str, real_serial: str, timeout):
        """初始化 FastpusherManager

        Args:
            android_host: Android 控制器的 IP 地址
            real_serial: 设备的真实序列号
            timeout: 超时时间（秒）
        """
        self.android_host = android_host
        self.real_serial = real_serial
        self.timeout = timeout
        self._proc: Optional[subprocess.Popen] = None
        self._is_service_ready = False
        self._is_registered = False
        self._pc_host_ip: Optional[str] = None

        fastpusher_path = Path(__file__).resolve().parent / "resources" / "fastpusher_linux_x86"
        if not fastpusher_path.is_file():
            raise FileNotFoundError(f"Fastpusher binary not found at: {fastpusher_path}")
        try:
            if not os.access(fastpusher_path, os.X_OK):
                current_mode = fastpusher_path.stat().st_mode
                fastpusher_path.chmod(current_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                logger.info("Granted execute permission to fastpusher: %s", fastpusher_path)
        except Exception as e:
            raise DeviceException(f"Failed to grant execute permission to fastpusher: {fastpusher_path}") from e
        self.fastpusher_path = str(fastpusher_path)

    @property
    def pid(self) -> Optional[int]:
        return self._proc.pid if self._proc is not None else None

    def get_device_info_url(self) -> str:
        """获取设备信息"""
        return f"http://{self.android_host}:9900/device/{self.real_serial}"

    @property
    def pc_host_ip(self) -> str:
        """获取云机所在控制器与云机构建成的局域网中，控制器对应的IP地址

        通过 fastpusher API 获取设备信息，从中提取 usb_host_ip。
        结果会被缓存以提高性能。

        Returns:
            str: PC主机IP地址

        Raises:
            PCHostIPException: 获取IP地址失败时抛出
        """
        if self._pc_host_ip:
            return self._pc_host_ip

        try:
            url = self.get_device_info_url()
            # 去除代理，否则会导致请求失败
            response = requests.get(url, proxies={"http": None, "https": None})
            response.raise_for_status()  # Raise an exception for HTTP errors
            device_info = response.json()
            pc_host_ip = device_info.get("usb_host_ip", "")
            if not pc_host_ip:
                raise PCHostIPException(f"USB host IP not found in device info: {device_info} by url: {url}")
            self._pc_host_ip = pc_host_ip
            return self._pc_host_ip
        except requests.exceptions.RequestException as e:
            raise PCHostIPException(f"Error getting PC host IP") from e

    def start(self) -> None:
        """启动 fastpusher 进程"""
        if self.is_running():
            logger.debug(f"Fastpusher process already running, PID: {self.pid}")
            return

        self._is_service_ready = False
        self._is_registered = False
        cmd = [
            self.fastpusher_path,
            "-source",
            f"-source-proxy={self.android_host}:9900",
            f"-source-serial={self.real_serial}",
            "-debug",
            "-logAddr",
            "172.16.8.22:6666",
        ]
        # 去除代理，否则会导致 fastpusher 连接失败
        env = os.environ.copy()
        env.pop("http_proxy", None)
        env.pop("https_proxy", None)
        self._proc = subprocess.Popen(cmd, env=env)
        logger.info(f"Fastpusher process started, PID: {self.pid}")

    def is_running(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def _check_port(self, ip: str, port: int) -> bool:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        try:
            result = sock.connect_ex((ip, port))
            return result == 0
        except Exception:
            return False
        finally:
            sock.close()

    def wait_for_service_ready(self) -> None:
        """等待 Fastpusher 服务就绪（端口可达且 API 可访问）"""
        if self._is_service_ready:
            return

        start_time = time.time()
        last_error = None

        while time.time() - start_time < self.timeout:
            # 1. Check Port
            if not self._check_port(self.android_host, 9900):
                logger.debug(
                    f"Port 9900 on {self.android_host} not reachable, retry after 1 second (elapsed: {int(time.time() - start_time)}s)..."
                )
                time.sleep(1)
                continue

            # 2. Check API and cache PC Host IP
            try:
                # 访问 pc_host_ip 属性会触发 HTTP 请求并缓存结果
                _ = self.pc_host_ip
                logger.info(f"Fastpusher service ready, PC Host IP: {self.pc_host_ip}")
                self._is_service_ready = True
                return
            except Exception as e:
                last_error = str(e)
                logger.debug(f"Fastpusher API not ready: {e}")
                time.sleep(1)

        raise DeviceException(f"Fastpusher service not ready after {self.timeout}s: {last_error}")

    def wait_for_device_registration(self, curl_cmd_prefix: List[str]) -> None:
        """等待设备成功注册到 fastpusher"""
        if self._is_registered:
            return

        # 确保此时可以获取到 URL (依赖 wait_for_service_ready 成功)
        try:
            url = self.get_status_url()
        except Exception as e:
            raise DeviceException(f"Cannot get status URL, service might not be ready: {e}")

        cmd = curl_cmd_prefix + [url]
        start_time = time.time()
        last_error = None

        logger.debug(f"Check device register command: {' '.join(cmd)}")

        while time.time() - start_time < self.timeout:
            try:
                result = subprocess.run(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding="utf-8", timeout=5
                )

                if result.returncode == 0:
                    try:
                        data = json.loads(result.stdout)
                        if data.get("status") == "running" and data.get("control_count", 0) > 0:
                            self._is_registered = True
                            logger.info("Device register ready")
                            return
                        last_error = f"Status not ready: {data}"
                    except json.JSONDecodeError:
                        last_error = f"Invalid JSON response: {result.stdout}"
                else:
                    last_error = f"Command failed: {result.stderr}"
            except Exception as e:
                last_error = f"Check exception: {e}"

            time.sleep(1)
            logger.debug(f"Waiting for device register... (elapsed: {int(time.time() - start_time)}s)")

        raise DeviceException(f"Device register failed after {self.timeout}s: {last_error}")

    def ensure_ready(self, curl_cmd_prefix: List[str]) -> None:
        """确保 fastpusher 进程运行且服务就绪

        Args:
            curl_cmd_prefix: 用于检查状态的 curl 命令前缀
        """
        if not self.is_running():
            self.start()

        self.wait_for_service_ready()
        self.wait_for_device_registration(curl_cmd_prefix)

    def stop(self) -> None:
        """停止 fastpusher 进程"""
        if self._proc is None:
            return

        self._is_service_ready = False
        self._is_registered = False
        try:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=self.timeout)
                logger.info("Fastpusher process terminated")
            except Exception as e:
                logger.debug(f"Terminate timed out, killing fastpusher: {e}")
                self._proc.kill()
                logger.debug("Fastpusher process killed")
        except Exception as e:
            logger.debug(f"Failed to terminate fastpusher gracefully: {e}")
        finally:
            self._proc = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return False

    __del__ = stop

    def get_base_url(self) -> str:
        """连接PC控制器代理端口"""
        return f"http://{self.pc_host_ip}:9900"

    def get_status_url(self) -> str:
        """获取 fastpusher 状态检查 URL

        Returns:
            str: fastpusher 状态检查 URL
        """
        return f"{self.get_base_url()}/status"

    def get_download_url(self, local_file_path: str) -> str:
        """获取通过 fastpusher 下载文件的 URL

        Args:
            local_file_path: 本地文件路径

        Returns:
            str: fastpusher 下载文件 URL
        """
        return f"{self.get_base_url()}/serial/{self.real_serial}/download?file={local_file_path}"
