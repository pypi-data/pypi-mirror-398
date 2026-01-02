#!/bin/sh

# Access folder
script_path=$(readlink -f "${0}")
test_path=$(readlink -f "${script_path%/*}")
cd "${test_path}/"

# Detect Windows host
if [ "${OSTYPE}" = 'msys' ] || [ "${OSTYPE}" = 'win32' ]; then
  echo 'INFO: Test "windows" running on a Windows host'

# Detect Wine support
elif type wine >/dev/null 2>&1 && wine python --version >/dev/null 2>&1; then
  echo 'INFO: Test "windows" running in a Wine Python environment'
  if wine pre-commit-crocodile --version >/dev/null 2>&1; then
    alias pre-commit-crocodile='wine pre-commit-crocodile'
  fi

# Unsupported host
else
  echo 'INFO: Test "windows" was ignored as it is not supported on this host'
  exit 0
fi

# Configure tests
set -ex

# Run tests
pre-commit-crocodile --settings
pre-commit-crocodile --list
