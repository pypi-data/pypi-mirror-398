#!/usr/bin/env bash

set -e
set -x

echo "🧪 Running Python integration test..."
coverage run --source=src -m pytest
coverage report --show-missing
coverage html --title "${@-coverage}"
