from importlib.metadata import version

from .data import Engine, ZRXPData, ZRXPMetadata
from .reader import read
from .writer import write, writes

__all__ = [
    "Engine",
    "ZRXPData",
    "ZRXPMetadata",
    "read",
    "write",
    "writes",
]

try:
    __version__ = version("zrxp")
except ImportError:
    __version__ = "unknown"
