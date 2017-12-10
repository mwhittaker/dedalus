#! /usr/bin/env bash

set -euo pipefail

main() {
    pylint dedalus --errors-only
}

main "$@"
