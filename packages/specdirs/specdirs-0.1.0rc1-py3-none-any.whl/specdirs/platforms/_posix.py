import os
from pathlib import Path


def home_dir() -> Path:
    if (home := os.getenv("HOME")) is None:
        from pwd import getpwuid

        home = getpwuid(os.getuid()).pw_dir

    return Path(home)
