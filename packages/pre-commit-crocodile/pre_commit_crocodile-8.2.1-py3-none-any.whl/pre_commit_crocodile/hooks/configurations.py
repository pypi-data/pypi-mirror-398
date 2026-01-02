#!/usr/bin/env python3

# Standard libraries
from typing import List, NamedTuple

# Changes regex type
ChangesRegex = str

# Changes parsers class
class ChangesParsers(NamedTuple):
    match: str
    groups: List[int]
    commit_type: str

# Changes evaluator class
class ChangesEvaluator(NamedTuple):
    changes: List[ChangesRegex]
    parsers: List[ChangesParsers]

# Changes types class
class ChangesType(NamedTuple):
    commit_type: str
    changes: List[ChangesRegex]

# Changes matcher class
class ChangesMatcher(NamedTuple):
    commit_scope: str
    types: List[ChangesType]

# Commits changes constants
COMMITS_CHANGES_PATTERN: str = r'^#\s*(new file|modified|deleted|renamed|copied):\s*(.* -> |)(.+)$'
COMMITS_CHANGES_SECTION: str = '# Changes to be committed:'

# Commits comments constants
COMMITS_COMMENTS_PREFIX: str = '#'

# Commits default constants
COMMITS_DEFAULT_BODY: str = '# Issue: #...'
COMMITS_DEFAULT_SCOPE: str = 'scope'
COMMITS_DEFAULT_SUBJECT: str = ''
COMMITS_DEFAULT_TYPE: str = 'type'

# Commits footers constants
COMMITS_FOOTER_SIGNOFF: str = 'Signed-off-by: '

# Commits message constants
COMMITS_MESSAGE_EOL: str = '\n'

# Commitizen constants
COMMITIZEN_CONFIGURATION_FILE: str = '.cz.yaml'

# Regex constants
REGEX_EXT: str = r'[^/.]*'
REGEX_FOLDER: str = r'[^/]+?'
REGEX_STEM: str = r'[^/]+?'
REGEX_STEM_VISIBLE: str = r'[^/]{1}[^/]+?'

# Changes evaluators constants # pylint: disable=line-too-long
CHANGES_EVALUATORS: List[ChangesEvaluator] = [
    # Sources
    ChangesEvaluator(
        changes=[
            r'^sources/|^src/',
        ],
        parsers=[
            ChangesParsers(
                match=
                fr'(({REGEX_FOLDER})/)??(({REGEX_FOLDER})/)?({REGEX_STEM_VISIBLE})\.{REGEX_EXT}$',
                groups=[5, 4, 2],
                commit_type='fix',
            ),
        ],
    ),
    # Documentations
    ChangesEvaluator(
        changes=[
            r'^docs/',
        ],
        parsers=[
            ChangesParsers(
                match=
                fr'(({REGEX_FOLDER})/)??(({REGEX_FOLDER})/)?({REGEX_STEM_VISIBLE})(\.{REGEX_EXT})?$',
                groups=[5, 4, 2],
                commit_type='docs',
            ),
        ],
    ),
    # Containers
    ChangesEvaluator(
        changes=[
            r'^containers/',
        ],
        parsers=[
            ChangesParsers(
                match=
                fr'(({REGEX_FOLDER})/)??(({REGEX_FOLDER})/)?({REGEX_STEM_VISIBLE})(\.{REGEX_EXT})?$',
                groups=[4, 2],
                commit_type='build',
            ),
        ],
    ),
    # Resources
    ChangesEvaluator(
        changes=[
            r'^res/|^resources/',
        ],
        parsers=[
            ChangesParsers(
                match=
                fr'(({REGEX_FOLDER})/)??(({REGEX_FOLDER})/)?({REGEX_STEM_VISIBLE})(\.{REGEX_EXT})?$',
                groups=[4, 2],
                commit_type='docs',
            ),
        ],
    ),
    # Templates
    ChangesEvaluator(
        changes=[
            r'^templates/',
        ],
        parsers=[
            ChangesParsers(
                match=
                fr'(({REGEX_FOLDER})/)??(({REGEX_FOLDER})/)?({REGEX_STEM_VISIBLE})(\.{REGEX_EXT})?$',
                groups=[5, 4, 2],
                commit_type='ci',
            ),
        ],
    ),
    # Tests
    ChangesEvaluator(
        changes=[
            r'^test[s]?/',
        ],
        parsers=[
            ChangesParsers(
                match=
                fr'(({REGEX_FOLDER})/)??(({REGEX_FOLDER})/)?({REGEX_STEM_VISIBLE})(\.{REGEX_EXT})?$',
                groups=[5, 4, 2],
                commit_type='test',
            ),
        ],
    ),
    # Yocto
    ChangesEvaluator(
        changes=[
            fr'conf/(distro|machine)|recipes-{REGEX_STEM}',
        ],
        parsers=[
            ChangesParsers(
                match=fr'conf/(distro|machine)/{REGEX_STEM}.conf$',
                groups=[1],
                commit_type='fix',
            ),
            ChangesParsers(
                match=fr'({REGEX_STEM})/{REGEX_STEM}\.(bb[^/.]*|inc)$',
                groups=[1],
                commit_type='fix',
            ),
            ChangesParsers(
                match=fr'recipes-{REGEX_STEM}/({REGEX_STEM})/.*',
                groups=[1],
                commit_type='fix',
            ),
        ],
    ),
]

# Changes matchers constant
CHANGES_MATCHERS: List[ChangesMatcher] = [
    ChangesMatcher(
        commit_scope='gitlab-ci',
        types=[
            ChangesType(
                commit_type='ci',
                changes=[
                    r'\.gitlab-ci\.yml$',
                    r'\.gitlab-ci\.d$',
                ],
            ),
        ],
    ),
    ChangesMatcher(
        commit_scope='hooks',
        types=[
            ChangesType(
                commit_type='chore',
                changes=[
                    r'^\.hooks',
                ],
            ),
        ],
    ),
    ChangesMatcher(
        commit_scope='gitignore',
        types=[
            ChangesType(
                commit_type='chore',
                changes=[
                    r'\.gitignore$',
                ],
            ),
        ],
    ),
    ChangesMatcher(
        commit_scope='submodules',
        types=[
            ChangesType(
                commit_type='chore',
                changes=[
                    r'\.gitmodules$',
                ],
            ),
        ],
    ),
    ChangesMatcher(
        commit_scope='makefile',
        types=[
            ChangesType(
                commit_type='build',
                changes=[
                    r'Makefile$',
                    r'\.make$',
                ],
            ),
        ],
    ),
    ChangesMatcher(
        commit_scope='dockerfile',
        types=[
            ChangesType(
                commit_type='build',
                changes=[
                    r'Dockerfile$',
                ],
            ),
        ],
    ),
    ChangesMatcher(
        commit_scope='commitizen',
        types=[
            ChangesType(
                commit_type='chore',
                changes=[
                    r'\.cz.*$',
                ],
            ),
        ],
    ),
    ChangesMatcher(
        commit_scope='coveragerc',
        types=[
            ChangesType(
                commit_type='chore',
                changes=[
                    r'\.coveragerc$',
                ],
            ),
        ],
    ),
    ChangesMatcher(
        commit_scope='mkdocs',
        types=[
            ChangesType(
                commit_type='docs',
                changes=[
                    r'^mkdocs\.yml$',
                ],
            ),
        ],
    ),
    ChangesMatcher(
        commit_scope='mypy',
        types=[
            ChangesType(
                commit_type='chore',
                changes=[
                    r'mypy\.ini$',
                ],
            ),
        ],
    ),
    ChangesMatcher(
        commit_scope='pre-commit',
        types=[
            ChangesType(
                commit_type='chore',
                changes=[
                    r'\.pre-commit.*$',
                    r'^pre_commit_hooks/',
                ],
            ),
        ],
    ),
    ChangesMatcher(
        commit_scope='requirements',
        types=[
            ChangesType(
                commit_type='build',
                changes=[
                    r'^requirements/',
                ],
            ),
        ],
    ),
    ChangesMatcher(
        commit_scope='scripts',
        types=[
            ChangesType(
                commit_type='chore',
                changes=[
                    r'scripts/',
                ],
            ),
        ],
    ),
    ChangesMatcher(
        commit_scope='setup',
        types=[
            ChangesType(
                commit_type='chore',
                changes=[
                    r'setup\.py$',
                ],
            ),
        ],
    ),
    ChangesMatcher(
        commit_scope='sonar',
        types=[
            ChangesType(
                commit_type='chore',
                changes=[
                    r'^sonar-project\.properties$',
                ],
            ),
        ],
    ),
    ChangesMatcher(
        commit_scope='tsconfig',
        types=[
            ChangesType(
                commit_type='build',
                changes=[
                    r'tsconfig\.json$',
                ],
            ),
        ],
    ),
    ChangesMatcher(
        commit_scope='vscode',
        types=[
            ChangesType(
                commit_type='chore',
                changes=[
                    r'\.vscode/',
                ],
            ),
        ],
    ),
    ChangesMatcher(
        commit_scope='license',
        types=[
            ChangesType(
                commit_type='docs',
                changes=[
                    r'LICENSE$',
                    r'LICENSE\..*$',
                ],
            ),
        ],
    ),
    ChangesMatcher(
        commit_scope='readme',
        types=[
            ChangesType(
                commit_type='docs',
                changes=[
                    r'README$',
                    r'README\..*$',
                ],
            ),
        ],
    ),
    ChangesMatcher(
        commit_scope='changelog',
        types=[
            ChangesType(
                commit_type='docs',
                changes=[
                    r'CHANGELOG$',
                    r'CHANGELOG\..*$',
                ],
            ),
        ],
    ),
]
