#!/usr/bin/env python3

# Bundle class, pylint: disable=too-few-public-methods
class Bundle:

    # Modules
    MODULE: str = 'pre_commit_crocodile'

    # Names
    NAME: str = 'pre-commit-crocodile'

    # Packages
    PACKAGE: str = 'pre-commit-crocodile'

    # Details, pylint: disable=line-too-long
    DESCRIPTION: str = 'Git hooks manager intended for developers using pre-commit, prek and commitizen'

    # Resources
    RESOURCES_ASSETS: str = f'{MODULE}.assets'

    # Sources
    BADGE: str = 'https://img.shields.io/badge/pre--commit--crocodile-enabled-brightgreen?logo=gitlab' # pylint: disable=line-too-long
    DOCUMENTATION: str = 'https://radiandevcore.gitlab.io/tools/pre-commit-crocodile'
    REPOSITORY: str = 'https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile'

    # Releases
    RELEASE_FIRST_TIMESTAMP: int = 1579337311

    # Environment
    ENV_DEBUG_REVISION_SHA: str = 'DEBUG_REVISION_SHA'
    ENV_DEBUG_UPDATES_DAILY: str = 'DEBUG_UPDATES_DAILY'
    ENV_DEBUG_UPDATES_DISABLE: str = 'DEBUG_UPDATES_DISABLE'
    ENV_DEBUG_UPDATES_FAKE: str = 'DEBUG_UPDATES_FAKE'
    ENV_DEBUG_UPDATES_OFFLINE: str = 'DEBUG_UPDATES_OFFLINE'
    ENV_DEBUG_VERSION_FAKE: str = 'DEBUG_VERSION_FAKE'
    ENV_FORCE_COLOR: str = 'FORCE_COLOR'
    ENV_NO_COLOR: str = 'NO_COLOR'

    # Components
    COMPONENTS_PACKAGE_VERSION: str = '[PACKAGE_VERSION]'
    COMPONENTS_REMOTE_COMMITS: str = f'https://gitlab.com/RadianDevCore/tools/pre-commit-crocodile/-/raw/{COMPONENTS_PACKAGE_VERSION}/templates/commits.yml'
    COMPONENTS_SAAS_COMMITS: str = f'gitlab.com/RadianDevCore/tools/pre-commit-crocodile/commits@{COMPONENTS_PACKAGE_VERSION}'
    COMPONENTS_SAAS_DOMAIN: str = 'gitlab.com'
