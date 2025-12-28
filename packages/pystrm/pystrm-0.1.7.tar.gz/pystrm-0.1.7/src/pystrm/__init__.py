from importlib.metadata import version, PackageNotFoundError
from pystrm.main import main_function

try:
    __version__ = version("pystrm")
except PackageNotFoundError:
    # Handle the case where the package is not installed (e.g., running locally from source)
    __version__ = "0.0.0"

__all__ = ("main_function",)