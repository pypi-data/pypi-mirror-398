from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("wetest-usb-tethering")
except PackageNotFoundError:
    __version__ = "dev"
