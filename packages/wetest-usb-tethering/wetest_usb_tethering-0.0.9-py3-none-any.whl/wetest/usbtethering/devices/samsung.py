from http.client import RemoteDisconnected
from typing import Dict, Type

from .base import BaseDevice


class SamsungNote20Device(BaseDevice):
    """samsung note 20"""

    def _toggle_usb_tethering_on(self):
        """执行`开启 USB 共享`的具体操作"""
        for _ in range(4):
            self.shell("input keyevent KEYCODE_DPAD_DOWN")
        self.shell("input keyevent KEYCODE_ENTER")


SAMSAUNG_MODELS: Dict[str, Type[BaseDevice]] = {"sm-n986b": SamsungNote20Device, "sm-n9860": SamsungNote20Device}
