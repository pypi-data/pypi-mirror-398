#!/bin/sh

# Access folder
script_path=$(readlink -f "${0}")
test_path=$(readlink -f "${script_path%/*}")
cd "${test_path}/"

# Configure tests
set -ex

# Run tests
pre-commit-crocodile --list
pre-commit-crocodile --list --no-color
pre-commit-crocodile --set themes no_color 1
pre-commit-crocodile --list
pre-commit-crocodile --set themes no_color 0
pre-commit-crocodile --list
pre-commit-crocodile --set themes no_color UNSET
pre-commit-crocodile --list
FORCE_COLOR=1 pre-commit-crocodile --list
FORCE_COLOR=0 pre-commit-crocodile --list
NO_COLOR=1 pre-commit-crocodile --list
