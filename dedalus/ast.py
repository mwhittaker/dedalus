from enum import Enum
from typing import List, NamedTuple, NewType, Union


class Constant(NamedTuple):
    x: str
    is_location: bool

    def __str__(self) -> str:
        hash_ = "#" if self.is_location else ""
        return hash_ + self.x

class Variable(NamedTuple):
    x: str
    is_location: bool

    def __str__(self) -> str:
        hash_ = "#" if self.is_location else ""
        return hash_ + self.x

Term = Union[Constant, Variable]

class Predicate(NamedTuple):
    x: str

    def __str__(self) -> str:
        return self.x

class Atom(NamedTuple):
    predicate: Predicate
    terms: List[Term]

    def __str__(self) -> str:
        terms_string = ", ".join(str(term) for term in self.terms)
        return "{}({})".format(self.predicate, terms_string)

    def constants(self) -> List[Constant]:
        return [term for term in self.terms if isinstance(term, Constant)]

    def variables(self) -> List[Variable]:
        return [term for term in self.terms if isinstance(term, Variable)]

class Literal(NamedTuple):
    negative: bool
    atom: Atom

    def __str__(self) -> str:
        bang = "!" if self.negative else ""
        return f"{bang}{self.atom}"

    def is_negative(self) -> bool:
        return self.negative

    def is_positive(self) -> bool:
        return not self.is_negative()

class DeductiveRule(NamedTuple):
    pass

    def __str__(self) -> str:
        return ""

class InductiveRule(NamedTuple):
    pass

    def __str__(self) -> str:
        return "@next"

class AsyncRule(NamedTuple):
    pass

    def __str__(self) -> str:
        return "@async"

class ConstantTimeRule(NamedTuple):
    time: int

    def __str__(self) -> str:
        return f"@{self.time}"

RuleType = Union[DeductiveRule, InductiveRule, AsyncRule, ConstantTimeRule]

class Rule(NamedTuple):
    head: Atom
    rule_type: RuleType
    body: List[Literal]

    def __str__(self) -> str:
        body_string = ", ".join([str(l) for l in self.body])
        return f"{self.head}{str(self.rule_type)} :- {body_string}."

class Program(NamedTuple):
    rules: List[Rule]

    def __str__(self) -> str:
        return "\n".join(str(rule) for rule in self.rules)

def main() -> None:
    p = Predicate("p")
    X = Variable("X", True)
    r = Program([
        Rule(Atom(p, [X]), DeductiveRule(), [Literal(True, Atom(p, [X]))]),
        Rule(Atom(p, [X]), ConstantTimeRule(42), [Literal(True, Atom(p, [X]))]),
    ])
    print(str(r))

if __name__ == "__main__":
    main()
