import importlib.metadata

try:
    __version__ = importlib.metadata.version("plexus-python-common")
except importlib.metadata.PackageNotFoundError:
    __version__ = "unknown"
