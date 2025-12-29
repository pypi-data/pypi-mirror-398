import sys

if sys.platform == "win32":
    from .windows import home_dir
else:
    from ._posix import home_dir

__all__ = ["home_dir"]
