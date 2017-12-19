from typing import List, Set, Tuple
import unittest

import networkx as nx

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

    def test_program_deductive_pdg(self) -> None:
        source = r"""
          a(X) :- p(X).
          b(X) :- a(X), d(X).
          c(X) :- !b(X), e(X).
          d(X)@next :- a(X), b(X), c(X).
          e(X)@async :- a(X), b(X), c(X).
          a(X)@next :- a(X).
          a(X)@async :- a(X).
        """
        program = typecheck(desugar(parser.parse(source)))
        dpdg = program.deductive_pdg()

        a = self.predicate('a')
        b = self.predicate('b')
        c = self.predicate('c')
        expected = nx.DiGraph()
        expected.add_nodes_from([a, b, c])
        expected.add_edges_from([(a, b), (b, c)])

        self.assertEqual(dpdg.nodes, expected.nodes)
        self.assertEqual(dpdg.edges, expected.edges)
        self.assertFalse(dpdg[a][b]['negative'])
        self.assertTrue(dpdg[b][c]['negative'])

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
            self.assertTrue(program.is_stratified(), source)

        not_stratified_programs: List[str] = [
            r"""a(X)@next :- p(X), !b(X).
                b(X)@next :- p(X), !a(X).""",
            r"""a(X)@next :- p(X), !b(X).
                b(X)@next :- p(X), a(X).""",
            r"""a(X)@next :- p(X), !b(X).
                b(X)@next :- p(X), c(X).
                c(X)@next :- p(X), a(X).""",
            r"""a(X)@next :- p(X), !b(X).
                b(X)@next :- p(X), c(X).
                c(X)@next :- p(X), a(X).""",
            r"""b(X)@next :- p(X), !a(X).
                c(X)@next :- p(X), b(X).
                c(X)@next :- p(X), !a(X).
                d(X)@next :- p(X), c(X).
                a(X)@next :- p(X), d(X).""",
            r"""b(X)@next :- p(X), a(X).
                c(X)@next :- p(X), b(X).
                a(X)@next :- p(X), c(X).

                d(X)@next :- p(X), !c(X).
                a(X)@next :- p(X), !f(x).

                e(X)@next :- p(X), d(X).
                f(X)@next :- p(X), e(X).
                d(X)@next :- p(X), f(X).""",
        ]
        for source in not_stratified_programs:
            program = typecheck(desugar(parser.parse(source)))
            self.assertFalse(program.is_stratified(), source)

    def test_program_has_guarded_asynchrony(self) -> None:
        guarded_async_programs: List[str] = [
            'p(#a) :- .',
            'p(X) :- p(X).',
            'p(X)@next :- p(X).',
            r"""p(X)@async :- p(X).
                p(X)@next :- p(X).""",
            r"""p(X, Y, Z)@async :- p(X, Y, Z).
                p(X, Y, Z)@next :- p(X, Y, Z).""",
            r"""p(X)@async :- p(X).
                q(X, Y)@async :- q(X, Y).
                r(X, Y, Z)@async :- r(X, Y, Z).
                p(X)@next :- p(X).
                q(X, Y)@next :- q(X, Y).
                r(X, Y, Z)@next :- r(X, Y, Z).""",
        ]
        for source in guarded_async_programs:
            program = typecheck(desugar(parser.parse(source)))
            self.assertTrue(program.has_guarded_asynchrony())

        not_guarded_async_programs: List[str] = [
            'p(X)@async :- p(X).',
            'p(X, Y, Z)@async :- p(X, Y, Z).',
            r"""p(X)@async :- p(X).
                q(X, Y)@async :- q(X, Y).
                r(X, Y, Z)@async :- r(X, Y, Z).
                p(X)@next :- p(X).
                r(X, Y, Z)@next :- r(X, Y, Z).""",
        ]
        for source in not_guarded_async_programs:
            program = typecheck(desugar(parser.parse(source)))
            self.assertFalse(program.has_guarded_asynchrony(), source)

if __name__ == '__main__':
    unittest.main()
