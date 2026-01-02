#!/usr/bin/env python3

# Standard libraries
from shutil import copyfile
from typing import List

# Modules libraries
from setuptools import find_packages, setup

# Assets importation
for asset in [
        '.cz.yaml',
        'templates/commits.yml',
]:

    # Import file to assets
    copyfile(asset, f'src/assets/{asset.rsplit("/", maxsplit=1)[-1]}')

# Requirements
requirements: List[str] = []
with open('requirements/runtime.txt', encoding='utf8', mode='r') as f:
    requirements = [line for line in f.read().splitlines() if not line.startswith('#')]

# Long description
long_description: str = '' # pylint: disable=invalid-name
with open('README.md', encoding='utf8', mode='r') as f:
    long_description = f.read()

# Project configurations, pylint: disable=line-too-long
PROJECT_AUTHOR = 'Adrian DC'
PROJECT_DESCRIPTION = 'Git hooks manager intended for developers using pre-commit, prek and commitizen'
PROJECT_EMAIL = 'radian.dc@gmail.com'
PROJECT_KEYWORDS = 'git pre-commit hooks prek commitizen'
PROJECT_LICENSE = 'Apache License 2.0'
PROJECT_MODULE = 'pre_commit_crocodile'
PROJECT_NAME = 'pre-commit-crocodile'
PROJECT_NAMESPACE = 'RadianDevCore/tools'
PROJECT_PACKAGE = 'pre-commit-crocodile'
PROJECT_SCRIPTS = [
    'check-commitizen-branch = pre_commit_crocodile.hooks.check_commitizen_branch:main',
    'check-yaml-ruamel-pure = pre_commit_crocodile.hooks.check_yaml_ruamel_pure:main',
    'pre-commit-crocodile = pre_commit_crocodile.cli.main:main',
    'prepare-commit-message = pre_commit_crocodile.hooks.prepare_commit_message:main'
]
PROJECT_URL = f'https://gitlab.com/{PROJECT_NAMESPACE}/{PROJECT_NAME}'

# Setup configurations
setup(
    name=PROJECT_PACKAGE,
    use_scm_version=True,
    author=PROJECT_AUTHOR,
    author_email=PROJECT_EMAIL,
    license=PROJECT_LICENSE,
    description=PROJECT_DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/markdown',
    url=PROJECT_URL,
    project_urls={
        'Bug Reports': f'{PROJECT_URL}/-/issues',
        'Changelog': f'{PROJECT_URL}/blob/main/CHANGELOG.md',
        'Documentation': f'{PROJECT_URL}#{PROJECT_NAME}',
        'Source': f'{PROJECT_URL}',
        'Statistics': f'https://pypistats.org/packages/{PROJECT_PACKAGE}'
    },
    packages=[
        PROJECT_MODULE,
    ] + [
        f'{PROJECT_MODULE}.{module}' for module in find_packages(
            where='src',
            exclude=['tests'],
        )
    ],
    package_data={
        f'{PROJECT_MODULE}.assets': [
            '.*',
            '*',
        ],
    },
    package_dir={
        PROJECT_MODULE: 'src',
    },
    setup_requires=['setuptools_scm'],
    install_requires=requirements,
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Topic :: Software Development',
        'Topic :: Utilities',
    ],
    keywords=PROJECT_KEYWORDS,
    python_requires=','.join([
        '>=3',
        '!=3.0.*',
        '!=3.1.*',
        '!=3.2.*',
        '!=3.3.*',
        '!=3.4.*',
        '!=3.5.*',
        '!=3.6.*',
        '!=3.7.*',
        '!=3.8.*',
    ]),
    entry_points={
        'console_scripts': PROJECT_SCRIPTS,
    },
)
