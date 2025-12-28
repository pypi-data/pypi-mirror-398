class TetheringException(Exception):
    """USB网络共享基础异常类"""

    pass


class SettingsAppException(TetheringException):
    """未找到设置应用异常"""

    pass


class DeviceException(TetheringException):
    """未连接到设备异常"""

    pass


class UIAutomatorOccupiedException(TetheringException):
    """UIAutomator被占用异常"""

    pass


class FileMismatchException(TetheringException):
    """文件大小/MD5不匹配异常"""

    pass


class PCHostIPException(TetheringException):
    """PC主机IP获取异常"""

    pass


class TimeoutException(TetheringException):
    """下载文件超时异常"""

    pass


class DownloadException(TetheringException):
    """下载文件异常"""

    pass
