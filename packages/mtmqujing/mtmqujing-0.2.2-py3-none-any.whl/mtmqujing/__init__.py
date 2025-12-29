from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version(__package__)
except PackageNotFoundError:
    __version__ = "unknown version"

from .qujing import QujingConfigAPI, QujingInvokeAPI, AsyncQujingInvokeAPI, URLModel