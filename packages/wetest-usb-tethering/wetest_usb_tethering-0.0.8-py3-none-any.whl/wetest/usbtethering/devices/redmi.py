from http.client import RemoteDisconnected
from typing import Dict, Type

from .base import BaseDevice


class RedmiK50Device(BaseDevice):
    """redmi k50"""

    def _toggle_usb_tethering_on(self):
        """执行`开启 USB 共享`的具体操作"""
        try:
            self.device(textMatches=r"USB\s*网络共享").right(className="android.widget.Switch").click()
        except RemoteDisconnected:
            # 点击后如果设备已断开连接，也视为成功
            # http.client.RemoteDisconnected: Remote end closed connection without response
            pass


REDMI_MODELS: Dict[str, Type[BaseDevice]] = {"22011211c": RedmiK50Device}
