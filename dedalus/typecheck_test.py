import unittest

from desugar import desugar
from parser import parse
from typecheck import typecheck

class TestTypecheck(unittest.TestCase):
    def test_good_programs(self) -> None:
        good_programs = [
            "p(#a, a) :- .",
            "p(X) :- p(X).",
            "p(X, Y, Z) :- p(X, Y, Z).",
            "p(#a) :- q(#a), r(#a), s(#a).",
            "p(#X) :- q(#X), r(#X), s(#X).",
            "p(#X, X, Y, Z) :- q(#X, X), r(#X, Y), s(#X, Z).",
            "p(#X, X, Y, Z)@next :- q(#X, X), r(#X, Y), s(#X, Z).",
            "p(#Y)@async :- q(#X, X), r(#X, Y), s(#X, Z).",
            "p(#Z)@async :- q(#X, X), r(#X, Y), s(#X, Z).",
        ]

        for good_program in good_programs:
            try:
                program = parse(good_program)
                program = desugar(program)
                program = typecheck(program)
            except Exception as e:
                print(good_program)
                raise e

    def test_bad_programs(self) -> None:
        bad_programs = [
            # Inconsistent arities.
            "p(X, Y) :- p(X), p(Y).",

            # Range restricted.
            "p(X) :- .",
            "p(X, Y, Z) :- .",
            "p(X) :- q(X), !r(Y).",
            "p(X, Y) :- q(X), !r(Y).",

            # Timestamp restricted.
            "p(X)@42 :- q(X).",

            # Location restricted.
            "p(#X) :- q(X), r(#X).",
            "p(#X) :- q(#X), r(#X, #Z).",
            "p(#X) :- q(#X), r(#Y).",
            "p(#Y) :- q(#X), r(#X, Y).",
            "p(#Y)@next :- q(#X), r(#X, Y).",
        ]

        for bad_program in bad_programs:
            with self.assertRaises(ValueError):
                program = parse(bad_program)
                program = desugar(program)
                program = typecheck(program)

if __name__ == '__main__':
    unittest.main()
