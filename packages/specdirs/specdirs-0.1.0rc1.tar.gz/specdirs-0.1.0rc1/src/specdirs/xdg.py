import os
from pathlib import Path

from .platforms import home_dir as home_dir

_USER_DIRS = None


def _base_dir(env_var, default):
    if (value := os.getenv(env_var)) is not None:
        if (path := Path(value)).is_absolute():
            return path
    return default


def _base_dirs(env_var, default):
    if (value := os.getenv(env_var)) is not None:
        paths = [
            path for dir in value.split(os.pathsep) if (path := Path(dir)).is_absolute()
        ]
        if paths:
            return paths
    return default


def _parse_user_dirs_file():
    user_dirs = {}
    user_dirs_path = config_dir() / "user-dirs.dirs"
    if user_dirs_path.exists():
        with user_dirs_path.open() as file:
            for line in file.readlines():
                if line.startswith("XDG_"):
                    key, value = line.split("=")
                    path = Path(
                        value.rstrip().strip('"').replace("$HOME", str(home_dir()), 1)
                    )
                    if path.is_absolute():
                        user_dirs[key] = path
    return user_dirs


def _user_dir(env_var):
    global _USER_DIRS
    _USER_DIRS = _parse_user_dirs_file() if _USER_DIRS is None else _USER_DIRS

    return _USER_DIRS.get(env_var, home_dir())


def bin_dir() -> Path:
    return _base_dir("XDG_BIN_HOME", home_dir() / ".local/bin")


def cache_dir() -> Path:
    return _base_dir("XDG_CACHE_HOME", home_dir() / ".cache")


def config_dir() -> Path:
    return _base_dir("XDG_CONFIG_HOME", home_dir() / ".config")


def data_dir() -> Path:
    return _base_dir("XDG_DATA_HOME", home_dir() / ".local/share")


def state_dir() -> Path:
    return _base_dir("XDG_STATE_HOME", home_dir() / ".local/state")


def runtime_dir() -> Path | None:
    return _base_dir("XDG_RUNTIME_DIR", None)


def data_dirs() -> list[Path]:
    return _base_dirs("XDG_DATA_DIRS", [Path("/usr/local/share"), Path("/usr/share")])


def config_dirs() -> list[Path]:
    return _base_dirs("XDG_CONFIG_DIRS", [Path("/etc/xdg")])


def desktop_dir() -> Path:
    return _user_dir("XDG_DESKTOP_DIR")


def documents_dir() -> Path:
    return _user_dir("XDG_DOCUMENTS_DIR")


def downloads_dir() -> Path:
    return _user_dir("XDG_DOWNLOAD_DIR")


def music_dir() -> Path:
    return _user_dir("XDG_MUSIC_DIR")


def pictures_dir() -> Path:
    return _user_dir("XDG_PICTURES_DIR")


def public_dir() -> Path:
    return _user_dir("XDG_PUBLICSHARE_DIR")


def templates_dir() -> Path:
    return _user_dir("XDG_TEMPLATES_DIR")


def videos_dir() -> Path:
    return _user_dir("XDG_VIDEOS_DIR")
