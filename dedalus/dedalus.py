#! /usr/bin/env python

from typing import Callable
import argparse
import random

from desugar import desugar
from parser import parse
from repl import repl
from run import run, spawn
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

def _run(filename: str, timesteps: int, randint: Callable[[], int]) -> None:
    program = _parse_from_file(filename)
    program = desugar(program)
    program = typecheck(program)
    process = spawn(program, randint)
    process = run(process, timesteps)
    print(str(process))

def main(args: argparse.Namespace) -> None:
    if args.subcommand == 'parse':
        _parse(args.filename)
    elif args.subcommand == 'desugar':
        _desugar(args.filename)
    elif args.subcommand == 'typecheck':
        _typecheck(args.filename)
    elif args.subcommand == 'run':
        assert 1 <= args.low <= args.high
        randint = lambda: random.randint(args.low, args.high)
        _run(args.filename, args.timesteps, randint)
    elif args.subcommand == 'repl':
        repl(args.filename)
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

    run = subparsers.add_parser('run')
    run.add_argument('filename', help='Dedalus file.')
    run.add_argument('--timesteps', type=int, default=10)
    run.add_argument('--low', type=int, default=1)
    run.add_argument('--high', type=int, default=10)

    repl = subparsers.add_parser('repl')
    repl.add_argument('filename', nargs='?', default=None, help='Dedalus file.')

    # TODO(mwhittaker): Add server.

    return parser

if __name__ == '__main__':
    parser = get_parser()
    main(parser.parse_args())
