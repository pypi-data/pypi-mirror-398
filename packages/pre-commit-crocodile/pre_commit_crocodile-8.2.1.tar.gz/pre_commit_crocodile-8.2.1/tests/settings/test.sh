#!/bin/sh

# Access folder
script_path=$(readlink -f "${0}")
test_path=$(readlink -f "${script_path%/*}")
cd "${test_path}/"

# Configure tests
set -ex

# Run tests
pre-commit-crocodile --settings
! type sudo >/dev/null 2>&1 || sudo -E env PYTHONPATH="${PYTHONPATH}" pre-commit-crocodile --settings
pre-commit-crocodile --set && exit 1 || true
pre-commit-crocodile --set GROUP && exit 1 || true
pre-commit-crocodile --set GROUP KEY && exit 1 || true
pre-commit-crocodile --set package test 1
pre-commit-crocodile --set package test 0
pre-commit-crocodile --set package test UNSET
pre-commit-crocodile --set updates enabled NaN
pre-commit-crocodile --version
pre-commit-crocodile --set updates enabled UNSET
