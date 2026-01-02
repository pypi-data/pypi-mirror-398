#!/usr/bin/env python3

# Standard libraries
from pathlib import Path
from typing import List

# Readme class
class Readme:

    # Constants
    EOL: str = '\n'
    FILE: str = 'README.md'

    # Exists
    @staticmethod
    def exists() -> bool:

        # Check if binary exists
        return Path(Readme.FILE).exists()

    # Read
    @staticmethod
    def read() -> List[str]:

        # Ignore missing file
        if not Readme.exists(): # pragma: no cover
            return []

        # Read file contents
        with open(
                Readme.FILE,
                encoding='utf8',
                mode='r',
        ) as file:
            return file.readlines()

    # Write
    @staticmethod
    def write(lines: List[str]) -> None:

        # Write file contents
        with open(
                Readme.FILE,
                encoding='utf8',
                mode='w',
        ) as file:
            file.writelines(lines)
