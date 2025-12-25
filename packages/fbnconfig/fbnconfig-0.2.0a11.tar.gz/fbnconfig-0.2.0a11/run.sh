#!/bin/bash

set -euo pipefail
THISDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

function help(){
cat <<EOT
       fbnconfig: A tool for configuring a lusid environment

       Run commands for "$THISDIR"
           restore:         install any dependencies (after a fresh clone or when switching branches)
           unit:            run unit tests
           cover:           run unit tests and generate coverage report
           build:           lint / check the code
           dev:             install editable fbnconfig in the venv so that commandline works
           format:          run the ruff formatter to (re)format python files to standard layout
           test:            run the system tests
EOT
}

function run_cmd(){
    local cmd="$1"
    shift || true
    (
        "cmd_$cmd" "$@"
    )
}

function main(){
    local cmd=${1-none}
    shift || true
    case "$cmd" in
        none)
            help "$cmd"
            exit 1
            ;;
        help)
            help "$cmd"
            ;;
        restore|unit|build|test|dev|cover|format)
            run_cmd "$cmd" "$@"
            ;;
        *)
            echo "Unknown command $cmd"
            exit 1
            ;;
    esac
}

function cmd_restore() {
    uv sync
    echo "Environment created in .venv, source .venv/bin/activate to activate it"
}

function cmd_unit() {
    uv run pytest "$THISDIR/tests/unit"
}

function cmd_test() {
    : "${LUSID_ENV?Need to set LUSID_ENV to a lusid base url to run tests}"
    : "${FBN_ACCESS_TOKEN?Need to set FBN_ACCESS_TOKEN to run tests}"
    uv run pytest "$THISDIR/tests/integration" -n auto --dist loadfile
}

function cmd_build() {
    (
        cd "$THISDIR"
        uv run pyright .
        uv run ruff check .
    )
}

function cmd_format() {
    (
        uv run ruff format
    )
}

function cmd_cover() {
    uv run pytest --cov-branch --cov=fbnconfig --cov-report=html --cov-report=term tests/unit
}

main "$@"

