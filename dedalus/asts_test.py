from typing import List, Set, Tuple
import unittest

from desugar import desugar
from typecheck import typecheck
import parser
import asts

class TestAsts(unittest.TestCase):
    def predicate(self, x: str) -> asts.Predicate:
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

    def test_program_is_positive(self) -> None:
        positive_programs: List[str] = [
            'p(#a) :- .',
            'p(X) :- q(X), r(X).',
            r"""p(X) :- q(X), r(X).
                p(Y) :- r(Y), r(X).""",
        ]
        for source in positive_programs:
            program = typecheck(desugar(parser.parse(source)))
            self.assertTrue(program.is_positive())

        negative_programs: List[str] = [
            'p(X) :- q(X), !r(X).',
            r"""p(X) :- q(X).
                p(X) :- q(X), !r(X).""",
        ]
        for source in negative_programs:
            program = typecheck(desugar(parser.parse(source)))
            self.assertFalse(program.is_positive())

    def test_program_is_semipositive(self) -> None:
        semipositive_programs: List[str] = [
            'p(#a) :- .',
            'p(X) :- q(X), r(X).',
            r"""p(X) :- q(X), r(X).
                p(Y) :- r(Y), r(X).""",
            r"""p(#a, b) :- .
                q(X) :- q(X), !p(X).""",
        ]
        for source in semipositive_programs:
            program = typecheck(desugar(parser.parse(source)))
            self.assertTrue(program.is_semipositive())

        not_semipositive_programs: List[str] = [
            r"""r(X) :- q(X).
                p(X) :- q(X), !r(X).""",
        ]
        for source in not_semipositive_programs:
            program = typecheck(desugar(parser.parse(source)))
            self.assertFalse(program.is_semipositive())

    def test_program_is_stratified(self) -> None:
        stratified_programs: List[str] = [
            'p(#a) :- .',
            'p(X) :- q(X).',
            'p(X) :- p(X).',
            r"""b() :- a().
                c() :- b().
                a() :- c().""",
            r"""a() :- b(), c().
                b() :- a(), c().
                c() :- a(), b().""",
            r"""b(X) :- p(X), !a(X).
                c(X) :- p(X), !b(X).""",
            r"""b(X) :- p(X), a(X).
                c(X) :- p(X), b(X).
                a(X) :- p(X), c(X).

                d(X) :- p(X), !c(X).

                e(X) :- p(X), d(X).
                f(X) :- p(X), e(X).
                d(X) :- p(X), f(X).""",
            r"""b(X) :- p(X), a(X).
                c(X) :- p(X), b(X).
                c(X) :- p(X), !a(X).
                d(X) :- p(X), c(X)."""
        ]
        for source in stratified_programs:
            program = typecheck(desugar(parser.parse(source)))
            self.assertTrue(program.is_stratified())

        not_stratified_programs: List[str] = [
            r"""a(X) :- p(X), !b(X).
                b(X) :- p(X), !a(X).""",
            r"""a(X) :- p(X), !b(X).
                b(X) :- p(X), a(X).""",
            r"""a(X) :- p(X), !b(X).
                b(X) :- p(X), c(X).
                c(X) :- p(X), a(X).""",
            r"""a(X) :- p(X), !b(X).
                b(X) :- p(X), c(X).
                c(X) :- p(X), a(X).""",
            r"""b(X) :- p(X), !a(X).
                c(X) :- p(X), b(X).
                c(X) :- p(X), !a(X).
                d(X) :- p(X), c(X).
                a(X) :- p(X), d(X).""",
            r"""b(X) :- p(X), a(X).
                c(X) :- p(X), b(X).
                a(X) :- p(X), c(X).

                d(X) :- p(X), !c(X).
                a(X) :- p(X), !f(x).

                e(X) :- p(X), d(X).
                f(X) :- p(X), e(X).
                d(X) :- p(X), f(X).""",
        ]
        for source in not_stratified_programs:
            program = typecheck(desugar(parser.parse(source)))
            self.assertFalse(program.is_stratified())

if __name__ == '__main__':
    unittest.main()
