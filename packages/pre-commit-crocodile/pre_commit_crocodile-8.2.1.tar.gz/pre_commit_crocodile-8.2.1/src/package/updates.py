#!/usr/bin/env python3

# Standard libraries
from datetime import datetime
from os import access, environ, W_OK
from time import localtime, strftime, time
from typing import Optional

# Modules libraries
from packaging.version import Version as PackageVersion

# Components
from ..prints.boxes import Boxes
from ..prints.colors import Colors
from ..system.platform import Platform
from .bundle import Bundle
from .settings import Settings
from .version import Version

# Updates class
class Updates:

    # Members
    __enabled: bool
    __name: str
    __settings: Settings

    # Constructor
    def __init__(
        self,
        name: str,
        settings: Settings,
    ) -> None:

        # Initialize members
        self.__name = name
        self.__settings = settings

        # Detect migration
        self.__migration()

        # Prepare enabled
        if not self.__settings.has('updates', 'enabled'):
            self.__settings.set_bool('updates', 'enabled', True)

        # Check enabled
        self.__enabled = bool(self.__settings.get_bool('updates', 'enabled')) and \
            not environ.get(Bundle.ENV_DEBUG_UPDATES_DISABLE, '')

    # Migration
    def __migration(self) -> None:

        # Acquire versions
        current_version = Version.get()
        package_version = self.__settings.get('package', 'version')
        if not package_version:
            package_version = '0.0.0'

        # Refresh package version
        if not package_version or current_version != package_version:
            self.__settings.set('package', 'version', current_version)

    # Checker
    def check(
        self,
        older: bool = False,
    ) -> bool:

        # Reference version
        version = '0.0.0' if older else Version.get()

        # Fake test updates
        if Bundle.ENV_DEBUG_UPDATES_FAKE in environ:
            available = environ[Bundle.ENV_DEBUG_UPDATES_FAKE]
            if PackageVersion(available) >= PackageVersion(version):

                # Show updates message
                release_date = datetime.utcfromtimestamp(Bundle.RELEASE_FIRST_TIMESTAMP)
                Updates.message(
                    name=self.__name,
                    older=older,
                    available=available,
                    date=release_date,
                )
                return True

        # Check if not offline
        if not environ.get(Bundle.ENV_DEBUG_UPDATES_OFFLINE, ''):

            # Modules libraries, pylint: disable=import-outside-toplevel
            from update_checker import UpdateChecker

            # Check for updates
            check = UpdateChecker(bypass_cache=True).check(self.__name, version)
            if check: # pragma: no cover

                # Show updates message
                Updates.message(
                    name=self.__name,
                    older=older,
                    available=check.available_version,
                    date=check.release_date,
                )
                return True

        # Older offline failure
        if older:

            # Show offline message
            Updates.message(
                name=self.__name,
                offline=True,
            )
            return True

        # Result
        return False

    # Daily
    @property
    def daily(self) -> bool:

        # Acquire updates check last timestamp
        last = self.__settings.get('updates', 'last_timestamp')

        # Fake test updates
        if Bundle.ENV_DEBUG_UPDATES_DAILY in environ:
            last = None

        # Handle daily checks
        current = int(time())
        if not last or strftime('%Y-%m-%d', localtime(current)) != strftime(
                '%Y-%m-%d', localtime(int(last))):
            self.__settings.set('updates', 'last_timestamp', current)
            return True

        # Default fallback
        return False

    # Enabled
    @property
    def enabled(self) -> bool:
        return self.__enabled

    # Message, pylint: disable=too-many-arguments
    @staticmethod
    def message(
        name: str,
        offline: bool = False,
        older: bool = False,
        available: Optional[str] = None,
        date: Optional[datetime] = None,
    ) -> None:

        # Modules libraries, pylint: disable=import-outside-toplevel
        from update_checker import pretty_date

        # Create message box
        box = Boxes()

        # Acquire current version
        version = Version.get()

        # Detect package installer
        package_install: str = ''
        if Platform.PATH_SEPARATOR + 'pipx' + Platform.PATH_SEPARATOR in Version.path():
            package_install = 'pipx upgrade' # pragma: no cover
        else:
            package_install = 'pip3 install -U' # pragma: no cover

        # Detect package ownership
        writable = access(__file__, W_OK)
        if Platform.IS_USER_SUDO or not writable:
            package_install = 'sudo ' + package_install # pragma: no cover

        # Prepare package specification
        package_specification: str = ''
        if 'pipx' in package_install:
            package_specification = f'{name}' # pragma: no cover
        else:
            package_specification = f'{name}>={available}' # pragma: no cover

        # Evaluate same version
        same = available and available == version

        # Version message prefix
        version_outdated = not offline and available and not older and not same
        version_prefix = f'{Colors.YELLOW_LIGHT}Version: {Colors.BOLD}{name}' \
            f' {Colors.RED if version_outdated else Colors.GREEN}{version}'

        # Offline version message
        if offline:
            box.add(f'{version_prefix} {Colors.BOLD}not found, network might be down')

        # Updated version message
        elif same:
            box.add(
                f'{version_prefix} {Colors.BOLD}was released {pretty_date(date)}{Colors.BOLD}!'
            )

        # Older version message
        elif older:
            box.add(
                f'{version_prefix} {Colors.BOLD}newer than {Colors.RED}{available}' \
                    f' {Colors.BOLD}from {pretty_date(date)}{Colors.BOLD}!'
            )

        # Newer version message
        else:
            box.add(
                f'{version_prefix} {Colors.BOLD}updated {pretty_date(date)}' \
                    f' to {Colors.GREEN}{available}{Colors.BOLD}!'
            )

        # Changelog message
        box.add(
            f'{Colors.YELLOW_LIGHT}Changelog: {Colors.CYAN}{Bundle.REPOSITORY}/-/releases'
        )

        # Update message
        if available:
            box.add(
                f'{Colors.YELLOW_LIGHT}Update: {Colors.BOLD}' \
                    f"Run {Colors.GREEN}{package_install} '{package_specification}'"
            )

        # Print message box
        box.print()
