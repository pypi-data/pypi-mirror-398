__version__ = "0.0.0"
# Try to import the version from the generated _version.py file
try:
    from ._version import __version__  # noqa: F401
except (ImportError, ModuleNotFoundError):
    pass
