#! /usr/bin/env bash

set -euo pipefail

main() {
    python -m unittest discover --verbose -s dedalus -p '*_test.py'
}

main "$@"
