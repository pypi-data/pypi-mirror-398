from http.client import RemoteDisconnected
from typing import Dict, Type

from uiautomator2.exceptions import UiObjectNotFoundError

from ..exceptions import SettingsAppException
from .base import BaseDevice


class Xiaomi8Device(BaseDevice):
    """xiaomi 8, xiaomi 8 ud"""

    def _open_usb_tethering_page(self):
        """打开到包含`USB 共享网络`开关的页面"""
        try:
            super()._open_usb_tethering_page()
        except UiObjectNotFoundError:
            # 王者云 device id 4274 上的设置页面与其他机型不同
            self.device.app_stop("com.android.settings")
            self.shell(
                "am start -n com.android.settings/.SubSettings --es ':android:show_fragment' com.android.settings.MiuiWirelessSettings"
            )
            pid = self.device.app_wait("com.android.settings")
            if pid == 0:
                raise SettingsAppException("Failed to open settings app")
            self.device(textMatches=r"USB\s*网络共享", className="android.widget.TextView").must_wait(self.timeout)

    def _toggle_usb_tethering_on(self):
        """执行`开启 USB 共享`的具体操作"""
        # 由于系统版本不同，存在两种布局，开关分别为 switch 和 checkbox
        # 这两种布局在 mi8 和 mi8 ud 中都存在，不能根据机型区分
        try:
            try:
                self.device(textMatches=r"USB\s*网络共享").right(className="android.widget.Switch").click()
            except AttributeError:
                self.device(textMatches=r"USB\s*网络共享").right(resourceId="android:id/checkbox").click()
        except RemoteDisconnected:
            # 点击后如果设备已断开连接，也视为成功
            # http.client.RemoteDisconnected: Remote end closed connection without response
            pass


XIAOMI_MODELS: Dict[str, Type[BaseDevice]] = {"mi 8": Xiaomi8Device, "mi 8 ud": Xiaomi8Device}
