#!/usr/bin/env bash

build() {
    python setup.py sdist bdist_wheel
}

check() {
    flake8 migrate tests
    pylint migrate tests --disable=C0103 # invalid-name
    mypy migrate tests --strict
}

tests() {
    pytest --cov=migrate tests
}

usage() {
    cat << EOF
usage: run.sh [command]

Runs development scripts.

commands:

build
    Build package.

check
    Run linters and type checkers.

tests
    Run tests.
EOF
}

COMMAND="$1"

if [ "$COMMAND" = "" ];
then
    usage
else
    "$COMMAND"
fi
