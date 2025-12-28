from typing import Dict, Type

from ..exceptions import SettingsAppException
from .base import BaseDevice


class OppoA59sDevice(BaseDevice):
    """OPPO A59s"""

    def _toggle_usb_tethering_on(self):
        """执行`开启 USB 共享`的具体操作"""
        for _ in range(2):
            self.shell("input keyevent KEYCODE_ENTER")


class OppoR11Device(BaseDevice):
    """OPPO R11"""

    def _open_usb_tethering_page(self):
        self.device.app_stop("com.android.settings")
        self.shell("am start -a android.settings.WIRELESS_SETTINGS")
        pid = self.device.app_wait("com.android.settings")
        if pid == 0:
            raise SettingsAppException("Failed to open settings app")
        self.device(text="网络共享").click()
        self.device(textMatches=r"USB\s*共享网络", className="android.widget.TextView").must_wait(self.timeout)

    def _toggle_usb_tethering_on(self):
        """执行`开启 USB 共享`的具体操作"""
        self.device(textMatches=r"USB\s*共享网络").right(className="android.widget.Switch").click()


OPPO_MODELS: Dict[str, Type[BaseDevice]] = {"oppo a59s": OppoA59sDevice, "oppo r11": OppoR11Device}
