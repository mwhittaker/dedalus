from parsec import generate, many, regex, string, times
from typing import NamedTuple, Optional, Union
import re
import traceback

from desugar import desugar
from parser import parse
from typecheck import typecheck, typechecks
import asts
import run


class ReplState(NamedTuple):
    program: Optional[asts.Program]
    process: Optional[run.Process]

class Help(NamedTuple):
    pass

    def run(self, state: ReplState) -> ReplState:
        print("#load <filename> | #show | #step <n> | <rule>")
        return state

class Load(NamedTuple):
    filename: str

    def run(self, state: ReplState) -> ReplState:
        with open(self.filename) as f:
            program = typecheck(desugar(parse(f.read())))
            return state._replace(program=program)

class Show(NamedTuple):
    pass

    def run(self, state: ReplState) -> ReplState:
        if state.program is None:
            print("No program.")
        else:
            print(str(state.program))
        return state

class Step(NamedTuple):
    timesteps: Optional[int]

    def run(self, state: ReplState) -> ReplState:
        if state.program is None:
            print("No program.")
            return state

        process = state.process or run.spawn(state.program)
        timesteps = self.timesteps or 1
        process = run.run(process, timesteps)
        print(str(process))
        return state._replace(process=process)

class Line(NamedTuple):
    line: str

    def run(self, state: ReplState) -> ReplState:
        program = typecheck(desugar(parse(self.line)))
        if state.program is None:
            return state._replace(program=program)

        assert len(program.rules) == 1
        state.program.rules.append(program.rules[0])
        try:
            typecheck(state.program)
            return state
        except ValueError as e:
            traceback.print_exc()
            del state.program.rules[len(state.program.rules) - 1]
            return state


# Whitespace and comments.
whitespace = regex(r'\s+', re.MULTILINE)
ignore = many(whitespace)

# Lexing.
lexeme = lambda p: p << ignore
hashtag = lexeme(string('#'))
number = lexeme(regex(r'\d+')).parsecmap(int)
filename = lexeme(regex(r'[^\s]+'))
anything = lexeme(regex(r'.*'))

help_cmd = lexeme(regex(r'#help', re.IGNORECASE))
load_cmd = lexeme(regex(r'#load', re.IGNORECASE))
show_cmd = lexeme(regex(r'#show', re.IGNORECASE))
step_cmd = lexeme(regex(r'#step', re.IGNORECASE))

# Parsing.
def maybe(p):
    @generate
    def f():
        xs = yield times(p, 0, 1)
        assert len(xs) in [0, 1]
        return xs[0] if len(xs) == 1 else None
    return f

help_ = help_cmd.parsecmap(lambda _: Help())
load = load_cmd >> filename.parsecmap(Load)
show = show_cmd.parsecmap(lambda _: Show())
line = anything.parsecmap(Line)
step = step_cmd >> maybe(number).parsecmap(Step)
command = ignore >> (help_ ^ load ^ show ^ step ^ line)

def repl(filename: Optional[str]) -> None:
    state = ReplState(None, None)
    if filename is not None:
        # Pylint is confused: https://github.com/PyCQA/pylint/issues/1628
        state = Load(filename).run(state) # pylint: disable=no-member
        state = Show().run(state) # pylint: disable=no-member

    while True:
        try:
            print('> ', end='')
            c = command.parse_strict(input())
            state = c.run(state)
        except EOFError:
            break
        except Exception as e:
            traceback.print_exc()
