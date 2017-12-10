#! /usr/bin/env bash

set -euo pipefail

main() {
    python -m unittest discover -s dedalus -p '*_test.py'
}

main "$@"
