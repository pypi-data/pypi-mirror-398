#!/usr/bin/env python3

# Standard libraries
from typing import List

# Modules libraries
try:
    try: # colored>=2.0.0
        from colored import Colored
    except ImportError: # colored<2.0.0 # pragma: no cover
        from colored import colored as Colored # type: ignore[assignment]
except ModuleNotFoundError: # pragma: no cover
    pass

# Components
from ..system.platform import Platform

# Colors class, pylint: disable=too-few-public-methods
class Colors:

    # Attributes
    ALL: List[str] = []
    BOLD = ''
    CYAN = ''
    GREEN = ''
    GREY = ''
    RED = ''
    RESET = ''
    YELLOW = ''
    YELLOW_LIGHT = ''

    # Symbols
    ARROW = ''

    # Enabled
    @staticmethod
    def enabled() -> bool:

        # Result
        try:
            return bool(Colored('').enabled())
        except (NameError, TypeError): # pragma: no cover
            return False

    # Prepare
    @staticmethod
    def prepare() -> None:

        # Colors enabled
        if Colors.enabled():
            Colors.RESET = Colored('reset').attribute()
            Colors.BOLD = Colors.RESET + Colored('bold').attribute()
            Colors.CYAN = Colors.BOLD + Colored('cyan').foreground()
            Colors.GREEN = Colors.BOLD + Colored('green').foreground()
            Colors.GREY = Colors.BOLD + Colored('light_gray').foreground()
            Colors.RED = Colors.BOLD + Colored('red').foreground()
            Colors.YELLOW = Colors.BOLD + Colored('yellow').foreground()
            Colors.YELLOW_LIGHT = Colors.BOLD + Colored('light_yellow').foreground()
            Colors.ALL = [
                Colors.CYAN,
                Colors.GREEN,
                Colors.GREY,
                Colors.RED,
                Colors.YELLOW,
                Colors.YELLOW_LIGHT,
                Colors.BOLD,
                Colors.RESET,
            ]

        # Colors disabled
        else:
            Colors.BOLD = ''
            Colors.CYAN = ''
            Colors.GREEN = ''
            Colors.GREY = ''
            Colors.RED = ''
            Colors.RESET = ''
            Colors.YELLOW = ''
            Colors.YELLOW_LIGHT = ''
            Colors.ALL = []

        # UTF8 symbols
        if Platform.IS_TTY_UTF8:
            Colors.ARROW = '‣'

        # ASCII symbols
        else:
            Colors.ARROW = '>'

    # Strip
    @staticmethod
    def strip(string: str) -> str:

        # Strip all colors
        for item in Colors.ALL:
            string = string.replace(item, '')

        # Result
        return string
