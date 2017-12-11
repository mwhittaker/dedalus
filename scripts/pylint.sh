#! /usr/bin/env bash

set -euo pipefail

main() {
    PYTHONPATH="dedalus" pylint dedalus --errors-only
}

main "$@"
