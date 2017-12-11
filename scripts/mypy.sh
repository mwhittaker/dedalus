#! /usr/bin/env bash

set -euo pipefail

main() {
    MYPYPATH="dedalus" mypy dedalus --ignore-missing-imports
}

main "$@"
