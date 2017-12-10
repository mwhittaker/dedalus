import unittest

import desugar
import parser

class TestDesugar(unittest.TestCase):
    def _strip_leading_whitespace(self, s: str) -> str:
        lines = [line.strip() for line in s.split("\n") if line.strip() != ""]
        return "\n".join(lines)

    def test_desugar(self):
        program = parser.parse(r"""
            // Desugared.
            p(X) :- .
            p(X) :- q(X), r(X).
            p(X, Y, Z) :- q(X, Y, Z), r(X, Y, Z).

            // Not desugared.
            p(#X) :- q(X), r(X).
            p(X) :- q(#X), r(X).
            p(X) :- q(X), r(#X).
            p(X) :- q(#X), r(#X).
            p(#X) :- q(X), r(#X).
            p(#X) :- q(#X), r(X).
            p(#X) :- q(#X), r(#X).
            p(X, #Y, Z) :- q(X, Y, Z), r(X, Y, Z).
            p(X, Y, Z) :- q(X, Y, #Z), r(X, Y, Z).
            p(X, Y, Z) :- q(X, Y, Z), r(#X, Y, Z).
            p(X, #Y, Z) :- q(X, Y, #Z), r(#X, Y, Z).
        """)
        desugared = desugar.desugar(program)

        expected = self._strip_leading_whitespace(r"""
            p(#_L, X) :- .
            p(#_L, X) :- q(#_L, X), r(#_L, X).
            p(#_L, X, Y, Z) :- q(#_L, X, Y, Z), r(#_L, X, Y, Z).
            p(#X) :- q(X), r(X).
            p(X) :- q(#X), r(X).
            p(X) :- q(X), r(#X).
            p(X) :- q(#X), r(#X).
            p(#X) :- q(X), r(#X).
            p(#X) :- q(#X), r(X).
            p(#X) :- q(#X), r(#X).
            p(X, #Y, Z) :- q(X, Y, Z), r(X, Y, Z).
            p(X, Y, Z) :- q(X, Y, #Z), r(X, Y, Z).
            p(X, Y, Z) :- q(X, Y, Z), r(#X, Y, Z).
            p(X, #Y, Z) :- q(X, Y, #Z), r(#X, Y, Z).
        """)

        # Expand full diff when test fails.
        self.maxDiff = None
        self.assertEqual(str(desugared), expected)

if __name__ == '__main__':
    unittest.main()
