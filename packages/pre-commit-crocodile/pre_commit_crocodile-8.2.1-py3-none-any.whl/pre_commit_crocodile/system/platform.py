#!/usr/bin/env python3

# Standard libraries
from os import access, environ, R_OK, sep
from os.path import expanduser
from pathlib import Path
from sys import platform, stdin, stdout
from typing import Optional

# Platform
class Platform:

    # Environment
    ENV_SIMULATE_MAC_OS: str = 'SIMULATE_MAC_OS'
    ENV_SUDO_USER: str = 'SUDO_USER'

    # Constants
    IS_LINUX: bool = platform in ['linux', 'linux2']
    IS_MAC_OS: bool = platform in ['darwin'] or ENV_SIMULATE_MAC_OS in environ
    IS_SIMULATED: bool = ENV_SIMULATE_MAC_OS in environ
    IS_WINDOWS: bool = platform in ['win32', 'win64']

    # Separators
    PATH_SEPARATOR: str = sep

    # TTYs
    IS_TTY_STDIN: bool = stdin.isatty() and stdin.encoding != 'cp1252'
    IS_TTY_STDOUT: bool = stdout.isatty()
    IS_TTY_UTF8: bool = str(stdout.encoding).lower() == 'utf-8'

    # Outputs
    IS_FLUSH_ENABLED: bool = IS_TTY_STDOUT or IS_WINDOWS

    # Users
    IS_USER_SUDO: bool = ENV_SUDO_USER in environ
    USER_SUDO: str = environ[ENV_SUDO_USER] if IS_USER_SUDO else ''

    # Bashrc
    @staticmethod
    def bashrc() -> Optional[Path]:

        # Variables
        bashrc: None | Path = None
        home: Path = Path.home()

        # Detect .bashrc
        if Path(home / '.bashrc').exists():
            bashrc = Path(home / '.bashrc')

        # Detect .bash_user.rc
        if Path(home / '.bash_user.rc').exists():
            bashrc = home / '.bash_user.rc'

        # Result
        return bashrc

    # Flush
    @staticmethod
    def flush() -> None:

        # Flush output
        print(
            '',
            end='',
            flush=Platform.IS_FLUSH_ENABLED,
        )

    # Userspace
    @staticmethod
    def userspace(name: str) -> Path:

        # Variables
        home: None | Path = None

        # Elevated home
        if Platform.IS_USER_SUDO: # pragma: linux cover
            home = Path(expanduser(f'~{Platform.USER_SUDO}'))
            if not access(home, R_OK): # pragma: no cover
                home = None

        # Default home
        if not home or not home.is_dir():
            home = Path.home()

        # Windows userspace
        if Platform.IS_WINDOWS: # pragma: windows cover
            return home / 'AppData' / 'Local' / name

        # macOS userspace
        if Platform.IS_MAC_OS: # pragma: macos cover
            return home / 'Library' / 'Preferences' / name

        # Linux userspace
        return home / '.config' / name # pragma: linux cover
