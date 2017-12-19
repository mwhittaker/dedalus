from enum import Enum
from typing import List, NamedTuple, NewType, Set, Union

import networkx as nx


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

    def is_deductive(self) -> bool:
        return isinstance(self.rule_type, DeductiveRule)

    def is_inductive(self) -> bool:
        return isinstance(self.rule_type, InductiveRule)

    def is_async(self) -> bool:
        return isinstance(self.rule_type, AsyncRule)

    def is_constant_time(self) -> bool:
        return isinstance(self.rule_type, ConstantTimeRule)

class Program(NamedTuple):
    rules: List[Rule]

    def __str__(self) -> str:
        return "\n".join(str(rule) for rule in self.rules)

    def predicates(self) -> Set[Predicate]:
        """
        `program.predicates()` returns the set of all predicates present in
        `program`. For example, the following program:

            p(#a, b)@0 :- .
            p(#a, b) :- .
            q(#a, b) :- .
            q(X) :- p(X).
            r(X)@next :- p(X), q(X).

        has predicates `p`, `q`, and `r`.
        """
        predicates: Set[Predicate] = set()
        for rule in self.rules:
            predicates |= {rule.head.predicate}
            predicates |= {l.atom.predicate for l in rule.body}
        return predicates

    def idb(self) -> Set[Predicate]:
        """
        `program.idb()` returns the set of all IDB predicates present in
        `program`. We define a predicate to be in the IDB if it appears on the
        left hand side of a rule with a non-empty body. For example, the
        following program:

            p(#a, b)@0 :- .
            p(#a, b) :- .
            q(#a, b) :- .
            q(X) :- p(X).
            r(X)@next :- p(X), q(X).

        has idb predicates `q` and `r`.
        """
        predicates: Set[Predicate] = set()
        for rule in self.rules:
            if len(rule.body) != 0:
                predicates.add(rule.head.predicate)
        return predicates

    def edb(self) -> Set[Predicate]:
        """
        `program.edb()` returns the set of all EDB predicates present in
        `program`. We define a predicate to be in the EDB if it's not in the
        IDB. For example, the following program:

            p(#a, b)@0 :- .
            p(#a, b) :- .
            q(#a, b) :- .
            q(X) :- p(X).
            r(X)@next :- p(X), q(X).

        has edb predicate `p`.
        """
        return self.predicates() - self.idb()

    def persistent_edb(self) -> Set[Predicate]:
        """
        `program.persistent_edb()` returns the set of all EDB predicates whose
        contents are guaranteed to be available at all timesteps.
        Conservatively, we consider an EDB predicate to be persistent if all of
        the predicates rules---i.e. the rules in which the predicate is the
        head---are deductive. For example, consider the following program:

            p(#a, b)@0 :- .
            p(#a, b) :- .
            q(#a, b) :- .

        Both `p` and `q` are EDB predicates, but only `q` is persistent. `p` is
        not persistent because the first rule is not deductive.
        """
        not_persistent: Set[Predicate] = set()
        for rule in self.rules:
            p = rule.head.predicate
            if p in self.edb() and not rule.is_deductive():
                not_persistent.add(p)
        return self.edb() - not_persistent

    def is_positive(self) -> bool:
        """
        `program.is_positive()` returns True if `program` is a positive datalog
        program. A datalog program is positive if all of its literals are
        positive.
        """
        for rule in self.rules:
            if any(literal.is_negative() for literal in rule.body):
                return False
        return True

    def is_semipositive(self) -> bool:
        """
        `program.is_positive()` returns True if `program` is a semipositive
        datalog program. A datalog program is semipositive if the only negated
        literals are on EDB predicates.
        """
        for rule in self.rules:
            for literal in rule.body:
                p = literal.atom.predicate
                if p in self.idb() and literal.is_negative():
                    return False
        return True

    def pdg(self) -> nx.DiGraph:
        """
        `program.pdg()` returns the predicate dependency graph (PDG) of
        `program`. Vertices in the PDG are predicates in the program. There is
        an edge from predicate p to predicate q if there exists a rule of the
        form `p :- ..., q, ...`. The edge is labelled `negative` if `q` is
        negative. The edge is labelled `async` if the rule is `async`.
        """
        g = nx.DiGraph()
        g.add_nodes_from(self.predicates())

        for rule in self.rules:
            p = rule.head.predicate
            for literal in rule.body:
                q = literal.atom.predicate
                if p not in g[q]:
                    g.add_edge(q, p, negative=False, async=False)
                edge = g[q][p]
                edge['negative'] = edge['negative'] or literal.is_negative()
                edge['async'] = edge['async'] or rule.is_async()

        return g

    def deductive_pdg(self) -> nx.DiGraph:
        """
        `program.deductive_pdg()` returns the PDG for the deductive rules of
        dedalus program `program`.
        """
        deductive_rules = [rule for rule in self.rules if rule.is_deductive()]
        deductive_predicates = {rule.head.predicate for rule in deductive_rules}

        g = nx.DiGraph()
        g.add_nodes_from(deductive_predicates)
        for rule in deductive_rules:
            p = rule.head.predicate
            for literal in rule.body:
                q = literal.atom.predicate
                if q not in deductive_predicates:
                    continue

                if p not in g[q]:
                    g.add_edge(q, p, negative=False)
                edge = g[q][p]
                edge['negative'] = edge['negative'] or literal.is_negative()

        return g

    def _is_stratified(self, pdg: nx.DiGraph) -> bool:
        """
        `p.is_stratified(pdg)` returns whether `pdg` is stratified. A PDG is
        stratified if it does not contain any cycles that contain a negative
        edge.
        """
        # Compute the number of cycles in the original PDG.
        num_cycles = len(list(nx.simple_cycles(pdg)))

        # Compute the number of cycles in the PDG with all negative edges
        # removed.
        pdg_copy = pdg.copy()
        edges = pdg_copy.edges
        negative_edges = [edge for edge in edges if edges[edge]['negative']]
        pdg_copy.remove_edges_from(negative_edges)
        num_positive_cycles = len(list(nx.simple_cycles(pdg_copy)))

        # If a PDG has a cycle through a negative edge, then removing the
        # negative edge will reduce the number of cycles. Conversely, if a PDG
        # does not have any cycles that contain a negative edge, then every
        # cycle contains only positive edges. Thus, removing the negative edges
        # does not reduce the number of cycles.
        return num_cycles == num_positive_cycles

    def is_deductive_stratified(self) -> bool:
        """
        `program.is_stratified()` returns whether `program`'s deductive PDG is
        stratified.
        """
        return self._is_stratified(self.deductive_pdg())

    def is_stratified(self) -> bool:
        """
        `program.is_stratified()` returns whether `program`'s PDG is
        stratified.
        """
        return self._is_stratified(self.pdg())

    def has_guarded_asynchrony(self) -> bool:
        """
        `program.has_guarded_asynchrony()` returns whether `program` has
        guarded asynchrony. A dedalus program has guarded asynchrony if for
        every predicate `p` at the head of an asynchronous rule, there is a
        persitence rule of the form `p(X, Y, Z)@next :- p(X, Y, Z)`.
        """
        async_rules = [rule for rule in self.rules if rule.is_async()]
        async_predicates = {rule.head.predicate for rule in async_rules}

        guarded_predicates: Set[Predicate] = set()
        for rule in self.rules:
            if (rule.head.predicate in async_predicates and
                rule.is_inductive() and
                len(rule.body) == 1 and
                rule.head.terms == rule.body[0].atom.terms):
                guarded_predicates.add(rule.head.predicate)

        return async_predicates == guarded_predicates

    def is_dedalus_s(self) -> bool:
        """
        `program.is_dedalus_s()` returns whether `program` is a Dedalus^S
        program: a Dedalus program with persistent edb, guarded asynchrony, and
        a stratified PDG. We also disallow constant time rules.
        """
        constant_time_rules = [r for r in self.rules if r.is_constant_time()]
        return (self.edb() == self.persistent_edb() and
                self.has_guarded_asynchrony() and
                len(constant_time_rules) == 0 and
                self.is_stratified())
