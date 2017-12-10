#! /usr/bin/env bash

set -euo pipefail

main() {
    scripts/pylint.sh
    scripts/mypy.sh
}

main "$@"
