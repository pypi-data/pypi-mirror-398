#!/usr/bin/env python3

# Standard libraries
from os import environ
from typing import Dict, List, NamedTuple

# Environments class
class Environments:

    # Constants
    LINE_EOL: str = '\n'

    # Variable
    class Variable(NamedTuple):

        # Variables
        name: str
        description: str
        fallback: str

        # Value
        @property
        def value(self) -> str:
            if self.fallback:
                return environ.get(self.name, environ.get(self.fallback, ''))
            return environ.get(self.name, '')

    # Members
    __group: str
    __variables: Dict[str, Variable]

    # Constructor
    def __init__(self) -> None:
        self.__group = ''
        self.__variables = {}

    # Group
    @property
    def group(self) -> str:
        return self.__group

    # Group
    @group.setter
    def group(self, value: str) -> None:
        self.__group = value

    # Add
    def add(
        self,
        key: str,
        name: str,
        description: str,
        fallback: str = '',
    ) -> None:

        # Append variable to list
        self.__variables[key] = Environments.Variable(
            name=name,
            description=description,
            fallback=fallback,
        )

    # Help
    def help(self, help_position: int) -> str:

        # Variables
        lines: List[str] = []

        # Append group
        if self.__group:
            lines += [f'{self.__group}:']

        # Append variables
        for _, variable in self.__variables.items():
            line = f'  {variable.name: <{help_position - 2}}'
            line += f'{variable.description}'
            if variable.fallback:
                line += f' (fallback: {variable.fallback})'
            lines += [line]

        # Result
        return Environments.LINE_EOL.join(lines)

    # Value
    def value(self, key: str) -> str:

        # Get value of declared variable
        if key in self.__variables:
            return self.__variables[key].value

        # Fallback
        return ''
