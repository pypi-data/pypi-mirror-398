#!/usr/bin/env python3

# Standard libraries
from argparse import (
    _ArgumentGroup,
    _MutuallyExclusiveGroup,
    ArgumentParser,
    Namespace,
    RawTextHelpFormatter,
)
from os import environ
from shutil import get_terminal_size
from sys import exit as sys_exit
from time import sleep

# Components
from ..features.precommit import PreCommit
from ..features.prek import Prek
from ..package.bundle import Bundle
from ..package.settings import Settings
from ..package.updates import Updates
from ..package.version import Version
from ..prints.colors import Colors
from ..system.platform import Platform
from ..types.environments import Environments
from .entrypoint import Entrypoint

# Constants
HELP_POSITION: int = 25

# Main, pylint: disable=too-many-branches,too-many-statements
def main() -> None:

    # Variables
    environments: Environments
    group: _ArgumentGroup
    result: Entrypoint.Result = Entrypoint.Result.ERROR
    subgroup: _MutuallyExclusiveGroup

    # Configure environment variables
    environments = Environments()

    # Configure pre-commit
    PreCommit.configure()

    # Arguments creation
    parser: ArgumentParser = ArgumentParser(
        prog=Bundle.NAME,
        description=f'{Bundle.NAME}: {Bundle.DESCRIPTION}',
        epilog=environments.help(HELP_POSITION),
        add_help=False,
        formatter_class=lambda prog: RawTextHelpFormatter(
            prog,
            max_help_position=HELP_POSITION,
            width=min(
                120,
                get_terminal_size().columns - 2,
            ),
        ),
    )

    # Arguments internal definitions
    group = parser.add_argument_group('internal arguments')
    group.add_argument(
        '-h',
        '--help',
        dest='help',
        action='store_true',
        help='Show this help message',
    )
    group.add_argument(
        '--version',
        dest='version',
        action='store_true',
        help='Show the current version',
    )
    group.add_argument(
        '--no-color',
        dest='no_color',
        action='store_true',
        help=f'Disable colors outputs with \'{Bundle.ENV_NO_COLOR}=1\'\n'
        '(or default settings: [themes] > no_color)',
    )
    group.add_argument(
        '--update-check',
        dest='update_check',
        action='store_true',
        help='Check for newer package updates',
    )
    group.add_argument(
        '--settings',
        dest='settings',
        action='store_true',
        help='Show the current settings path and contents',
    )
    group.add_argument(
        '--set',
        dest='set',
        action='store',
        metavar=('GROUP', 'KEY', 'VAL'),
        nargs=3,
        help='Set settings specific \'VAL\' value to [GROUP] > KEY\n' \
             'or unset by using \'UNSET\' as \'VAL\'',
    )

    # Arguments modes definitions
    group = parser.add_argument_group('modes arguments')
    subgroup = group.add_mutually_exclusive_group()
    subgroup.add_argument(
        '-l',
        '--list',
        dest='list',
        action='store_true',
        help='List Git hooks installed in sources',
    )
    subgroup.add_argument(
        '-i',
        '--install',
        dest='install',
        action='store_true',
        help='Install dependencies for pre-commit hooks',
    )
    subgroup.add_argument(
        '-c',
        '--configure',
        dest='configure',
        action='store_true',
        help='Update sources with hooks configurations',
    )
    subgroup.add_argument(
        '-b',
        '--badges',
        dest='badges',
        action='store_true',
        help='Update documentation with badges configurations',
    )
    subgroup.add_argument(
        '-e',
        '--enable',
        dest='enable',
        action='store_true',
        help='Enable pre-commit hooks',
    )
    subgroup.add_argument(
        '-d',
        '--disable',
        dest='disable',
        action='store_true',
        help='Disable pre-commit hooks',
    )
    subgroup.add_argument(
        '-a',
        '--autoupdate',
        dest='autoupdate',
        action='store_true',
        help='Autoupdate pre-commit hooks',
    )
    subgroup.add_argument(
        '-C',
        '--clean',
        dest='clean',
        action='store_true',
        help='Clean pre-commit cached hooks',
    )
    subgroup.add_argument(
        '-r',
        '--run',
        dest='run',
        action='store_true',
        help='Run pre-commit hooks',
    )

    # Arguments configurations definitions
    group = parser.add_argument_group('configurations arguments')
    subgroup = group.add_mutually_exclusive_group()
    subgroup.add_argument(
        '--config',
        dest='config',
        action='store',
        metavar='FOLDER',
        help='Use configurations from a specific folder',
    )
    subgroup.add_argument(
        '-D',
        '--default',
        dest='default',
        action='store_true',
        help='Use global default configurations instead of sources',
    )
    group.add_argument(
        '--commit',
        dest='commit',
        action='store_true',
        help='Commit configurations changes automatically (implies --configure)',
    )
    subgroup = group.add_mutually_exclusive_group()
    subgroup.add_argument(
        '--components',
        dest='components',
        action='store_true',
        help='Import components from GitLab with \'include: component:\'',
    )
    subgroup.add_argument(
        '--remotes',
        dest='remotes',
        action='store_true',
        help='Import components from GitLab with \'include: remote:\'',
    )
    subgroup.add_argument(
        '--no-components',
        dest='no_components',
        action='store_true',
        help='Import components templates locally instead of \'include: component:\'',
    )
    group.add_argument(
        '--offline',
        dest='offline',
        action='store_true',
        help='Use offline mode to disable configurations autoupdate',
    )
    group.add_argument(
        '--stage',
        dest='stage',
        action='store',
        metavar='STAGE',
        help='Run a specific pre-commit stage with --run\n' \
             '(use \'list\' to list supported stages)',
    )

    # Arguments settings definitions
    group = parser.add_argument_group('settings arguments')
    group.add_argument(
        '--set-engine',
        dest='set_engine',
        metavar='ENGINE',
        type=lambda x: str(x) if str(x) in (PreCommit.ENGINE, Prek.ENGINE) else None,
        nargs='?',
        const=PreCommit.ENGINE,
        help='Set pre-commit engine to use'
        f' ({PreCommit.ENGINE}, {Prek.ENGINE}, default: %(const)s)',
    )

    # Arguments positional definitions
    group = parser.add_argument_group('positional arguments')
    group.add_argument(
        '--',
        dest='double_dash',
        action='store_true',
        help='Positional arguments separator (recommended)',
    )

    # Arguments parser
    options: Namespace = parser.parse_args()

    # Help informations
    if options.help:
        print(' ')
        parser.print_help()
        print(' ')
        Platform.flush()
        sys_exit(0)

    # Instantiate settings
    settings: Settings = Settings(name=Bundle.NAME)

    # Prepare no_color
    if not options.no_color:
        if settings.has('themes', 'no_color'):
            options.no_color = settings.get_bool('themes', 'no_color')
        else:
            options.no_color = False
            settings.set_bool('themes', 'no_color', options.no_color)

    # Configure no_color
    if options.no_color:
        environ[Bundle.ENV_FORCE_COLOR] = '0'
        environ[Bundle.ENV_NO_COLOR] = '1'

    # Prepare colors
    Colors.prepare()

    # Settings setter
    if options.set:
        settings.set(options.set[0], options.set[1], options.set[2])
        settings.show()
        sys_exit(0)

    # Settings informations
    if options.settings:
        settings.show()
        sys_exit(0)

    # Instantiate updates
    updates: Updates = Updates(
        name=Bundle.PACKAGE,
        settings=settings,
    )

    # Version informations
    if options.version:
        print(
            f'{Bundle.NAME} {Version.get()} from {Version.path()} (python {Version.python()})'
        )
        Platform.flush()
        sys_exit(0)

    # Check for current updates
    if options.update_check:
        if not updates.check():
            updates.check(older=True)
        sys_exit(0)

    # Engine setter
    if options.set_engine:
        settings.set('engines', 'pre_commit', options.set_engine)
        settings.show()
        sys_exit(0)

    # Implicit modes
    if options.commit and not options.configure and not options.badges:
        options.configure = True

    # Arguments modes
    if options.autoupdate:
        options.enable = True
    elif not ( \
                options.list or \
                options.install or \
                options.configure or \
                options.badges or \
                options.enable or \
                options.disable or \
                options.clean or \
                options.run \
            ):
        result = Entrypoint.Result.CRITICAL

    # Header
    print(' ')
    Platform.flush()

    # Tool identifier
    if result != Entrypoint.Result.CRITICAL:
        print(f'{Colors.BOLD} {Bundle.NAME}'
              f'{Colors.YELLOW_LIGHT} ({Version.get()})'
              f'{Colors.RESET}')
        Platform.flush()

    # Engine validation
    if result != Entrypoint.Result.CRITICAL and not settings.has('engines', 'pre_commit'):
        print(' ')
        print(
            f'  {Colors.YELLOW}{Colors.ARROW} WARNING: '
            f'{Colors.RED}Default engine not configured: '
            f'{Colors.BOLD}Use \''
            f'{Colors.CYAN}{Bundle.NAME} --set-engine [{PreCommit.ENGINE}, {Prek.ENGINE}]'
            f'{Colors.BOLD}\' '
            f'{Colors.GREEN}({Bundle.REPOSITORY}/-/issues/12)'
            f'{Colors.RESET}')
        Platform.flush()
        if Platform.IS_TTY_STDIN:
            sleep(3)

    # CLI entrypoint
    if result != Entrypoint.Result.CRITICAL:
        result = Entrypoint.cli(options)

    # CLI helper
    else:
        parser.print_help()

    # Footer
    print(' ')
    Platform.flush()

    # Check for daily updates
    if updates.enabled and updates.daily:
        updates.check()

    # Result
    if result in [
            Entrypoint.Result.SUCCESS,
            Entrypoint.Result.FINALIZE,
    ]:
        sys_exit(0)
    else:
        sys_exit(1)

# Entrypoint
if __name__ == '__main__': # pragma: no cover
    main()
