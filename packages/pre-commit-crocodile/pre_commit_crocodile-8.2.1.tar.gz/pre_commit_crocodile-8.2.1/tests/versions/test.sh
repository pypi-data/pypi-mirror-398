#!/bin/sh

# Access folder
script_path=$(readlink -f "${0}")
test_path=$(readlink -f "${script_path%/*}")
cd "${test_path}/"

# Configure tests
set -ex

# Configure environment
(
  # Configure versions
  export DEBUG_UPDATES_DISABLE=''
  export DEBUG_VERSION_FAKE='2.0.0'

  # Run tests
  pre-commit-crocodile --version
  pre-commit-crocodile --update-check
  DEBUG_UPDATES_DISABLE=true pre-commit-crocodile --update-check
  FORCE_COLOR=1 pre-commit-crocodile --update-check
  NO_COLOR=1 pre-commit-crocodile --update-check
  FORCE_COLOR=1 PYTHONIOENCODING=ascii pre-commit-crocodile --update-check
  FORCE_COLOR=1 COLUMNS=40 pre-commit-crocodile --update-check
  FORCE_COLOR=1 DEBUG_UPDATES_OFFLINE='' pre-commit-crocodile --update-check
  FORCE_COLOR=1 DEBUG_UPDATES_OFFLINE=true pre-commit-crocodile --update-check
  FORCE_COLOR=1 DEBUG_UPDATES_OFFLINE=true DEBUG_VERSION_FAKE=0.0.2 DEBUG_UPDATES_FAKE=0.0.1 pre-commit-crocodile --update-check
  FORCE_COLOR=1 DEBUG_UPDATES_OFFLINE=true DEBUG_VERSION_FAKE=0.0.2 DEBUG_UPDATES_FAKE=0.0.2 pre-commit-crocodile --update-check
  FORCE_COLOR=1 DEBUG_UPDATES_OFFLINE=true DEBUG_VERSION_FAKE=0.0.2 DEBUG_UPDATES_FAKE=0.0.3 pre-commit-crocodile --update-check
  FORCE_COLOR=1 DEBUG_UPDATES_DAILY=true DEBUG_VERSION_FAKE=0.0.2 DEBUG_UPDATES_FAKE=0.0.3 pre-commit-crocodile --list
  FORCE_COLOR=1 pre-commit-crocodile --list
)
