from importlib.metadata import PackageNotFoundError, version

from pyscribe.errors import FileTooLargeError, PyscribeError
from pyscribe.transcriber import atranscribe, transcribe

try:
    __version__ = version("pyscribest")
except PackageNotFoundError:
    __version__ = "0.0.0.dev0"

__all__ = [
    "FileTooLargeError",
    "PyscribeError",
    "__version__",
    "atranscribe",
    "transcribe",
]
