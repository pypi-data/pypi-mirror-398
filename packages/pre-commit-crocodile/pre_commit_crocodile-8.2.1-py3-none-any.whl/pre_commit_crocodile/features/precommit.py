#!/usr/bin/env python3

# Standard libraries
from pathlib import Path
from shutil import copyfile, move
from typing import Dict, List, Optional

# Components
from ..features.git import Git
from ..package.bundle import Bundle
from ..package.settings import Settings
from ..prints.colors import Colors
from ..system.commands import Commands
from .prek import Prek

# PreCommit class
class PreCommit:

    # Constants
    CONFIGURATION_EOL: str = '\n'
    CONFIGURATION_EXTENSION: str = '.yaml'
    CONFIGURATION_FILE: str = '.pre-commit-config.yaml'
    CONFIGURATION_TEMPLATE: str = '.pre-commit-config.template.yaml'
    ENGINE: str = 'pre-commit'
    HOOK_CHECK_HOOKS_APPLY: str = 'check-hooks-apply'
    HOOK_CHECK_USELESS_EXCLUDES: str = 'check-useless-excludes'
    HOOKS_APPLY_ERROR: str = ' does not apply to this repository'
    HOOKS_EXCLUDE_DELIMITER: str = ' for '
    HOOKS_EXCLUDE_ERROR: str = ' does not match any files'
    REV_TEMPLATE: str = 'PACKAGE_REVISION'

    # Defaults
    DEFAULT_BINARY: str = 'pre-commit'
    DEFAULT_PACKAGES: List[str] = [
        'pre-commit',
    ]
    DEFAULT_TITLE: str = 'pre-commit'

    # Variables
    BINARY: str = ''
    PACKAGES: List[str] = []
    TITLE: str = ''

    # Internals
    __flags_configuration: List[str] = []

    # Configurations
    @staticmethod
    def configure() -> None:

        # Prepare settings
        settings: Settings = Settings(name=Bundle.NAME)

        # Configure pre-commit engine
        if settings.get('engines', 'pre_commit') == PreCommit.ENGINE:
            PreCommit.BINARY = PreCommit.DEFAULT_BINARY
            PreCommit.PACKAGES = PreCommit.DEFAULT_PACKAGES
            PreCommit.TITLE = PreCommit.DEFAULT_TITLE

        # Configure Prek engine
        else:
            PreCommit.BINARY = Prek.DEFAULT_BINARY
            PreCommit.PACKAGES = Prek.DEFAULT_PACKAGES
            PreCommit.TITLE = Prek.DEFAULT_TITLE

    # Autoupdate
    @staticmethod
    def autoupdate(repo: str = '') -> bool:

        # Clean pre-commit
        return Commands.run(PreCommit.BINARY, [
            'autoupdate',
        ] + PreCommit.__flags_configuration + ([
            '--repo',
            repo,
        ] if repo else []))

    # Clean
    @staticmethod
    def clean() -> bool:

        # Clean pre-commit
        return Commands.run(PreCommit.BINARY, [
            'clean',
        ])

    # Configure unused hooks, pylint: disable=too-many-branches,too-many-locals,too-many-statements
    @staticmethod
    def configure_unused_hooks(
        default: bool,
        configuration_file: str = CONFIGURATION_FILE,
        hooks_disable: Optional[List[str]] = None,
    ) -> bool:

        # Variables
        configuration_moved: bool = False
        configuration_tmp: bool = False
        data_lines: List[str]
        hook_id: str = '- id: '
        hook_offset: str
        hook_section: bool
        hooks_element: str = 'hooks:'
        hooks_empty_flag: Dict[int, bool]
        hooks_ending: str
        hooks_index: int
        hooks_line: str
        hooks_unused: List[str] = []

        # Fake pre-commit configuration
        if default and configuration_file != PreCommit.CONFIGURATION_FILE:
            if Path(PreCommit.CONFIGURATION_FILE).exists():
                move(PreCommit.CONFIGURATION_FILE, f'{PreCommit.CONFIGURATION_FILE}.tmp')
                configuration_moved = True
            else:
                configuration_tmp = True
            copyfile(
                configuration_file,
                PreCommit.CONFIGURATION_FILE,
            )

        # Prestage pre-commit configuration
        if not default or configuration_moved or configuration_tmp:
            if Git.is_repository():
                Commands.run(Git.BINARY, [
                    'add',
                    PreCommit.CONFIGURATION_FILE,
                ])

        # Configure pre-commit unused hooks
        print(' ')
        print(f'{Colors.GREEN} ===['
              f'{Colors.YELLOW} Configure sources: '
              f'{Colors.YELLOW_LIGHT}{PreCommit.HOOK_CHECK_HOOKS_APPLY}'
              f'{Colors.GREEN} ]==='
              f'{Colors.RESET}')
        print(' ')
        for line in Commands.output(PreCommit.BINARY, [
                'run',
        ] + PreCommit.__flags_configuration + [
                '--all-files',
                PreCommit.HOOK_CHECK_HOOKS_APPLY,
        ]).splitlines():
            if PreCommit.HOOKS_APPLY_ERROR not in line:
                continue
            hooks_unused += [
                line[0:line.find(PreCommit.HOOKS_APPLY_ERROR)] \
                    .lstrip(' \t')
            ]

        # Cleanup fake pre-commit configuration
        if configuration_moved or configuration_tmp:
            Path(PreCommit.CONFIGURATION_FILE).unlink()

        # Restore pre-commit configurations
        if configuration_moved:
            move(f'{PreCommit.CONFIGURATION_FILE}.tmp', PreCommit.CONFIGURATION_FILE)

        # Reset pre-commit configuration
        if not default or configuration_moved or configuration_tmp:
            if Git.is_repository():
                Commands.run(Git.BINARY, [
                    'reset',
                    'HEAD',
                    PreCommit.CONFIGURATION_FILE,
                ])

        # Show unused hooks
        print(f'detected unused hooks in configuration: {", ".join(hooks_unused) or "-"}')

        # Disable pre-commit specific hooks
        if hooks_disable:
            print(
                f'disabling specific hooks in configuration: {", ".join(hooks_disable) or "-"}'
            )
            hooks_unused += hooks_disable

        # Disable pre-commit unused hooks
        if hooks_unused:

            # Parse pre-commit hooks
            data_lines = []
            hook_section = False
            hooks_empty_flag = {}
            hooks_index = -1
            with open(
                    configuration_file,
                    encoding='utf8',
                    mode='r',
            ) as f:
                for line in f.readlines():
                    line_stripped = line.strip()

                    # Parse lines
                    if not line_stripped:
                        data_lines.append(line)
                        hook_section = False
                    elif line_stripped.startswith(hooks_element):
                        hooks_index = len(data_lines)
                        hooks_empty_flag[hooks_index] = True
                        data_lines.append(line)
                    elif any(
                            line_stripped == f'{hook_id}{hook}' for hook in hooks_unused):
                        data_lines.append(line.replace(hook_id, f'# {hook_id}'))
                        hook_offset = line[0:line.find(hook_id)]
                        hook_section = True
                    elif line_stripped.startswith(hook_id):
                        data_lines.append(line)
                        if hooks_index != -1:
                            hooks_empty_flag[hooks_index] = False
                        hook_section = False
                    elif hook_section:
                        data_lines.append(f'{hook_offset}#   {line.lstrip()}')
                    else:
                        data_lines.append(line)
                        hooks_index = -1

            # Fix empty hooks
            for index, empty in hooks_empty_flag.items():
                if empty:
                    hooks_line = data_lines[index]
                    hooks_ending = hooks_line[len(hooks_line.rstrip('\r\n')):]
                    data_lines[index] = hooks_line.rstrip('\r\n') + ' []' + hooks_ending

            # Write pre-commit hooks
            with open(
                    configuration_file,
                    encoding='utf8',
                    mode='w',
            ) as f:
                f.writelines(data_lines)

        # Result
        return True

    # Configure useless excludes
    @staticmethod
    def configure_useless_excludes(
        default: bool,
        configuration_file: str = CONFIGURATION_FILE,
    ) -> bool:

        # Variables
        configuration_moved: bool = False
        configuration_tmp: bool = False
        data_lines: List[str]
        hook_exclude: str = 'exclude: '
        hook_id: str = '- id: '
        hook_offset: str
        hook_property: bool
        hook_section: bool
        hooks_unused: List[str] = []

        # Fake pre-commit configuration
        if default and configuration_file != PreCommit.CONFIGURATION_FILE:
            if Path(PreCommit.CONFIGURATION_FILE).exists():
                move(PreCommit.CONFIGURATION_FILE, f'{PreCommit.CONFIGURATION_FILE}.tmp')
                configuration_moved = True
            else:
                configuration_tmp = True
            copyfile(
                configuration_file,
                PreCommit.CONFIGURATION_FILE,
            )

        # Prestage pre-commit configuration
        if not default or configuration_moved or configuration_tmp:
            if Git.is_repository():
                Commands.run(Git.BINARY, [
                    'add',
                    PreCommit.CONFIGURATION_FILE,
                ])

        # Configure pre-commit unused hooks
        print(' ')
        print(f'{Colors.GREEN} ===['
              f'{Colors.YELLOW} Configure sources: '
              f'{Colors.YELLOW_LIGHT}{PreCommit.HOOK_CHECK_USELESS_EXCLUDES}'
              f'{Colors.GREEN} ]==='
              f'{Colors.RESET}')
        print(' ')
        for line in Commands.output(PreCommit.BINARY, [
                'run',
        ] + PreCommit.__flags_configuration + [
                '--all-files',
                PreCommit.HOOK_CHECK_USELESS_EXCLUDES,
        ]).splitlines():
            if PreCommit.HOOKS_EXCLUDE_ERROR not in line:
                continue
            hooks_unused += [
                line[line.find(PreCommit.HOOKS_EXCLUDE_DELIMITER) \
                     + len(PreCommit.HOOKS_EXCLUDE_DELIMITER) \
                     :line.find(PreCommit.HOOKS_EXCLUDE_ERROR)] \
                    .strip('`')
            ]

        # Cleanup fake pre-commit configuration
        if configuration_moved or configuration_tmp:
            Path(PreCommit.CONFIGURATION_FILE).unlink()

        # Restore pre-commit configurations
        if configuration_moved:
            move(f'{PreCommit.CONFIGURATION_FILE}.tmp', PreCommit.CONFIGURATION_FILE)

        # Reset pre-commit configuration
        if not default or configuration_moved or configuration_tmp:
            if Git.is_repository():
                Commands.run(Git.BINARY, [
                    'reset',
                    'HEAD',
                    PreCommit.CONFIGURATION_FILE,
                ])

        # Show unused hooks
        print(f'detected unused hooks in configuration: {", ".join(hooks_unused) or "-"}')

        # Disable pre-commit unused hooks
        if hooks_unused:

            # Parse pre-commit hooks
            data_lines = []
            hook_property = False
            hook_section = False
            with open(
                    configuration_file,
                    encoding='utf8',
                    mode='r',
            ) as f:
                for line in f.readlines():
                    line_stripped = line.strip()

                    # Parse lines
                    if not line_stripped:
                        data_lines.append(line)
                        hook_property = False
                        hook_section = False
                    elif any(
                            line_stripped == f'{hook_id}{hook}' for hook in hooks_unused):
                        data_lines.append(line)
                        hook_offset = line[0:line.find(hook_id)]
                        hook_property = False
                        hook_section = True
                    elif line_stripped.startswith(hook_id):
                        data_lines.append(line)
                        hook_property = False
                        hook_section = False
                    elif hook_section and line_stripped.startswith(hook_exclude):
                        data_lines.append(line.replace(hook_exclude, f'# {hook_exclude}'))
                        hook_property = True
                    elif hook_property and line.startswith(hook_offset + '  '):
                        data_lines.append(
                            f'{hook_offset}  # {line[len(hook_offset) + 2:]}')
                    else:
                        data_lines.append(line)
                        hook_property = False

            # Write pre-commit hooks
            with open(
                    configuration_file,
                    encoding='utf8',
                    mode='w',
            ) as f:
                f.writelines(data_lines)

        # Result
        return True

    # Dependencies
    @staticmethod
    def dependencies() -> bool:

        # Variables
        result: bool = True

        # Uninstall existing pre-commit, pylint: disable=duplicate-code
        if Commands.exists(PreCommit.BINARY):
            for package in PreCommit.PACKAGES:
                Commands.pip([
                    'uninstall',
                    package,
                ])
                print(' ')

        # Install pre-commit
        for package in PreCommit.PACKAGES:

            # Check package installation
            if not Commands.pip([
                    'install',
                    package,
            ]):
                result = False

            # Isolate package installation
            if package != PreCommit.PACKAGES[-1]:
                print(' ')

        # Result
        return result

    # Exists
    @staticmethod
    def exists() -> bool:

        # Check if binary exists
        return Commands.exists(PreCommit.BINARY)

    # Install
    @staticmethod
    def install() -> bool:

        # Clean pre-commit
        return Commands.run(PreCommit.BINARY, [
            'install',
        ] + PreCommit.__flags_configuration + [
            '--allow-missing-config',
        ])

    # Run
    @staticmethod
    def run(all_files: bool, stage: str = '') -> bool:

        # Run commitizen hooks
        return Commands.run(PreCommit.BINARY, [
            'run',
        ] + PreCommit.__flags_configuration + ([
            '--all-files',
        ] if all_files else []) + ([
            '--hook-stage',
            stage,
        ] if stage else []))

    # Set configuration
    @staticmethod
    def set_configuration(file: str) -> None:

        # Set configuration flags
        if file:
            PreCommit.__flags_configuration = [
                '--config',
                file,
            ]
        else:
            PreCommit.__flags_configuration = []

    # Stages
    @staticmethod
    def stages() -> List[str]:

        # Variables
        hooks_stages: List[str] = []

        # Validate pre-commit
        if not PreCommit.exists():
            return hooks_stages # pragma: no cover

        # Get pre-commit run help
        for line in Commands.output(PreCommit.BINARY, [
                'run',
                '--help',
        ]).splitlines():

            # Parse hooks stages
            if ' --hook-stage' in line:
                hooks_stages = line[line.index('{') + 1:line.index('}')].split(',')
                break

        # Result
        return hooks_stages

    # Uninstall
    @staticmethod
    def uninstall() -> bool:

        # Clean pre-commit
        return Commands.run(PreCommit.BINARY, [
            'uninstall',
        ] + PreCommit.__flags_configuration)
