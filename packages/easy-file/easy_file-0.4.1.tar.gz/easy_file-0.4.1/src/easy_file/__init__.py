"""Easy File - Files for humans."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("easy_file")
except PackageNotFoundError:
    __version__ = "0.0.0.dev0"

from easy_file.easy_file import (
    File,
    FileOperationError,
    JSONDecodeError,
    YAMLDecodeError,
)

__all__ = [
    "__version__",
    "File",
    "FileOperationError",
    "JSONDecodeError",
    "YAMLDecodeError",
]
