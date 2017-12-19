#! /usr/bin/env bash

set -euo pipefail

main() {
    for example in examples/*; do
        echo -n "Typechecking $example "
        ./dedalus/dedalus.py typecheck "$example"
        echo "passed."
    done
}

main "$@"
