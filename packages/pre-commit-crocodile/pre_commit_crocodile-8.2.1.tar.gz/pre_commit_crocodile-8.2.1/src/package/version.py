#!/usr/bin/env python3

# Standard libraries
from os import environ
from sys import version_info

# Components
from ..system.platform import Platform
from .bundle import Bundle

# Version class
class Version:

    # Getter
    @staticmethod
    def get() -> str:

        # Fake test version
        if Bundle.ENV_DEBUG_VERSION_FAKE in environ:
            return environ[Bundle.ENV_DEBUG_VERSION_FAKE]

        # Acquire version from metadata
        try:
            from importlib import metadata # pylint: disable=import-outside-toplevel
            return metadata.version(Bundle.PACKAGE)
        except Exception: # pylint: disable=broad-exception-caught # pragma: no cover
            pass

        # Acquire version from resources
        try: # pragma: no cover
            import importlib.metadata # pylint: disable=import-outside-toplevel
            name = __name__.split('.', maxsplit=1)[0]
            return importlib.metadata.version(name)

        # Acquire version from package resources
        except Exception: # pylint: disable=broad-exception-caught # pragma: no cover
            try:
                import importlib.metadata # pylint: disable=import-outside-toplevel
                return importlib.metadata.version(Bundle.PACKAGE)

            # Default fallback
            except Exception: # pylint: disable=broad-exception-caught # pragma: no cover
                return '0.0.0'

    # Path
    @staticmethod
    def path() -> str:

        # Acquire path
        path = __file__

        # Strip package path
        index = path.rfind(Platform.PATH_SEPARATOR)
        index = path.rfind(Platform.PATH_SEPARATOR, 0, index)
        path = path[0:index]

        # Result
        return path

    # Python
    @staticmethod
    def python() -> str:

        # Acquire Python version
        version = f'{version_info.major}.{version_info.minor}'

        # Result
        return version

    # Revision
    @staticmethod
    def revision() -> str:

        # Force package revision
        if Bundle.ENV_DEBUG_REVISION_SHA in environ:
            return environ[Bundle.ENV_DEBUG_REVISION_SHA]

        # Acquire package version
        version: str = Version.get()

        # Handle development version
        if '+g' in version:
            version = version.replace('.dev', '-')
            version = version.replace('+g', '-g')
            return version.rsplit('.d', 1)[0]

        # Result
        return version
