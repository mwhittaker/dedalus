import re

from parsec import generate, many, many1, regex, sepBy, string, times

import ast

# Whitespace and comments.
whitespace = regex(r'\s+', re.MULTILINE)
comment = regex(r'//.*')
ignore = many((whitespace | comment))

# Lexing.
lexeme = lambda p: p << ignore
at = lexeme(string('@'))
bang = lexeme(string('!'))
comma = lexeme(string(','))
hashtag = lexeme(string('#'))
lparen = lexeme(string('('))
rparen = lexeme(string(')'))
period = lexeme(string('.'))
turnstyle = lexeme(string(':-'))

next_ = lexeme(string('next'))
async = lexeme(string('async'))
number = lexeme(regex(r'\d+')).parsecmap(int)
constant_id = lexeme(regex(r'[a-z0-9]\w*'))
variable_id = lexeme(regex(r'[A-Z]\w*'))
predicate_id = lexeme(regex(r'[a-z]\w*'))

# Parsing.
def maybe(p):
    @generate
    def f():
        xs = yield times(p, 0, 1)
        assert len(xs) in [0, 1]
        return xs[0] if len(xs) == 1 else None
    return f

@generate
def is_location():
    hashtag_ = yield maybe(hashtag)
    return hashtag_ is not None

@generate
def constant():
    is_location_ = yield is_location
    x = yield constant_id
    return ast.Constant(x, is_location_)

@generate
def variable():
    is_location_ = yield is_location
    x = yield variable_id
    return ast.Variable(x, is_location_)

term = constant ^ variable

predicate = predicate_id.parsecmap(ast.Predicate)

@generate
def atom():
    predicate_ = yield predicate
    yield lparen
    terms = yield sepBy(term, comma)
    yield rparen
    return ast.Atom(predicate_, terms)

@generate
def literal():
    bangs = yield times(bang, 0, 1)
    assert len(bangs) in [0, 1]
    negative = True if len(bangs) == 1 else False
    atom_ = yield atom
    return ast.Literal(negative, atom_)

inductive_rule = at >> next_.parsecmap(lambda _: ast.InductiveRule())
async_rule = at >> async.parsecmap(lambda _: ast.AsyncRule())
constant_time_rule = at >> number.parsecmap(ast.ConstantTimeRule)
non_deductive_rule = inductive_rule ^ async_rule ^ constant_time_rule

@generate
def rule_type():
    rule_types = yield times(non_deductive_rule, 0, 1)
    assert len(rule_types) in [0, 1]
    if len(rule_types) == 1:
        return rule_types[0]
    else:
        return ast.DeductiveRule()

@generate
def rule():
    head = yield atom
    rule_type_ = yield rule_type
    yield turnstyle
    body = yield sepBy(literal, comma)
    yield period
    return ast.Rule(head, rule_type_, body)

program = many1(rule).parsecmap(ast.Program)

parser = ignore >> program

def parse(s: str) -> ast.Program:
    return parser.parse_strict(s)
