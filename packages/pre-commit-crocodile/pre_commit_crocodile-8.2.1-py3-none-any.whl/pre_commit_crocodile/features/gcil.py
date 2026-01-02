#!/usr/bin/env python3

# Standard libraries
from pathlib import Path
from re import search
from typing import List

# Components
from ..features.git import Git
from ..features.precommit import PreCommit
from ..prints.colors import Colors
from ..system.commands import Commands
from ..system.platform import Platform

# Gcil class
class Gcil:

    # Constants
    BADGE_IMAGE: str = 'https://img.shields.io/badge/gcil-enabled-brightgreen?logo=gitlab'
    BADGE_URL: str = 'https://radiandevcore.gitlab.io/tools/gcil'
    BADGE_TEXT: str = 'gcil'
    BINARY: str = 'gcil'
    EOL: str = '\n'
    FILE: str = '.gitlab-ci.yml'
    HOOK_DESCRIPTION: str = 'Automatically run GitLab CI job with gcil'
    HOOK_ID: str = 'run-gcil-push'
    HOOK_NAME: str = 'Run GitLab CI job with gcil'
    HOOKS_LABEL: str = 'gcil'
    HOOKS_URL: str = 'https://gitlab.com/RadianDevCore/tools/gcil'
    HOOKS_VERSION_MINIMAL: str = '13.0.1'
    MARKER_NODE: str = '.local:'
    MARKER_VARIABLE: str = 'CI_LOCAL'

    # Jobs
    JOBS_WHITELIST: List[str] = [
        r'codestyle[:]?.*',
        r'lint[:]?.*',
        r'typings[:]?.*',
    ]

    # Configure unused hooks, pylint: disable=too-many-branches,too-many-statements
    @staticmethod
    def configure_hooks(
        configuration_file: str,
        autoupdate: bool,
    ) -> bool:

        # Validate gcil support
        if not Gcil.exists() or not Gcil.installed():
            return False

        # Validate pre-commit support
        if not Path(configuration_file).exists():
            return False # pragma: no cover

        # Configure pre-commit unused hooks
        print(' ')
        print(f'{Colors.GREEN} ===['
              f'{Colors.YELLOW} Configure sources: '
              f'{Colors.YELLOW_LIGHT}{Gcil.HOOK_ID}'
              f'{Colors.GREEN} ]==='
              f'{Colors.RESET}')
        print(' ')

        # Detect supported jobs
        jobs_list: List[str] = Gcil.jobs_list()
        jobs_supported: List[str] = []
        for job in jobs_list:
            if any(search(fr'^{whitelist}$', job) for whitelist in Gcil.JOBS_WHITELIST):
                jobs_supported += [job]

        # Show supported jobs hooks
        print(
            f'detected supported jobs hooks in configuration: {", ".join(jobs_supported) or "-"}'
        )
        Platform.flush()

        # Append hooks configuration
        if jobs_supported:
            with open(
                    configuration_file,
                    encoding='utf8',
                    mode='a',
            ) as file:

                # Inject repository header
                file.write(
                    PreCommit.CONFIGURATION_EOL.join([
                        '',
                        f'  # Repository: {Gcil.HOOKS_LABEL}',
                        f'  - repo: {Gcil.HOOKS_URL}',
                        f'    rev: {Gcil.HOOKS_VERSION_MINIMAL}',
                        '    hooks:',
                        '',
                    ]))

                # Inject repository hooks
                for job in jobs_supported:
                    file.write(
                        PreCommit.CONFIGURATION_EOL.join([
                            f'      - id: {Gcil.HOOK_ID}',
                            f'        name: {Gcil.HOOK_NAME} ({job})',
                            f'        description: {Gcil.HOOK_DESCRIPTION} ({job})',
                            '        args:',
                            f"          - '{job}'",
                            '',
                        ]))

            # Autoupdate repository
            if autoupdate and Git.is_repository():
                print(f'updating {Gcil.HOOKS_LABEL} repository with pre-commit: ', end='')
                Platform.flush()
                PreCommit.configure()
                PreCommit.autoupdate(Gcil.HOOKS_URL)
                Platform.flush()

        # Result
        return True

    # Configured
    @staticmethod
    def configured() -> bool:

        # Ignore missing file
        if not Gcil.exists():
            return False

        # Detect gcil configurations
        return Commands.grep(
            Path(Gcil.FILE),
            Gcil.MARKER_NODE,
        ) or Commands.grep(
            Path(Gcil.FILE),
            Gcil.MARKER_VARIABLE,
        )

    # Jobs list
    @staticmethod
    def jobs_list() -> List[str]:

        # Validate gcil support
        if not Gcil.exists() or not Gcil.installed():
            return []

        # Dump jobs configuration
        gcil_dump: str = Commands.output(Gcil.BINARY, [
            '--dump',
        ])
        if not gcil_dump or gcil_dump == '{}':
            return []

        # Extract job names
        jobs: List[str] = []
        for line in [
                line for line in gcil_dump.splitlines()
                if line.strip() and not line.startswith(' ')
        ]:
            job: str = line.strip().rstrip(':')
            if not job.startswith('.'):
                jobs += [job]

        # Result
        return jobs

    # Exists
    @staticmethod
    def exists() -> bool:

        # Check if configuration exists
        return Path(Gcil.FILE).exists()

    # Installed
    @staticmethod
    def installed() -> bool:

        # Check installed gcil
        return Commands.exists(Gcil.BINARY)
