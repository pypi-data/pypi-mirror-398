#!/usr/bin/env python3

# Standard libraries
from typing import List

# Prek class, pylint: disable=too-few-public-methods
class Prek:

    # Constants
    ENGINE: str = 'prek'

    # Defaults
    DEFAULT_BINARY: str = 'prek'
    DEFAULT_PACKAGES: List[str] = [
        'prek',
        'uv',
    ]
    DEFAULT_TITLE: str = 'prek'
