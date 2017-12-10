import unittest

import parsec

import parser

class TestParser(unittest.TestCase):
    def test_good_programs(self):
        good_programs = [
            "p() :- .",
            "p(X) :- .",
            "p(x) :- .",
            "foo(X) :- .",
            "foo(x) :- .",
            "foo(XXX) :- .",
            "foo(xxx) :- .",
            "foo(Xxx) :- .",
            "foo(xXX) :- .",
            "p(X, Y, Z) :- .",
            "p(x, y, z) :- .",
            "p(X, y, Z) :- .",
            "p(#X, y, Z) :- .",
            "p(X, #y, Z) :- .",
            "p(#X, #y, #Z) :- .",
            "p()@0 :- .",
            "p()@1 :- .",
            "p()@2 :- .",
            "p()@1933 :- .",
            "p()@next :- .",
            "p()@async :- .",
            "p(X, #Z)@next :- q(#X, Y), s(Y, #Z)."


            r"""

            // This is a comment.
            p(X) :- p(X), q(). // Another comment.
            p(X) :- p(X), q(). p(X) :- .

            // Comment

            p

            (

            X

            )

            @

            next

            :-

            p ( # X ) .


            """,
        ]

        for good_program in good_programs:
            try:
                parser.parse(good_program)
            except parsec.ParseError as e:
                print(good_program)
                raise e

    def test_bad_programs(self):
        bad_programs = [
            "",
            "p",
            "p()",
            "p(X)",
            "p(X) :- ",
            "p(X) :- p(X)",
            "p X) :- p(X).",
            "p(X  :- p(X).",
            "p(X) :- p X).",
            "p(X) :- p(X .",
            "p(1) :- p(X).",
            "p($) :- p(X).",
            "p(X)@ :- p(X).",
            "p(X)@foo :- p(X).",
            "p(X) :- p(X) p(X).",
            "p(X) :- p(X)@next.",
            "#p(X) :- p(X).",
            "p(X) : - p(X).",
            "p(X) :- p(X)..",
        ]

        for bad_program in bad_programs:
            with self.assertRaises(parsec.ParseError):
                parser.parse(bad_program)

if __name__ == '__main__':
    unittest.main()
