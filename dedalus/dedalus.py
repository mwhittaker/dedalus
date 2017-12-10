#! /usr/bin/env python

import argparse

from desugar import desugar
from parser import parse
from typecheck import typecheck
import ast


def _parse_from_file(filename: str) -> ast.Program:
    with open(filename, "r") as f:
        return parse(f.read())

def _parse(filename: str) -> None:
    program = _parse_from_file(filename)
    print(str(program))

def _desugar(filename: str) -> None:
    program = desugar(_parse_from_file(filename))
    print(str(program))

def _typecheck(filename: str) -> None:
    typecheck(desugar(_parse_from_file(filename)))

def _repl() -> None:
    while True:
        try:
            print("> ", end="")
            program = typecheck(desugar(parse(input())))
            print(program)
        except EOFError:
            break
        except Exception as e:
            print(e)

def main(args: argparse.Namespace) -> None:
    if args.subcommand == "parse":
        _parse(args.filename)
    elif args.subcommand == "desugar":
        _desugar(args.filename)
    elif args.subcommand == "typecheck":
        _typecheck(args.filename)
    elif args.subcommand == "repl":
        _repl()
    else:
        print(f'Unrecognized subcommand "{args.subcommand}".')

def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='subcommand')
    subparsers.required = True # type: ignore

    subparser_names = ['parse', 'desugar', 'typecheck']
    for subparser_name in subparser_names:
        subparser = subparsers.add_parser(subparser_name)
        subparser.add_argument("filename", help="Dedalus file.")

    repl = subparsers.add_parser('repl')

    # TODO(mwhittaker): Add run.
    # TODO(mwhittaker): Add server.

    return parser

if __name__ == '__main__':
    parser = get_parser()
    main(parser.parse_args())
