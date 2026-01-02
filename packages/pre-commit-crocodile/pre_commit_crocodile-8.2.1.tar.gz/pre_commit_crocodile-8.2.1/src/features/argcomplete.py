#!/usr/bin/env python3

# Standard libraries
from pathlib import Path

# Components
from ..system.commands import Commands

# Argcomplete class
class Argcomplete:

    # Constants
    BINARY: str = 'activate-global-python-argcomplete'
    MARKER: str = 'added by argcomplete'

    # Configure
    @staticmethod
    def configure() -> bool:

        # Configure argcomplete
        return Commands.run(Argcomplete.BINARY, [
            '--user',
        ])

    # Configured
    @staticmethod
    def configured() -> bool:

        # Variables
        user_home: Path = Path.home()

        # Detect configured files
        return Commands.grep(
            Path(user_home / '.bash_completion'),
            Argcomplete.MARKER,
        ) and Commands.grep(
            Path(user_home / '.zshenv'),
            Argcomplete.MARKER,
        )
