#!/usr/bin/env python3

# Standard libraries
from configparser import ConfigParser
from pathlib import Path
from sys import stdout
from typing import Optional, Union

# Components
from ..prints.colors import Colors
from ..system.platform import Platform

# Settings class
class Settings:

    # Types
    Value = Union[int, str]

    # Constants
    SETTINGS_FILE: str = 'settings.ini'

    # Members
    __folder: Path
    __persistent: bool
    __path: Path
    __settings: ConfigParser

    # Constructor
    def __init__(self, name: str) -> None:

        # Prepare paths
        self.__folder = Platform.userspace(name)
        self.__path = self.__folder / Settings.SETTINGS_FILE
        self.__persistent = False

        # Parse settings
        self.__settings = ConfigParser()
        self.__settings.read(self.__path)

        # Prepare missing settings
        try:
            if self.get('package', 'name') != name:
                raise ValueError('Missing settings files')
            self.__persistent = True
        except ValueError:
            try:
                self.__prepare()
                self.__reset(name)
                self.__persistent = True
            except PermissionError: # pragma: no cover
                self.__persistent = False

        # Initialize settings
        if not Path(self.__path).is_file():
            self.__write()

    # Prepare
    def __prepare(self) -> None:

        # Prepare folder path
        if not Platform.IS_SIMULATED:
            self.__folder.mkdir(parents=True, exist_ok=True)

    # Reset
    def __reset(self, name: str) -> None:

        # Prepare barebone settings
        self.__settings = ConfigParser()
        self.set('package', 'name', name)

    # Writer
    def __write(self) -> None:

        # Write initial settings
        if self.__persistent and not Platform.IS_SIMULATED:
            with open(self.__path, encoding='utf8', mode='w') as output:
                self.__settings.write(output)

    # Has
    def has(self, group: str, key: str) -> bool:

        # Check settings key in group
        return group in self.__settings and key in self.__settings[group]

    # Get
    def get(self, group: str, key: str) -> Optional[Value]:

        # Get settings key in group
        if group in self.__settings and key in self.__settings[group]:
            return self.__settings[group][key]

        # Default fallback
        return None

    # Get bool
    def get_bool(self, group: str, key: str) -> Optional[bool]:

        # Get settings key as boolean
        try:
            value: str = str(self.get(group, key))
            return value.lower() == 'true' or int(value) == 1
        except (TypeError, ValueError):
            return False

    # Set
    def set(self, group: str, key: str, value: Value) -> None:

        # Prepare group
        if group not in self.__settings:
            self.__settings[group] = {}

        # Unset key
        if str(value) == 'UNSET':
            del self.__settings[group][key]

        # Set key
        else:
            self.__settings[group][key] = str(value)

        # Write updated settings
        self.__write()

    # Set bool
    def set_bool(self, group: str, key: str, value: Value) -> None:

        # Set settings key as boolean
        self.set(group, key, 1 if value else 0)

    # Show
    def show(self) -> None:

        # Settings file path
        print(' ')
        print(
            f' {Colors.GREEN}===[ {Colors.YELLOW}Settings:' \
                f' {Colors.BOLD}{self.__path} {Colors.GREEN}]==={Colors.RESET}'
        )
        print(' ')

        # Settings simulated contents
        if Platform.IS_SIMULATED:
            self.__settings.write(stdout)

        # Settings file contents
        else:
            with open(self.__path, encoding='utf8', mode='r') as data:
                print(data.read())
            Platform.flush()
