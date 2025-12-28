from importlib.metadata import version, PackageNotFoundError
try:
    __version__ = version("django-8e9e15-v1")
except PackageNotFoundError:
    import sys
    sys.tracebacklimit = 0
    raise ImportError()