from typing import Dict, Type

from .base import BaseDevice


class HuaweiY5Device(BaseDevice):
    """Huawei Y5"""

    def _toggle_usb_tethering_on(self):
        """执行`开启 USB 共享`的具体操作"""
        for _ in range(3):
            self.shell("input keyevent KEYCODE_DPAD_DOWN")
        self.shell("input keyevent KEYCODE_ENTER")


HUAWEI_MODELS: Dict[str, Type[BaseDevice]] = {"mya-l13": HuaweiY5Device}
