import logging
from typing import Callable, Dict, Optional, Type

from . import __version__
from .devices import *
from .uiautomator_manager import UIAutomatorManager

logger = logging.getLogger(__name__)


# 品牌与型号到设备类的映射
SUPPORTED_BRANDS: Dict[str, Dict[str, Type[BaseDevice]]] = {
    "oppo": OPPO_MODELS,
    "vivo": VIVO_MODELS,
    "huawei": HUAWEI_MODELS,
    "honor": HONOR_MODELS,
    "redmi": REDMI_MODELS,
    "xiaomi": XIAOMI_MODELS,
    "samsung": SAMSAUNG_MODELS,
}


def create_device(
    device_serial: Optional[str] = None,
    max_retries: int = 3,
    timeout: float = 30.0,
    error_handler: Optional[Callable] = None,
) -> BaseDevice:
    """自动检测设备并创建合适的实例"""
    manager = UIAutomatorManager(device_serial, max_retries, error_handler)
    device_info = manager.device.device_info
    brand = device_info.get("brand", "unknown").lower()
    model = device_info.get("model", "unknown").lower()
    logger.info(f"Wetest usb tethering version: {__version__}. Detected device: {brand} ({model})")

    models_map = SUPPORTED_BRANDS.get(brand)
    if models_map:
        device_class = models_map.get(model)
        if device_class:
            return device_class(manager, timeout)
        else:
            raise NotImplementedError(
                f"Device model '{model}' is not specifically supported for brand '{brand}'. "
                f"Supported models: {', '.join(models_map.keys())}. "
                f"Please check for updates or submit a feature request."
            )
    else:
        raise NotImplementedError(
            f"Device {brand} ({model}) is not supported. "
            f"Supported brands: {', '.join(SUPPORTED_BRANDS.keys())}. "
            f"Please check for updates or submit a feature request."
        )
