#!/usr/bin/env python3

# Standard libraries
from sys import argv, exit as sys_exit
from typing import List

# Modules libraries
from ruamel.yaml import YAML
from ruamel.yaml.error import YAMLError

# INFO:
# - New specific implementation for ruamel.yaml pure Python implementation only
# - Recommendations for 'YAML(typ='safe', pure=True)':
#   - https://stackoverflow.com/a/62160118
#   - https://sourceforge.net/p/ruamel-yaml/tickets/391/
# - Issues:
#   - https://github.com/pre-commit/pre-commit-hooks/issues/827
#   - https://github.com/pre-commit/pre-commit-hooks/issues/918
#   - https://github.com/pre-commit/pre-commit-hooks/issues/984
#   - https://github.com/pre-commit/pre-commit-hooks/pull/641
#   - https://github.com/pre-commit/pre-commit-hooks/pull/828

# Check YAML file
def check_yaml_file(file_path: str) -> bool:

    # Instantiate YAML class
    yaml = YAML(
        typ='safe',
        pure=True,
    )

    # Validate YAML file
    try:
        with open(
                file_path,
                encoding='utf8',
                mode='r',
        ) as file:
            for _ in yaml.parse(file):
                pass
        return True

    # Failure handlings
    except YAMLError as exc:
        print(exc)
        return False

# Main, pylint: disable=too-many-branches,too-many-statements
def main() -> None:

    # Variables
    file_paths: List[str]
    result: bool = True

    # Validate arguments
    if len(argv) <= 1:
        sys_exit(1)

    # Parse arguments
    file_paths = argv[1:]

    # Check YAML files
    for file_path in file_paths:
        if not check_yaml_file(file_path):
            result = False

    # Result
    sys_exit(0 if result else 1)

# Entrypoint
if __name__ == '__main__': # pragma: no cover
    main()
