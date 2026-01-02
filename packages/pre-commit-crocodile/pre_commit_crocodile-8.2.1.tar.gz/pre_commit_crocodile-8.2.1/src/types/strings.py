#!/usr/bin/env python3

# Standard libraries
from typing import List

# Components
from ..prints.colors import Colors

# Strings class
class Strings:

    # Center
    @staticmethod
    def center(string: str, length: int) -> str:

        # Extract text
        text: str = Colors.strip(string)

        # Center string
        if len(text) < length:
            paddings = length - len(text)
            left = paddings // 2
            right = -(-paddings // 2)
            return ' ' * left + string + ' ' * right

        # Default string
        return string

    # Quote
    @staticmethod
    def quote(string: str) -> str: # pragma: no cover

        # Single quotes
        if '\'' not in string:
            return '\'' + string + '\''

        # Double quotes
        if '\"' not in string:
            return '\"' + string + '\"'

        # Adaptive quotes
        return '\'' + string.replace('\'', '\\\'') + '\''

    # Wrap
    @staticmethod
    def wrap(string: str, length: int) -> List[str]:

        # Variables
        color: str = ''
        index: int = 0
        line_data: str = ''
        line_length: int = 0
        lines: List[str] = []
        space: str = ''
        word: str = ''

        # Length limitations
        length = max(length, 1)

        # Append line
        def append_line() -> None:
            nonlocal line_data, line_length, lines
            if line_length > 0:
                lines += [line_data]
                line_data = ''
                line_length = 0

        # Store word
        def store_word() -> None:
            nonlocal color, length, line_data, line_length, space, word
            if len(word) > 0:

                # Word overflows
                if line_length + len(space) + len(word) > length:
                    word_full = word
                    if len(word_full) > length:
                        while len(word_full) > 0:
                            word = word_full[0:length]
                            store_word()
                            word_full = word_full[length:]
                    append_line()

                # Word spacing
                if line_length > 0 and space:
                    line_data += space
                    line_length += len(space)
                space = ''

                # Word appendation
                line_data += color + word
                line_length += len(word)
                word = ''

                # Line wrapping
                if line_length >= length:
                    append_line()

        # Add char
        def add_char(char: str) -> None:
            nonlocal index, word
            index += 1
            word += char

        # Iterate through chars
        while index < len(string):

            # Space separator
            if string[index] == ' ':

                # Store last word
                store_word()

                # Reset word data
                space += ' '
                index += 1
                continue

            # Color marker
            for item in Colors.ALL:
                if item and string[index:].startswith(item):

                    # Store last word
                    store_word()

                    # Store new color
                    color = item
                    index += len(color)
                    break

            # Text content
            else:

                # Append character
                add_char(string[index])

        # Store last word
        store_word()

        # Append last line
        append_line()

        # Result
        return lines
