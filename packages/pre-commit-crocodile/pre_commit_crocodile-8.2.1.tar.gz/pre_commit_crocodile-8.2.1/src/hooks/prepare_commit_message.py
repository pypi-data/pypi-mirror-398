#!/usr/bin/env python3

# Standard libraries
from os import environ, sep
from pathlib import Path
from re import match, search
import sys
from sys import argv, exit as sys_exit, path
from typing import Any, Dict, List, NamedTuple, Optional, Tuple

# Modules libraries
from yaml import safe_load as yaml_load

# Bind sources
sys.dont_write_bytecode = True
path.append(str(Path(__file__).resolve().parent))

# Components, pylint: disable=import-error,wrong-import-position
from configurations import (
    COMMITIZEN_CONFIGURATION_FILE,
    COMMITS_CHANGES_PATTERN,
    COMMITS_CHANGES_SECTION,
    COMMITS_COMMENTS_PREFIX,
    COMMITS_DEFAULT_BODY,
    COMMITS_DEFAULT_SCOPE,
    COMMITS_DEFAULT_SUBJECT,
    COMMITS_DEFAULT_TYPE,
    CHANGES_EVALUATORS,
    COMMITS_FOOTER_SIGNOFF,
    CHANGES_MATCHERS,
    COMMITS_MESSAGE_EOL,
)

# Data type
Data = Dict[str, Any]

# Parse commitizen configuration
def parse_commitizen_configurations() -> bool:

    # Variables
    always_signoff: bool = False
    configuration: str
    data: Data

    # Detect commitizen configuration
    if 'PWD' in environ:
        configuration = f"{environ['PWD']}{sep}{COMMITIZEN_CONFIGURATION_FILE}"
    else:
        configuration = COMMITIZEN_CONFIGURATION_FILE

    # Parse commitizen configuration
    if Path(configuration).exists():
        with Path(configuration).open(encoding='utf8', mode='r') as file:
            data = yaml_load(file)

            # Extract always_signoff
            if 'commitizen' in data and 'always_signoff' in data['commitizen']:
                always_signoff = bool(data['commitizen']['always_signoff'])

    # Result
    return always_signoff

# Parse commit input
def parse_commit_input(filepath: str) -> Tuple[bool, bool, str, List[str]]:

    # Variables
    capture: bool = False
    changes: List[str] = []
    context: List[str] = []
    empty: bool = True
    signoff: bool = False

    # Read commit template
    with open(filepath, encoding='utf8', mode='r') as file:
        for line in file:

            # Get line content
            content = line.rstrip()

            # Append context
            context += [content]

            # Detect signoff
            if content and content.startswith(COMMITS_FOOTER_SIGNOFF):
                signoff = True

            # Detect contents
            if content and not any(
                    content.startswith(prefix) for prefix in [
                        COMMITS_COMMENTS_PREFIX,
                        COMMITS_FOOTER_SIGNOFF,
                    ]):
                empty = False

            # Detect section
            if content.startswith(COMMITS_CHANGES_SECTION):
                capture = True
                continue

            # Parse section
            if capture:
                matches = match(COMMITS_CHANGES_PATTERN, content)
                if matches:
                    changes.append(matches.group(3).strip())
                elif not content.strip() or content.startswith('#'):
                    capture = False

    # Result
    return empty, signoff, COMMITS_MESSAGE_EOL.join(context), changes

# Prepare commit title, pylint: disable=too-many-branches,too-many-locals,too-many-nested-blocks
def prepare_commit_title(changes: List[str]) -> Tuple[str, str]:

    # Types
    Result = NamedTuple('Result', [
        ('priority', int),
        ('level', int),
        ('commit_type', str),
        ('commit_scope', str),
    ])

    # Variables
    commit_scope: str = COMMITS_DEFAULT_SCOPE
    commit_type: str = COMMITS_DEFAULT_TYPE
    level: int
    levels: List[int]
    priority: int = 0
    results: List[Result] = []

    # Evaluate common changes
    for changes_evaluator in CHANGES_EVALUATORS:
        priority += 1
        for type_change in changes_evaluator.changes:
            for change in changes:
                if not search(type_change, change):
                    continue
                for parser in changes_evaluator.parsers:
                    matches = search(parser.match, change)
                    if not matches or not isinstance(matches.lastindex, int):
                        continue
                    level = 0
                    for group in parser.groups:
                        level += 1
                        if matches.lastindex >= group:
                            results += [
                                Result(
                                    priority=priority,
                                    level=level,
                                    commit_type=parser.commit_type,
                                    commit_scope=matches.group(group),
                                )
                            ]

    # Match common changes
    for changes_matcher in CHANGES_MATCHERS:
        priority += 1
        for matcher_type in changes_matcher.types:
            for type_change in matcher_type.changes:
                for change in changes:
                    if search(type_change, change):
                        results += [
                            Result(
                                priority=priority,
                                level=0,
                                commit_type=matcher_type.commit_type,
                                commit_scope=changes_matcher.commit_scope,
                            )
                        ]

    # Parse results
    if results:
        priority = min((result.priority for result in results))
        results = [result for result in set(results) if result.priority == priority]
        levels = sorted([result.level for result in results])
        level = min((level for level in set(levels) if levels.count(level) == 1),
                    default=levels[-1])
        for result in [result for result in set(results) if result.level == level]:
            commit_type = result.commit_type
            commit_scope = result.commit_scope
            break

    # Adapt scope
    commit_scope = commit_scope.lower()

    # Result
    return commit_type, commit_scope

# Prepare commit message, pylint: disable=too-many-arguments,too-many-positional-arguments
def prepare_commit_template(
    commit_type: str,
    commit_scope: str,
    commit_subject: str,
    commit_body: str,
    signoff: bool,
    always_signoff: bool,
) -> str:

    # Variables
    commit_lines: List[str] = []

    # Prepare commit title
    commit_lines += [
        f'{commit_type}({commit_scope}): {commit_subject}',
    ]

    # Prepare commit body
    template_body = not ([
        line for line in commit_body.splitlines()
        if not line.startswith(COMMITS_COMMENTS_PREFIX)
    ])
    if commit_body:
        commit_lines += [
            '',
            commit_body,
        ]

    # Append commit separator
    if commit_body and (always_signoff or signoff):
        commit_lines += [
            f'{COMMITS_COMMENTS_PREFIX} ---' if template_body else '---',
        ]

    # Inject commit signoff
    if not signoff and always_signoff and 'GIT_AUTHOR_NAME' in environ \
            and 'GIT_AUTHOR_EMAIL' in environ:
        commit_lines += [
            '',
            f"{COMMITS_FOOTER_SIGNOFF}{environ['GIT_AUTHOR_NAME']} <{environ['GIT_AUTHOR_EMAIL']}>",
        ]

    # Append comments separator
    if not signoff:
        commit_lines += [
            '',
        ]

    # Result
    return str(COMMITS_MESSAGE_EOL.join(commit_lines))

# Main, pylint: disable=too-many-branches,too-many-statements
def main() -> None:

    # Variables
    always_signoff: bool
    changes: List[str]
    commit_scope: str
    commit_type: str
    context: str
    empty: bool
    filepath: str
    signoff: bool
    source: Optional[str]

    # Validate arguments
    if len(argv) <= 1:
        sys_exit(1)

    # Parse arguments
    filepath = argv[1]
    source = argv[2] if len(argv) > 2 else None

    # Ignore commit source, documentation:
    # - message (if a -m or -F option was given)
    # - template (if a -t option was given or the configuration option commit.template is set)
    # - merge (if the commit is a merge or a .git/MERGE_MSG file exists)
    # - squash (if a .git/SQUASH_MSG file exists)
    # - commit, followed by a commit object name (if a -c, -C or --amend option was given)
    if source and source in ['template', 'squash', 'commit']:
        sys_exit(0)

    # Parse commitizen configuration
    always_signoff = parse_commitizen_configurations()

    # Parse commit input
    empty, signoff, context, changes = parse_commit_input(filepath)

    # Existing commit input
    if not empty:
        sys_exit(0)

    # Prepare commit title
    commit_type, commit_scope = prepare_commit_title(changes)

    # Prepare commit template
    commit_template = prepare_commit_template(
        commit_type=commit_type,
        commit_scope=commit_scope,
        commit_subject=COMMITS_DEFAULT_SUBJECT,
        commit_body=COMMITS_DEFAULT_BODY,
        signoff=signoff,
        always_signoff=always_signoff,
    )

    # Write commit template
    if environ.get('GIT_EXEC_PATH', ''):
        with open(filepath, encoding='utf8', mode='w') as file:
            file.write(commit_template + context)

    # Dump commit template
    else:
        print(commit_template + context)

    # Result
    sys_exit(0)

# Entrypoint
if __name__ == '__main__': # pragma: no cover
    main()
