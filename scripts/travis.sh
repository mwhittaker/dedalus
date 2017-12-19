#! /usr/bin/env bash

set -euo pipefail

main() {
    set -x
    scripts/pylint.sh
    scripts/mypy.sh
    scripts/unittests.sh
    scripts/typecheck_examples.sh
    set +x
}

main "$@"
