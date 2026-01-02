#!/usr/bin/env python3

# Standard libraries
from argparse import Namespace
from enum import Enum
from importlib.resources import files as resources_files
from pathlib import Path
from tempfile import _TemporaryFileWrapper, NamedTemporaryFile
from time import sleep
from typing import List, Union

# Components
from ..features.argcomplete import Argcomplete
from ..features.commitizen import Commitizen
from ..features.gcil import Gcil
from ..features.git import Git
from ..features.precommit import PreCommit
from ..features.radiandevcore import RadianDevCore
from ..features.readme import Readme
from ..features.templates import Templates
from ..package.bundle import Bundle
from ..package.version import Version
from ..prints.colors import Colors
from ..system.commands import Commands
from ..system.platform import Platform

# Entrypoint class, pylint: disable=too-few-public-methods,too-many-statements
class Entrypoint:

    # Enumerations
    Result = Enum('Result', [
        'SUCCESS',
        'FINALIZE',
        'ERROR',
        'CRITICAL',
    ])

    # TempFile type
    TempFile = Union[_TemporaryFileWrapper] # type: ignore[type-arg]

    # CLI, pylint: disable=too-many-boolean-expressions,too-many-branches,too-many-locals
    @staticmethod
    def cli(options: Namespace, ) -> Result:

        # Variables
        asset: str
        command_add: List[str]
        command_add_string: str
        command_commit: List[str]
        command_commit_string: str
        configurations_existed: bool = False
        configurations_files: List[str] = []
        data: str
        include_components: bool = False
        include_prefix: str
        include_remotes: bool = False
        include_sources: bool = False
        include_value: str
        local_ci_data: str
        local_template: str

        # Configure pre-commit
        PreCommit.configure()

        # List hooks
        if options.list:

            # Detect hooks directory
            hooks_dir = Git.hooks_dir()

            # List hooks directory
            if Path(hooks_dir).exists():

                # Detect hooks files
                hooks_files = Git.hooks_files()

                # List hooks files
                if hooks_files:
                    print(' ')
                    print(f'{Colors.GREEN} ===['
                          f'{Colors.YELLOW} List hooks: '
                          f'{Colors.YELLOW_LIGHT}Hooks installed in '
                          f'{Colors.CYAN}"{hooks_dir}"'
                          f'{Colors.GREEN} ]==='
                          f'{Colors.RESET}')
                    print(' ')
                    for hook in hooks_files:
                        print(f'{Colors.BOLD}   - Hook: {Colors.RESET}{hook}')
                    print(' ')
                    Platform.flush()

                # Missing hooks files
                else:
                    print(' ')
                    print(f'{Colors.GREEN} ===['
                          f'{Colors.YELLOW} List hooks: '
                          f'{Colors.YELLOW_LIGHT}No hooks installed in '
                          f'{Colors.CYAN}"{hooks_dir}"'
                          f'{Colors.GREEN} ]==='
                          f'{Colors.RESET}')
                    print(' ')
                    Platform.flush()

            # Missing hooks directory
            else:
                print(' ')
                print(f'{Colors.GREEN} ===['
                      f'{Colors.YELLOW} List hooks: '
                      f'{Colors.YELLOW_LIGHT}No hooks directory found in '
                      f'{Colors.CYAN}"{hooks_dir}"'
                      f'{Colors.GREEN} ]==='
                      f'{Colors.RESET}')
                print(' ')
                Platform.flush()

        # Prepare dependencies
        if options.install or options.configure or options.enable or options.autoupdate \
                or options.clean or options.run:

            # Install pre-commit dependency
            if options.install or not PreCommit.exists():
                print(' ')
                print(f'{Colors.GREEN} ===['
                      f'{Colors.YELLOW} Install dependencies: '
                      f'{Colors.YELLOW_LIGHT}{PreCommit.TITLE}'
                      f'{Colors.GREEN} ]==='
                      f'{Colors.RESET}')
                print(' ')
                Platform.flush()
                PreCommit.dependencies()

            # Install commitizen dependency
            if options.install or not Commitizen.exists() or not Commitizen.compatible():
                print(' ')
                print(f'{Colors.GREEN} ===['
                      f'{Colors.YELLOW} Install dependencies: '
                      f'{Colors.YELLOW_LIGHT}{Commitizen.TITLE}'
                      f'{Colors.GREEN} ]==='
                      f'{Colors.RESET}')
                print(' ')
                Platform.flush()
                Commitizen.dependencies()

            # Install argcomplete completion
            if options.install and not Argcomplete.configured():
                print(' ')
                print(f'{Colors.GREEN} ===['
                      f'{Colors.YELLOW} Install bash completion: '
                      f'{Colors.YELLOW_LIGHT}argcomplete'
                      f'{Colors.GREEN} ]==='
                      f'{Colors.RESET}')
                print(' ')
                Platform.flush()
                Argcomplete.configure()
                if Platform.IS_TTY_STDIN:
                    sleep(2)

            # Install commitizen completion
            if options.install and not Commitizen.configured():
                print(' ')
                print(f'{Colors.GREEN} ===['
                      f'{Colors.YELLOW} Install dependencies: '
                      f'{Colors.YELLOW_LIGHT}commitizen completion'
                      f'{Colors.GREEN} ]==='
                      f'{Colors.RESET}')
                print(' ')
                Platform.flush()
                commitizen_file: str = Commitizen.configure()
                print(f'commitizen completion enabled in: {commitizen_file}')
                if Platform.IS_TTY_STDIN:
                    sleep(1)

        # Bind specific configurations
        if options.config:
            Commitizen.set_configuration(options.config + Platform.PATH_SEPARATOR +
                                         Commitizen.CONFIGURATION_FILE)
            PreCommit.set_configuration(options.config + Platform.PATH_SEPARATOR +
                                        PreCommit.CONFIGURATION_FILE)

        # Bind default configurations
        elif options.default:

            # Bind configurations files, pylint: disable=consider-using-with
            commitizen_configuration: Entrypoint.TempFile = NamedTemporaryFile(
                delete_on_close=True,
                suffix=Commitizen.CONFIGURATION_EXTENSION,
            )
            precommit_configuration: Entrypoint.TempFile = NamedTemporaryFile(
                delete_on_close=True,
                suffix=PreCommit.CONFIGURATION_EXTENSION,
            )

            # Bind configurations flags
            Commitizen.set_configuration(commitizen_configuration.name)
            PreCommit.set_configuration(precommit_configuration.name)

            # Default pre-commit configuration
            with open(
                    precommit_configuration.name,
                    encoding='utf8',
                    mode='w+t',
            ) as file:

                # Acquire pre-commit configuration
                file.write(resources_files(Bundle.RESOURCES_ASSETS) \
                    .joinpath(PreCommit.CONFIGURATION_TEMPLATE) \
                    .read_text(encoding='utf8') \
                    .replace(PreCommit.REV_TEMPLATE, Version.revision()))
                file.flush()

            # Default commitizen configuration
            with open(
                    commitizen_configuration.name,
                    encoding='utf8',
                    mode='w+t',
            ) as file:

                # Acquire commitizen configuration
                file.write(resources_files(Bundle.RESOURCES_ASSETS) \
                    .joinpath(Commitizen.CONFIGURATION_FILE) \
                    .read_text(encoding='utf8') \
                    .replace(PreCommit.REV_TEMPLATE, Version.revision()))
                file.flush()

            # Autoupdate pre-commit hooks
            if not options.offline and Git.is_repository():
                PreCommit.autoupdate()

            # Configure useless excludes
            PreCommit.configure_useless_excludes(
                default=options.default,
                configuration_file=precommit_configuration.name,
            )

            # Configure unused hooks
            PreCommit.configure_unused_hooks(
                default=options.default,
                configuration_file=precommit_configuration.name,
                hooks_disable=[
                    PreCommit.HOOK_CHECK_HOOKS_APPLY,
                    PreCommit.HOOK_CHECK_USELESS_EXCLUDES,
                ],
            )

            # Configre gcil hooks
            Gcil.configure_hooks(
                configuration_file=precommit_configuration.name,
                autoupdate=not options.offline,
            )

            # Autoupdate pre-commit hooks
            if not options.offline and Git.is_repository():
                PreCommit.autoupdate()

        # Configure sources
        if options.configure:

            # Install sources configurations
            print(' ')
            print(f'{Colors.GREEN} ===['
                  f'{Colors.YELLOW} Configure sources: '
                  f'{Colors.YELLOW_LIGHT}{Bundle.NAME}'
                  f'{Colors.GREEN} ]==='
                  f'{Colors.RESET}')
            print(' ')

            # Export pre-commit assets file
            if Path(PreCommit.CONFIGURATION_FILE).exists():
                configurations_existed = True
            print(
                f'exporting configuration in {PreCommit.CONFIGURATION_FILE} configuration'
            )
            configurations_files += [PreCommit.CONFIGURATION_FILE]
            data = resources_files(Bundle.RESOURCES_ASSETS) \
                .joinpath(PreCommit.CONFIGURATION_TEMPLATE) \
                .read_text(encoding='utf8') \
                .replace(PreCommit.REV_TEMPLATE, Version.revision())
            with open(
                    PreCommit.CONFIGURATION_FILE,
                    encoding='utf8',
                    mode='w',
            ) as f:
                f.write(data)
                if Platform.IS_TTY_STDIN:
                    sleep(0.5)

            # Export Commitizen assets file
            if Path(Commitizen.CONFIGURATION_FILE).exists():
                configurations_existed = True
            print(
                f'exporting configuration in {Commitizen.CONFIGURATION_FILE} configuration'
            )
            configurations_files += [Commitizen.CONFIGURATION_FILE]
            data = resources_files(Bundle.RESOURCES_ASSETS) \
                .joinpath(Commitizen.CONFIGURATION_FILE) \
                .read_text(encoding='utf8') \
                .replace(PreCommit.REV_TEMPLATE, Version.revision())
            with open(
                    Commitizen.CONFIGURATION_FILE,
                    encoding='utf8',
                    mode='w',
            ) as f:
                f.write(data)
                if Platform.IS_TTY_STDIN:
                    sleep(0.5)

            # Autoupdate pre-commit hooks
            if not options.offline and Git.is_repository():
                PreCommit.autoupdate()

            # Configure useless excludes
            PreCommit.configure_useless_excludes(default=options.default)

            # Configure unused hooks
            PreCommit.configure_unused_hooks(
                default=options.default,
                hooks_disable=[
                    PreCommit.HOOK_CHECK_HOOKS_APPLY,
                    PreCommit.HOOK_CHECK_USELESS_EXCLUDES,
                ],
            )

            # Configre gcil hooks
            Gcil.configure_hooks(
                configuration_file=PreCommit.CONFIGURATION_FILE,
                autoupdate=not options.offline,
            )

            # Autoupdate pre-commit hooks
            if not options.offline and Git.is_repository():
                PreCommit.autoupdate()

        # Export components templates
        if options.configure and Gcil.exists():

            # Detect if components in sources
            if options.components:
                include_components = True
            elif options.remotes:
                include_remotes = True
            elif options.no_components:
                include_sources = True
            elif any(Bundle.COMPONENTS_SAAS_DOMAIN in url for url in Git.urls()):
                include_components = True
            else:
                include_remotes = True

            # Bind components version
            if include_components:

                # Install components configurations
                print(' ')
                print(f'{Colors.GREEN} ===['
                      f'{Colors.YELLOW} Configure sources: '
                      f'{Colors.YELLOW_LIGHT}components'
                      f'{Colors.GREEN} ]==='
                      f'{Colors.RESET}')
                print(' ')

                # Inject component in .gitlab-ci.yml
                include_value = Bundle.COMPONENTS_SAAS_COMMITS.replace(
                    Bundle.COMPONENTS_PACKAGE_VERSION,
                    Version.revision(),
                )
                include_prefix = Bundle.COMPONENTS_SAAS_COMMITS.split(
                    Bundle.COMPONENTS_PACKAGE_VERSION,
                    1,
                )[0]
                local_ci_data = ''
                with open(Gcil.FILE, encoding='utf8') as local_ci_file:
                    local_ci_data = local_ci_file.read()
                if include_value not in local_ci_data:
                    configurations_files += [Gcil.FILE]
                    with open(
                            Gcil.FILE,
                            encoding='utf8',
                            mode='w',
                    ) as f:
                        if f'component: {include_prefix}' not in local_ci_data:
                            f.write(
                                Gcil.EOL.join([
                                    'include:',
                                    f'  - component: {include_value}',
                                    '    inputs:',
                                    '      stage: test',
                                    '      name: commits',
                                    '',
                                    '',
                                ]))
                        else:
                            local_ci_data = Gcil.EOL.join([
                                f'{line[0:line.find(include_prefix)]}{include_value}' #
                                if f'component: {include_prefix}' in line #
                                else line #
                                for line in local_ci_data.splitlines()
                            ]) + Gcil.EOL
                        if 'stages:' not in local_ci_data.splitlines():
                            f.write(Gcil.EOL.join([
                                'stages:',
                                '  - test',
                                '',
                            ]))
                        f.write(local_ci_data)

            # Bind remotes version
            elif include_remotes:

                # Install remotes configurations
                print(' ')
                print(f'{Colors.GREEN} ===['
                      f'{Colors.YELLOW} Configure sources: '
                      f'{Colors.YELLOW_LIGHT}remotes'
                      f'{Colors.GREEN} ]==='
                      f'{Colors.RESET}')
                print(' ')

                # Inject remote in .gitlab-ci.yml
                include_value = Bundle.COMPONENTS_REMOTE_COMMITS.replace(
                    Bundle.COMPONENTS_PACKAGE_VERSION,
                    Version.revision(),
                )
                include_prefix = Bundle.COMPONENTS_REMOTE_COMMITS.split(
                    Bundle.COMPONENTS_PACKAGE_VERSION,
                    1,
                )[0]
                local_ci_data = ''
                with open(Gcil.FILE, encoding='utf8') as local_ci_file:
                    local_ci_data = local_ci_file.read()
                if include_value not in local_ci_data:
                    configurations_files += [Gcil.FILE]
                    with open(
                            Gcil.FILE,
                            encoding='utf8',
                            mode='w',
                    ) as f:
                        if f'remote: {include_prefix}' not in local_ci_data:
                            f.write(
                                Gcil.EOL.join([
                                    'include:',
                                    f'  - remote: {include_value}',
                                    '    inputs:',
                                    '      stage: test',
                                    '      name: commits',
                                    '',
                                    '',
                                ]))
                        else:
                            local_ci_data = Gcil.EOL.join([
                                f'{line[0:line.find(include_prefix)]}{include_value}' #
                                if f'remote: {include_prefix}' in line #
                                else line #
                                for line in local_ci_data.splitlines()
                            ]) + Gcil.EOL
                        if 'stages:' not in local_ci_data.splitlines():
                            f.write(Gcil.EOL.join([
                                'stages:',
                                '  - test',
                                '',
                            ]))
                        f.write(local_ci_data)

            # Export components sources
            elif include_sources:

                # Install templates configurations
                print(' ')
                print(f'{Colors.GREEN} ===['
                      f'{Colors.YELLOW} Configure sources: '
                      f'{Colors.YELLOW_LIGHT}templates'
                      f'{Colors.GREEN} ]==='
                      f'{Colors.RESET}')
                print(' ')

                # Export templates files
                for asset in [
                        Templates.COMMITS_FILE,
                ]:

                    # Export template file
                    print(f'exporting components in {asset} local template')
                    Path(Templates.GITLAB_CI_LOCAL_FOLDER).mkdir(
                        parents=False,
                        exist_ok=True,
                    )
                    local_template = f'{Templates.GITLAB_CI_LOCAL_FOLDER}/{asset}'
                    configurations_files += [local_template]
                    data = resources_files(Bundle.RESOURCES_ASSETS) \
                        .joinpath(asset) \
                        .read_text(encoding='utf8')
                    with open(
                            local_template,
                            encoding='utf8',
                            mode='w',
                    ) as f:
                        f.write(data)
                        if Platform.IS_TTY_STDIN:
                            sleep(0.5)

                    # Inject template in .gitlab-ci.yml
                    local_ci_data = ''
                    with open(Gcil.FILE, encoding='utf8') as local_ci_file:
                        local_ci_data = local_ci_file.read()
                    if asset not in local_ci_data:
                        configurations_files += [Gcil.FILE]
                        with open(
                                Gcil.FILE,
                                encoding='utf8',
                                mode='w',
                        ) as f:
                            f.write(
                                Gcil.EOL.join([
                                    'include:',
                                    f'  - local: \'/{local_template}\'',
                                    '    inputs:',
                                    '      stage: test',
                                    f'      name: {asset.rsplit("/", 1)[-1].split(".", 1)[0]}',
                                    '',
                                    '',
                                ]))
                            if 'stages:' not in local_ci_data.split():
                                f.write(Gcil.EOL.join([
                                    'stages:',
                                    '  - test',
                                    '',
                                ]))
                            f.write(local_ci_data)

                            # Register configured file
                            configurations_files += [Gcil.FILE]

            # Enable pre-commit hooks
            if not options.enable:
                options.enable = True

        # Configure sources or badges
        if options.configure or options.badges:

            # Inject badge to README
            if Readme.exists() or options.badges:

                # Configure README sources
                print(' ')
                print(f'{Colors.GREEN} ===['
                      f'{Colors.YELLOW} Configure sources: '
                      f'{Colors.YELLOW_LIGHT}{Readme.FILE}'
                      f'{Colors.GREEN} ]==='
                      f'{Colors.RESET}')
                print(' ')

                # Acquire README contents
                readme_lines: List[str] = Readme.read()

                # Prepare empty README
                if not readme_lines:
                    readme_lines = [f'# {Path.cwd().name}{Readme.EOL}']

                # Prepare README without empty lines
                if all(line.strip() for line in readme_lines):
                    if not readme_lines[-1].endswith(Readme.EOL):
                        readme_lines[-1] = f'{readme_lines[-1]}{Readme.EOL}'
                    readme_lines += [f'{Readme.EOL}']
                    readme_lines += ['']

                # Check badges in READE
                bundle_found: bool = any(
                    line.startswith(f'[![{Bundle.NAME}]') for line in readme_lines)
                guidelines_found: bool = any(
                    line.startswith(f'[![{RadianDevCore.Guidelines.BADGE_TEXT}]')
                    for line in readme_lines)
                gcil_found: bool = any(
                    line.startswith(f'[![{Gcil.BADGE_TEXT}]') for line in readme_lines)

                # Detect gcil usage
                gcil_exists: bool = Gcil.exists()
                gcil_configured: bool = Gcil.configured()
                gcil_installed: bool = Gcil.installed()
                gcil_needed: bool = gcil_exists and (gcil_configured or gcil_installed)

                # Validate badge in README
                if not bundle_found \
                        or not guidelines_found \
                        or (not gcil_found and gcil_needed):

                    # Inject badge lines
                    print(f'injecting badge in {Readme.FILE} documentation')
                    for i, line in enumerate(readme_lines):

                        # Ignore non-empty lines
                        if line.strip():
                            continue

                        # Handle empty line
                        if not line:
                            line = Readme.EOL

                        # Inject badges separator
                        readme_lines.insert(
                            i + 1,
                            line,
                        )

                        # Inject RadianDevCore guidelines badge
                        if not guidelines_found:
                            readme_lines.insert(
                                i + 1,
                                f'[![{RadianDevCore.Guidelines.BADGE_TEXT}]'
                                f'({RadianDevCore.Guidelines.BADGE_IMAGE})]'
                                f'({RadianDevCore.Guidelines.BADGE_URL}){line}',
                            )

                        # Inject pre-commit-crocodile badge
                        if not bundle_found:
                            readme_lines.insert(
                                i + 1,
                                f'[![{Bundle.NAME}]'
                                f'({Bundle.BADGE})]'
                                f'({Bundle.DOCUMENTATION}){line}',
                            )

                        # Inject gcil badge
                        if not gcil_found and gcil_needed:
                            readme_lines.insert(
                                i + 1,
                                f'[![{Gcil.BADGE_TEXT}]'
                                f'({Gcil.BADGE_IMAGE})]'
                                f'({Gcil.BADGE_URL}){line}',
                            )

                        # Preserve README documentation
                        break

                    # Export README contents
                    Readme.write(readme_lines)

                    # Register configured file
                    configurations_files += [Readme.FILE]

                # Keep existing README
                else:
                    print(f'keeping original {Readme.FILE} documentation')

            # Show sources status
            if Git.is_repository():
                print(' ')
                print(f'{Colors.GREEN} ===['
                      f'{Colors.YELLOW} Sources status: '
                      f'{Colors.YELLOW_LIGHT}git status'
                      f'{Colors.GREEN} ]==='
                      f'{Colors.RESET}')
                print(' ')
                Git.status(untracked=True)

        # Configure sources
        if options.configure \
                and Git.is_repository() \
                and Git.intend(configurations_files) \
                and Git.diff(configurations_files):

            # Show commit hints
            print(' ')
            print(f'{Colors.GREEN} ===['
                  f'{Colors.YELLOW} Update sources: '
                  f'{Colors.YELLOW_LIGHT}git'
                  f'{Colors.GREEN} ]==='
                  f'{Colors.RESET}')
            print(' ')
            command_add = [
                Git.BINARY,
                'add',
                '-v',
            ] + [f'./{asset}' for asset in configurations_files]
            if configurations_existed:
                command_commit = [
                    Git.BINARY,
                    'commit',
                    '-m',
                    f'chore(pre-commit): migrate to \'{Bundle.NAME}\' {Version.get()}',
                    '-s',
                ]
            else:
                command_commit = [
                    Git.BINARY,
                    'commit',
                    '-m',
                    f'chore(pre-commit): import \'{Bundle.NAME}\' {Version.get()}',
                    '-s',
                ]
            command_add_string = ' '.join([
                f'{argument}' if "'" in argument else argument #
                for argument in command_add
            ])
            command_commit_string = ' '.join([
                f'"{argument}"' if "'" in argument else argument
                for argument in command_commit
            ])
            print(f'{Colors.BOLD} - Add configurations: '
                  f'{Colors.CYAN}{command_add_string}'
                  f'{Colors.RESET}')
            print(f'{Colors.BOLD} - Commit changes: '
                  f'{Colors.CYAN}{command_commit_string}'
                  f'{Colors.RESET}')
            Platform.flush()

            # Commit changes automatically
            if options.commit:
                print(' ')
                Commands.run(Git.BINARY, command_add[1:])
                Platform.flush()
                if not Git.staging_empty():
                    print(' ')
                    Commands.run(Git.BINARY, command_commit[1:])
                    Platform.flush()

            # Delay user interactions
            if Platform.IS_TTY_STDIN:
                if options.commit:
                    sleep(1)
                else:
                    sleep(3)

        # Configure badges
        elif options.badges and configurations_files and Git.is_repository():

            # Show commit hints
            print(' ')
            print(f'{Colors.GREEN} ===['
                  f'{Colors.YELLOW} Update sources: '
                  f'{Colors.YELLOW_LIGHT}git'
                  f'{Colors.GREEN} ]==='
                  f'{Colors.RESET}')
            print(' ')
            command_add = [
                Git.BINARY,
                'add',
                '-v',
            ] + [f'./{asset}' for asset in configurations_files]
            command_commit = [
                Git.BINARY,
                'commit',
                '-m',
                'docs(readme): add applicable badges to the documentation',
                '-s',
            ]
            command_add_string = ' '.join([
                f'{argument}' if "'" in argument else argument #
                for argument in command_add
            ])
            command_commit_string = ' '.join([
                f'"{argument}"' if "'" in argument else argument
                for argument in command_commit
            ])
            print(f'{Colors.BOLD} - Add configurations: '
                  f'{Colors.CYAN}{command_add_string}'
                  f'{Colors.RESET}')
            print(f'{Colors.BOLD} - Commit changes: '
                  f'{Colors.CYAN}{command_commit_string}'
                  f'{Colors.RESET}')
            Platform.flush()

            # Commit changes automatically
            if options.commit:
                print(' ')
                Commands.run(Git.BINARY, command_add[1:])
                Platform.flush()
                if not Git.staging_empty():
                    print(' ')
                    Commands.run(Git.BINARY, command_commit[1:])
                    Platform.flush()

            # Delay user interactions
            if Platform.IS_TTY_STDIN:
                if options.commit:
                    sleep(1)
                else:
                    sleep(3)

        # Enable hooks
        if options.enable and Git.is_repository():

            # Detect Git remotes
            git_remotes: List[str] = Git.remotes()

            # Enable Git hooks
            print(' ')
            print(f'{Colors.GREEN} ===['
                  f'{Colors.YELLOW} Enable hooks: '
                  f'{Colors.YELLOW_LIGHT}Git remote'
                  f'{Colors.GREEN} ]==='
                  f'{Colors.RESET}')
            print(' ')
            print(f'detected Git remotes: {", ".join(git_remotes)}')
            Platform.flush()
            for remote in git_remotes:
                print(f'updating git remote for {remote}')
                Git.update_remote_head(remote)

            # Enable pre-commit hooks
            print(' ')
            print(f'{Colors.GREEN} ===['
                  f'{Colors.YELLOW} Enable hooks: '
                  f'{Colors.YELLOW_LIGHT}{PreCommit.TITLE}'
                  f'{Colors.GREEN} ]==='
                  f'{Colors.RESET}')
            print(' ')
            Platform.flush()
            PreCommit.install()

            # Run pre-commit hooks
            if not options.run and Path(PreCommit.CONFIGURATION_FILE).exists():
                options.run = True

        # Disable hooks
        if options.disable:

            # Disable pre-commit hooks
            print(' ')
            print(f'{Colors.GREEN} ===['
                  f'{Colors.YELLOW} Disable hooks: '
                  f'{Colors.YELLOW_LIGHT}{PreCommit.TITLE}'
                  f'{Colors.GREEN} ]==='
                  f'{Colors.RESET}')
            print(' ')
            Platform.flush()
            PreCommit.uninstall()

        # Autoupdate hooks
        if options.autoupdate:

            # Autoupdate pre-commit hooks
            print(' ')
            print(f'{Colors.GREEN} ===['
                  f'{Colors.YELLOW} Autoupdate hooks: '
                  f'{Colors.YELLOW_LIGHT}{PreCommit.TITLE}'
                  f'{Colors.GREEN} ]==='
                  f'{Colors.RESET}')
            print(' ')
            Platform.flush()
            PreCommit.autoupdate()

        # Cleanup hooks
        if options.clean:

            # Disable pre-commit hooks
            print(' ')
            print(f'{Colors.GREEN} ===['
                  f'{Colors.YELLOW} Cleanup hooks: '
                  f'{Colors.YELLOW_LIGHT}{PreCommit.TITLE}'
                  f'{Colors.GREEN} ]==='
                  f'{Colors.RESET}')
            print(' ')
            Platform.flush()
            PreCommit.clean()

        # Run hooks
        if options.run:

            # Run pre-commit hooks
            print(' ')
            print(f'{Colors.GREEN} ===['
                  f'{Colors.YELLOW} Run hooks: '
                  f'{Colors.YELLOW_LIGHT}{PreCommit.TITLE}'
                  f'{Colors.CYAN}{f" (stage: {options.stage})" if options.stage else ""}'
                  f'{Colors.GREEN} ]==='
                  f'{Colors.RESET}')
            print(' ')
            Platform.flush()
            if options.stage == 'list':
                hooks_stages: List[str] = PreCommit.stages()
                print(f'{Colors.BOLD}Supported {PreCommit.TITLE} hooks stages:'
                      f'{Colors.RESET} {", ".join(hooks_stages)}')
            else:
                PreCommit.run(
                    all_files=True,
                    stage=options.stage,
                )

            # Run commitizen hooks
            if Git.is_repository() and Git.commit_exists('HEAD'):
                print(' ')
                print(f'{Colors.GREEN} ===['
                      f'{Colors.YELLOW} Run hooks: '
                      f'{Colors.YELLOW_LIGHT}commitizen'
                      f'{Colors.GREEN} ]==='
                      f'{Colors.RESET}')
                print(' ')
                Platform.flush()
                if Git.commit_exists('HEAD~1'):
                    Commitizen.check('HEAD~1..HEAD')
                else:
                    Commitizen.check('HEAD')

        # Result
        return Entrypoint.Result.SUCCESS
