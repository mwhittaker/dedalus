#! /usr/bin/env bash

set -euo pipefail

main() {
    mypy dedalus --ignore-missing-imports
}

main "$@"
