#!/bin/sh

# Access folder
script_path=$(readlink -f "${0}")
test_path=$(readlink -f "${script_path%/*}")
cd "${test_path}/"

# Detect macOS host
if [ "${OSTYPE}" = 'darwin' ]; then
  echo 'INFO: Test "macos" running on a macOS host'

# Unsupported host
else
  echo 'INFO: Test "macos" will simulate a macOS host as it is not supported on this host'
  export SIMULATE_MAC_OS='true'
fi

# Configure tests
set -ex

# Run tests
pre-commit-crocodile --settings
