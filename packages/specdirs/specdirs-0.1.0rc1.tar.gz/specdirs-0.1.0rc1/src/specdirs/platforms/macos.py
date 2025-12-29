from pathlib import Path

from ._posix import home_dir as home_dir


def application_support_dir() -> Path:
    return home_dir() / "Library/Application Support"


def caches_dir() -> Path:
    return home_dir() / "Library/Caches"


def logs_dir() -> Path:
    return home_dir() / "Library/Logs"


def desktop_dir() -> Path:
    return home_dir() / "Desktop"


def documents_dir() -> Path:
    return home_dir() / "Documents"


def downloads_dir() -> Path:
    return home_dir() / "Downloads"


def movies_dir() -> Path:
    return home_dir() / "Movies"


def music_dir() -> Path:
    return home_dir() / "Music"


def pictures_dir() -> Path:
    return home_dir() / "Pictures"


def public_dir() -> Path:
    return home_dir() / "Public"
