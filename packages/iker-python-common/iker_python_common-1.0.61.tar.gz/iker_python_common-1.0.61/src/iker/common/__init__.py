import importlib.metadata

try:
    __version__ = importlib.metadata.version("iker-python-common")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"
