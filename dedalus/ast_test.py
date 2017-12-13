from typing import List, Set, Tuple
import unittest

from desugar import desugar
from typecheck import typecheck
import parser
import ast

class TestAst(unittest.TestCase):
    def predicate(self, x: str) -> ast.Predicate:
        return parser.predicate.parse_strict(x)

    def test_program_predicates(self) -> None:
        test_cases: List[Tuple[str, Set[str]]] = [
            ('p(#a) :- .', {'p'}),
            ('p() :- q().', {'p', 'q'}),
            ('p() :- q(), r().', {'p', 'q', 'r'}),
            (r"""p() :- q(), r().
                 s(#a) :- .
                 t(X) :- u(X).""",
             {'p', 'q', 'r', 's', 't', 'u'}),
        ]
        for source, predicates in test_cases:
            program = typecheck(desugar(parser.parse(source)))
            expected = {self.predicate(p) for p in predicates}
            self.assertEqual(program.predicates(), expected)

    def test_program_idb(self) -> None:
        test_cases: List[Tuple[str, Set[str]]] = [
            ('p(#a) :- .', set()),
            ('p() :- q().', {'p'}),
            ('p() :- q(), r().', {'p'}),
            (r"""p(#a, b) :- .
                 p(#a, c)@42 :- .
                 q(#a, b) :- .
                 q(#a, b)@42 :- .
                 q(X) :- p(X).""",
             {'q'}),
        ]
        for source, predicates in test_cases:
            program = typecheck(desugar(parser.parse(source)))
            expected = {self.predicate(p) for p in predicates}
            self.assertEqual(program.idb(), expected)

    def test_program_edb(self) -> None:
        test_cases: List[Tuple[str, Set[str]]] = [
            ('p(#a) :- .', {'p'}),
            ('p() :- q().', {'q'}),
            ('p() :- q(), r().', {'q', 'r'}),
            (r"""p(#a, b) :- .
                 p(#a, c)@42 :- .
                 q(#a, b) :- .
                 q(#a, b)@42 :- .
                 q(X) :- p(X).""",
             {'p'}),
        ]
        for source, predicates in test_cases:
            program = typecheck(desugar(parser.parse(source)))
            expected = {self.predicate(p) for p in predicates}
            self.assertEqual(program.edb(), expected)

    def test_program_persistent_edb(self) -> None:
        test_cases: List[Tuple[str, Set[str]]] = [
            ('p(#a) :- .', {'p'}),
            ('p(#a)@0 :- .', set()),
            ('p(#a)@next :- .', set()),
            (r"""p(#a) :- .
                 p(#a)@0 :- .""",
             set()),
        ]
        for source, predicates in test_cases:
            program = typecheck(desugar(parser.parse(source)))
            expected = {self.predicate(p) for p in predicates}
            self.assertEqual(program.persistent_edb(), expected)

if __name__ == '__main__':
    unittest.main()
