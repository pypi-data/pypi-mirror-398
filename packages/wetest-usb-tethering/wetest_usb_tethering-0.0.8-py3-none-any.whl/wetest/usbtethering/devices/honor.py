from typing import Dict, Type

from .base import BaseDevice


class HonorMyaDevice(BaseDevice):
    """honor MYA-TL10, MYA-AL10(Y5)"""

    def _toggle_usb_tethering_on(self):
        """执行`开启 USB 共享`的具体操作"""
        for _ in range(3):
            self.shell("input keyevent KEYCODE_DPAD_DOWN")
        self.shell("input keyevent KEYCODE_ENTER")


HONOR_MODELS: Dict[str, Type[BaseDevice]] = {"mya-tl10": HonorMyaDevice, "mya-al10": HonorMyaDevice}
