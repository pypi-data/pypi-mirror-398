from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, TypeVar

if sys.platform == "win32":
    from .platforms.windows import (
        desktop_dir,
        documents_dir,
        downloads_dir,
        home_dir,
        music_dir,
        pictures_dir,
        public_dir,
        videos_dir,
    )
elif sys.platform == "darwin":
    from .platforms.macos import (
        desktop_dir,
        documents_dir,
        downloads_dir,
        home_dir,
        music_dir,
        pictures_dir,
        public_dir,
    )
    from .platforms.macos import movies_dir as videos_dir
else:
    from .xdg import (
        desktop_dir,
        documents_dir,
        downloads_dir,
        home_dir,
        music_dir,
        pictures_dir,
        public_dir,
        videos_dir,
    )

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence

    PathOrSequencePath = TypeVar("PathOrSequencePath", bound=Path | Sequence[Path])

__all__ = [
    "iter_dirs",
    "app_name",
    "join_on",
    "dir_on",
    "cache_dir",
    "config_dir",
    "data_dir",
    "log_dir",
    "system_config_dirs",
    "system_data_dirs",
    "home_dir",
    "desktop_dir",
    "documents_dir",
    "downloads_dir",
    "music_dir",
    "pictures_dir",
    "public_dir",
    "videos_dir",
    "AppDirs",
]


def iter_dirs(*args: Path | Sequence[Path]) -> Iterator[Path]:
    for arg in args:
        if isinstance(arg, Path):
            yield arg
        else:
            yield from arg


def _on(windows=None, macos=None, posix=None, others=None):
    if sys.platform == "win32":
        if windows is not None:
            return windows
    else:  # posix
        if sys.platform == "darwin":
            if macos is not None:
                return macos
        if posix is not None:
            return posix

    if others is not None:
        return others

    raise NotImplementedError(f"unsupported platform '{sys.platform}'")


def app_name(
    app: str, org: str = "", tld: str = "", *, posix_lowercase_app: bool = True
) -> str:
    return _on(
        windows="\\".join(filter(None, [org, app])),
        posix=".".join(
            filter(
                None,
                [tld.lower(), org.lower(), app.lower() if posix_lowercase_app else app],
            )
        ).replace(" ", "-"),
    )


def join_on(
    path: str | Path,
    *,
    windows: str | Path | None = None,
    macos: str | Path | None = None,
    posix: str | Path | None = None,
    others: str | Path | None = None,
) -> Path:
    return Path(path, _on(windows, macos, posix, others))


def dir_on(
    *,
    windows: Callable[..., PathOrSequencePath] | None = None,
    macos: Callable[..., PathOrSequencePath] | None = None,
    posix: Callable[..., PathOrSequencePath] | None = None,
    others: Callable[..., PathOrSequencePath] | None = None,
) -> PathOrSequencePath:
    return _on(windows, macos, posix, others)()


def _windows_data_dir(system, roaming=True):
    from .platforms.windows import (
        GUID,
        app_data_local_dir,
        app_data_roaming_dir,
        known_folder,
    )

    return (
        known_folder(GUID.from_int(0x62AB5D82_FDC1_4DC3_A9DD_070D1D495D97))
        if system
        else (app_data_roaming_dir() if roaming else app_data_local_dir())
    )


def _macos_cache_dir(system):
    from .platforms.macos import caches_dir

    return Path("/Library/Caches") if system else caches_dir()


def _macos_data_dir(system):
    from .platforms.macos import application_support_dir

    return Path("/Library/Application Support") if system else application_support_dir()


def _macos_log_dir(system):
    from .platforms.macos import logs_dir

    return Path("/Library/Logs") if system else logs_dir()


def _posix_cache_dir(system):
    from .xdg import cache_dir

    return Path("/var/cache") if system else cache_dir()


def _posix_config_dir(system, local=False):
    from .xdg import config_dir

    return Path("/", "usr/local" * local, "etc") if system else config_dir()


def _posix_data_dir(system, local=False):
    from .xdg import data_dir

    return Path("/usr", "local" * local, "share") if system else data_dir()


def _posix_log_dir(system):
    from .xdg import state_dir

    return Path("/var/log") if system else state_dir()


def _posix_system_config_dirs(xdg):
    from .xdg import config_dirs

    return config_dirs() if xdg else [Path("/usr/local/etc"), Path("/etc")]


def _posix_system_data_dirs(xdg):
    from .xdg import data_dirs

    return data_dirs() if xdg else [Path("/usr/local/share"), Path("/usr/share")]


def cache_dir(*, system: bool = False, macos_asposix: bool = False) -> Path:
    return dir_on(
        windows=lambda: _windows_data_dir(system, roaming=False),
        macos=None if macos_asposix else lambda: _macos_cache_dir(system),
        posix=lambda: _posix_cache_dir(system),
    )


def config_dir(
    *, system: bool = False, macos_asposix: bool = False, posix_local: bool = False
) -> Path:
    return dir_on(
        windows=lambda: _windows_data_dir(system, roaming=True),
        macos=None if macos_asposix else lambda: _macos_data_dir(system),
        posix=lambda: _posix_config_dir(system, posix_local),
    )


def data_dir(
    *,
    system: bool = False,
    windows_roaming: bool = True,
    macos_asposix: bool = False,
    posix_local: bool = False,
) -> Path:
    return dir_on(
        windows=lambda: _windows_data_dir(system, windows_roaming),
        macos=None if macos_asposix else lambda: _macos_data_dir(system),
        posix=lambda: _posix_data_dir(system, posix_local),
    )


def log_dir(*, system: bool = False, macos_asposix: bool = False) -> Path:
    return dir_on(
        windows=lambda: _windows_data_dir(system, roaming=False),
        macos=None if macos_asposix else lambda: _macos_log_dir(system),
        posix=lambda: _posix_log_dir(system),
    )


def system_config_dirs(
    *, macos_asposix: bool = False, posix_xdg: bool = False
) -> list[Path]:
    return dir_on(
        windows=lambda: [_windows_data_dir(system=True)],
        macos=None if macos_asposix else lambda: [_macos_data_dir(system=True)],
        posix=lambda: _posix_system_config_dirs(posix_xdg),
    )


def system_data_dirs(
    *, macos_asposix: bool = False, posix_xdg: bool = False
) -> list[Path]:
    return dir_on(
        windows=lambda: [_windows_data_dir(system=True)],
        macos=None if macos_asposix else lambda: [_macos_data_dir(system=True)],
        posix=lambda: _posix_system_data_dirs(posix_xdg),
    )


class AppDirs:
    def __init__(
        self,
        app_name: str,
        *,
        system: bool = False,
        windows_roaming: bool = True,
        macos_asposix: bool = False,
        posix_local: bool = False,
        posix_xdg: bool = False,
    ) -> None:
        self.app_name = app_name
        self.system = system
        self.windows_roaming = windows_roaming
        self.macos_asposix = macos_asposix
        self.posix_local = posix_local
        self.posix_xdg = posix_xdg

    def _attr_if_none(self, **kwargs):
        for key, val in kwargs.items():
            if val is None:
                kwargs[key] = getattr(self, key)
        return kwargs

    def cache_dir(
        self, *, system: bool | None = None, macos_asposix: bool | None = None
    ) -> Path:
        kwargs = self._attr_if_none(system=system, macos_asposix=macos_asposix)
        return join_on(cache_dir(**kwargs) / self.app_name, windows="Caches", posix="")

    def config_dir(
        self,
        *,
        system: bool | None = None,
        macos_asposix: bool | None = None,
        posix_local: bool | None = None,
    ) -> Path:
        kwargs = self._attr_if_none(
            system=system, macos_asposix=macos_asposix, posix_local=posix_local
        )
        return join_on(
            config_dir(**kwargs) / self.app_name, windows="Settings", posix=""
        )

    def data_dir(
        self,
        *,
        system: bool | None = None,
        windows_roaming: bool | None = None,
        macos_asposix: bool | None = None,
        posix_local: bool | None = None,
    ) -> Path:
        kwargs = self._attr_if_none(
            system=system,
            windows_roaming=windows_roaming,
            macos_asposix=macos_asposix,
            posix_local=posix_local,
        )
        return data_dir(**kwargs) / self.app_name

    def log_dir(
        self, *, system: bool | None = None, macos_asposix: bool | None = None
    ) -> Path:
        kwargs = self._attr_if_none(system=system, macos_asposix=macos_asposix)
        return join_on(log_dir(**kwargs) / self.app_name, windows="Logs", posix="")

    def system_config_dirs(
        self, *, macos_asposix: bool | None = None, posix_xdg: bool | None = None
    ) -> list[Path]:
        kwargs = self._attr_if_none(macos_asposix=macos_asposix, posix_xdg=posix_xdg)
        return [
            join_on(dir / self.app_name, windows="Settings", posix="")
            for dir in system_config_dirs(**kwargs)
        ]

    def system_data_dirs(
        self, *, macos_asposix: bool | None = None, posix_xdg: bool | None = None
    ) -> list[Path]:
        kwargs = self._attr_if_none(macos_asposix=macos_asposix, posix_xdg=posix_xdg)
        return [dir / self.app_name for dir in system_data_dirs(**kwargs)]
