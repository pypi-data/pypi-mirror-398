from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("connexity")
except PackageNotFoundError:
    __version__ = "unknown"
