import unittest
from typing import Any, Dict, List, Optional, Tuple

from desugar import desugar
from run import (Bindings, _eval_rule, _stratify, _subst, _unify, run, spawn,
                 step)
from typecheck import typecheck
import parser
import asts


class TestRun(unittest.TestCase):
    def var(self, x: str) -> asts.Variable:
        return parser.variable.parse_strict(x)

    def predicate(self, x: str) -> asts.Predicate:
        return parser.predicate.parse_strict(x)

    def atom(self, x: str) -> asts.Atom:
        return parser.atom.parse_strict(x)

    def test_subst(self) -> None:
        A = self.var('A')
        X = self.var('X')
        Y = self.var('Y')
        Z = self.var('Z')

        GoodTestCase = Tuple[asts.Atom, Bindings, Tuple[Any, ...]]
        good_test_cases: List[GoodTestCase] = [
            (self.atom('p(a,b,c)'), {}, ('a','b','c')),
            (self.atom('p(a,b,c)'), {X:'x'}, ('a','b','c')),
            (self.atom('p(a,b,c)'), {X:'x', Y:'y'}, ('a','b','c')),
            (self.atom('p(a,b,c)'), {X:'x', Y:'y', Z:'z'}, ('a','b','c')),
            (self.atom('p(a,b,Z)'), {X:'x', Y:'y', Z:'z'}, ('a','b','z')),
            (self.atom('p(a,Y,Z)'), {X:'x', Y:'y', Z:'z'}, ('a','y','z')),
            (self.atom('p(X,Y,Z)'), {X:'x', Y:'y', Z:'z'}, ('x','y','z')),
            (self.atom('p(X,Y,c)'), {X:'x', Y:'y', Z:'z'}, ('x','y','c')),
            (self.atom('p(X,b,c)'), {X:'x', Y:'y', Z:'z'}, ('x','b','c')),
            (self.atom('p(X)'), {A:'a', X:'x'}, ('x',)),
        ]
        for atom, bindings, expected in good_test_cases:
            self.assertEqual(_subst(atom, bindings), expected)

        BadTestCase = Tuple[asts.Atom, Bindings]
        bad_test_cases: List[BadTestCase] = [
            (self.atom('p(X)'), {}),
            (self.atom('p(X)'), {Y:'y'}),
            (self.atom('p(X, Y)'), {Y:'y'}),
        ]
        for atom, bindings in bad_test_cases:
            with self.assertRaises(AssertionError):
                _subst(atom, bindings)
                print(atom, bindings)

    def test_unify(self) -> None:
        A = self.var('A')
        B = self.var('B')
        C = self.var('C')
        X = self.var('X')
        Y = self.var('Y')
        Z = self.var('Z')
        a = 'a'
        b = 'b'
        c = 'c'
        x = 'x'
        y = 'y'
        z = 'z'

        GoodTestCase = Tuple[
            List[asts.Atom],
            List[Tuple[Any, ...]],
            Optional[Bindings]]
        good_test_cases: List[GoodTestCase] = [
            ([], [], {}),

            ([self.atom('p(X,Y,Z)')], [(x,y,z)], {X:x, Y:y, Z:z}),
            ([self.atom('p(a,Y,Z)')], [(a,y,z)], {Y:y, Z:z}),
            ([self.atom('p(a,b,Z)')], [(a,b,z)], {Z:z}),
            ([self.atom('p(a,b,c)')], [(a,b,c)], {}),
            ([self.atom('p(a,Y,Z)')], [(b,y,z)], None),
            ([self.atom('p(a,b,Z)')], [(a,c,z)], None),
            ([self.atom('p(a,b,c)')], [(a,b,a)], None),

            ([self.atom('p(X,Y,Z)'), self.atom('q(A,B,C)')],
             [(x,y,z), (a,b,c)],
             {X:x, Y:y, Z:z, A:a, B:b, C:c}),
            ([self.atom('p(X,Y,Z)'), self.atom('q(Z,B,C)')],
             [(x,y,z), (z,b,c)],
             {X:x, Y:y, Z:z, B:b, C:c}),
            ([self.atom('p(X,Y,Z)'), self.atom('q(Y,Z,C)')],
             [(x,y,z), (y,z,c)],
             {X:x, Y:y, Z:z, C:c}),
            ([self.atom('p(X,Y,Z)'), self.atom('q(X,Y,Z)')],
             [(x,y,z), (x,y,z)],
             {X:x, Y:y, Z:z}),
            ([self.atom('p(X,Y,Z)'), self.atom('q(Z,Y,X)')],
             [(x,y,z), (z,y,x)],
             {X:x, Y:y, Z:z}),

            ([self.atom('p(X,Y,Z)'), self.atom('q(Z,B,C)')],
             [(x,y,z), (a,b,c)],
             None),
            ([self.atom('p(X,Y,Z)'), self.atom('q(Y,Z,C)')],
             [(x,y,z), (y,y,c)],
             None),
            ([self.atom('p(X,Y,Z)'), self.atom('q(X,Y,Z)')],
             [(x,y,z), (x,y,x)],
             None),
            ([self.atom('p(X,Y,Z)'), self.atom('q(Z,Y,X)')],
             [(x,y,z), (z,y,z)],
             None),

            ([self.atom('p(X,Y)'), self.atom('p(Y,Z)'), self.atom('p(Z,X)')],
             [(x,y), (y,z), (z,x)],
             {X:x, Y:y, Z:z}),
        ]
        for atoms, tuples, expected in good_test_cases:
            self.assertEqual(_unify(atoms, tuples), expected)

        BadTestCase = Tuple[List[asts.Atom], List[Tuple[Any, ...]]]
        bad_test_cases: List[BadTestCase] = [
            ([self.atom('p(X)')], []),
            ([], [(x,)]),
            ([self.atom('p(X, Y)')], [(x,)]),
            ([self.atom('p(X)')], [(x,y)]),
            ([self.atom('p(X)'), self.atom('p(Y)')], [(x,)]),
        ]
        for atoms, tuples in bad_test_cases:
            with self.assertRaises(AssertionError):
                _unify(atoms, tuples)
                print(atoms, tuples)

    def test_eval_rule(self) -> None:
        source = r"""
            p(X, Y, Z) :-
                q(X, Y),  q(Y, Z),  q(Z, X),
                !eq(X, Y), !eq(Y, Z), !eq(Z, X),
                leq(X, Y), leq(Y, Z).
        """
        program = parser.parse(source)
        program = desugar(program)
        program = typecheck(program)

        q = self.predicate('q')
        eq = self.predicate('eq')
        leq = self.predicate('leq')
        l, a, b, c, d, e = "labcde"

        process = spawn(program)
        process.database[q] = {
            (l, a, a), (l, a, b), (l, a, c), (l, a, d),
            (l, b, a), (l, b, b), (l, b, c), (l, b, d),
            (l, c, a), (l, c, b), (l, c, c), (l, c, d), (l, c, e),
            (l, d, a), (l, d, b), (l, d, c), (l, d, d),
                       (l, e, c),            (l, e, e),
        }
        process.database[eq] = {
            (l, a, a), (l, b, b), (l, c, c), (l, d, d), (l, e, e)}
        process.database[leq] = {
            (l, a, a), (l, a, b), (l, a, c), (l, a, d), (l, a, e),
            (l, b, b), (l, b, c), (l, b, d), (l, b, e),
            (l, c, c), (l, c, d), (l, c, e),
            (l, d, d), (l, d, e),
            (l, e, e),
        }
        expected = {(l, a, b, c), (l, a, b, d), (l, a, c, d), (l, b, c, d)}

        actual = set(_eval_rule(process, program.rules[0]))
        self.assertEqual(actual, expected)

    def test_stratify(self) -> None:
        source = """
          b(X) :- a(X).
          c(X) :- b(X).
          a(X) :- c(X).

          e(X) :- d(X).
          d(X) :- e(X).

          g(X) :- f(X).
          h(X) :- g(X).
          f(X) :- h(X).

          d(X) :- b(X).
          f(X) :- a(X).
          g(X) :- e(X).
        """
        program = typecheck(desugar(parser.parse(source)))
        pdg = program.pdg()
        stratification = _stratify(pdg)

        a = self.predicate('a')
        b = self.predicate('b')
        c = self.predicate('c')
        d = self.predicate('d')
        e = self.predicate('e')
        f = self.predicate('f')
        g = self.predicate('g')
        h = self.predicate('h')

        self.assertEqual(len(stratification), 3)
        self.assertEqual(set(stratification[0].nodes), {a, b, c})
        self.assertEqual(set(stratification[1].nodes), {e, d})
        self.assertEqual(set(stratification[2].nodes), {f, g, h})
        self.assertEqual(set(stratification[0].edges), {(a,b), (b,c), (c,a)})
        self.assertEqual(set(stratification[1].edges), {(e,d), (d,e)})
        self.assertEqual(set(stratification[2].edges), {(f,g), (g,h), (h,f)})

    def test_step(self) -> None:
        # TODO(mwhittaker): Test step.
        pass

if __name__ == '__main__':
    unittest.main()
