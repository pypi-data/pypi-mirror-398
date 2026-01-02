#!/usr/bin/env python3

# Standard libraries
from os import environ
from pathlib import Path
import sys
from sys import exit as sys_exit, path

# Bind sources
sys.dont_write_bytecode = True
path.append(str(Path(__file__).resolve().parent.parent))

# Components, pylint: disable=import-error,wrong-import-position
from system.commands import Commands

# Commitizen branch
def commitizen_branch(
    remote: str,
    ignore_empty: bool = False,
) -> int:

    # Prepare --no-raise option
    no_raise: str = '3'
    if ignore_empty:
        no_raise += ',23'

    # Check commitizen branch
    return int(
        Commands.exec('cz', [
            '--no-raise',
            no_raise,
            'check',
            '--rev-range',
            f'{remote}/HEAD..HEAD',
        ]))

# Update remote head
def git_update_remote_head(remote: str) -> bool:

    # Fetch remote branches
    Commands.run('git', [
        'fetch',
        f'{remote}',
    ])

    # Update remote head
    return bool(Commands.run('git', [
        'remote',
        'set-head',
        f'{remote}',
        '-a',
    ]))

# Main, pylint: disable=too-many-branches,too-many-statements
def main() -> None:

    # Variables
    remote: str = ''
    result: int = 1

    # Detect Git remote
    print(environ)
    if environ.get('PRE_COMMIT_REMOTE_NAME', ''):
        remote = str(environ.get('PRE_COMMIT_REMOTE_NAME'))
    else:
        remote = 'origin'

    # Check commitizen branch
    result = commitizen_branch(remote)

    # Update Git remote
    if result == 23:
        if git_update_remote_head(remote):
            result = commitizen_branch(remote)
        else:
            result = 0

    # Result
    sys_exit(result)

# Entrypoint
if __name__ == '__main__': # pragma: no cover
    main()
