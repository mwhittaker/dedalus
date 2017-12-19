from collections import defaultdict
from copy import deepcopy
from itertools import product
from tabulate import tabulate
from typing import (Any, Callable, DefaultDict, Dict, FrozenSet, Generator,
                    List, NamedTuple, Optional, Set, Tuple)
import random

import networkx as nx

import asts


Relation = Set[Tuple[Any, ...]]
Database = Dict[asts.Predicate, Relation]
DefaultDatabase = DefaultDict[asts.Predicate, Relation]
AsyncBuffer = DefaultDict[int, DefaultDatabase]
Bindings = Dict[asts.Variable, str]
RandInt = Callable[[], int]


class Process(NamedTuple):
    program: asts.Program
    timestep: int
    database: Database
    async_buffer: AsyncBuffer
    randint: RandInt

    def __str__(self) -> str:
        timestep = f"timestep = {self.timestep}"

        relations = []
        for p in sorted(self.database):
            relations.append(p.x)
            relation = sorted(self.database[p])
            relations.append(tabulate(relation, tablefmt="psql"))
        database = "\n".join(relations)

        async_relations = []
        for t in sorted(self.async_buffer):
            for p in sorted(self.async_buffer[t]):
                async_relations.append(f"{p.x} (t = {t})")
                relation = sorted(self.async_buffer[t][p])
                async_relations.append(tabulate(relation, tablefmt="psql"))
        async_buffer = "\n".join(async_relations)

        return f"{timestep}\n\n\n{database}\n\n\n{async_buffer}"

def _empty_database(program: asts.Program) -> Database:
    return {p: set() for p in program.predicates()}

def _empty_default_database() -> DefaultDatabase:
    return defaultdict(set)

def _subst(atom: asts.Atom, bindings: Bindings) -> Tuple[Any, ...]:
    """
    `_subst` performs variable substituion in `atom` according to the variable
    bindings in `bindings`. If `atom` contains unbound variables, an exception
    is thrown. Some examples:

        bindings = {W: 'w', X: 'x', Y: 'y', Z: 'z'}
        _subst(p(X, Y, Z), bindings) == ('x', 'y', 'z')
        _subst(p(a, Y, Z), bindings) == ('a', 'y', 'z')
        _subst(p(a, b, Z), bindings) == ('a', 'b', 'z')
        _subst(p(a, b, c), bindings) == ('a', 'b', 'c')
    """
    values = []
    for term in atom.terms:
        if isinstance(term, asts.Constant):
            values.append(term.x)
        else:
            assert isinstance(term, asts.Variable)
            assert term in bindings
            values.append(bindings[term])
    return tuple(values)

def _unify(atoms: List[asts.Atom],
           tuples: List[Tuple[Any, ...]]) \
           -> Optional[Bindings]:
    """
    Consider the following rule which finds all the trianges in a graph `g`:

        triangles(X, Y, Z) :- g(X, Y), g(Y, Z), g(Z, A).

    Imagine we try to instantiate the body of the rule with the tuples (a, b),
    (b, c), and (c, a). In this case, the instantiation can succeed: X binds to
    a, Y binds to b, and Z binds to c.

    Now imagine we try to instantiate the body of the rule with the tuples (a,
    b), (b, c), (c, d). In this case, the instantiation fails. X must be both a
    and d which is impossible.

    `_unify` attempts to instantiate a set of atoms with the provided set of
    tuples. If the instantiation suceeds, the bindings produced are returned.
    If the instantiation fails, None is returned.
    """
    bindings: Bindings = {}
    assert len(atoms) == len(tuples), (atoms, tuples)
    for (atom, tuple_) in zip(atoms, tuples):
        assert len(atom.terms) == len(tuple_), (atom, tuple_)
        for (term, value) in zip(atom.terms, tuple_):
            if isinstance(term, asts.Constant):
                if term.x != value:
                    return None
            else:
                assert isinstance(term, asts.Variable)
                if term in bindings and bindings[term] != value:
                    return None
                bindings[term] = value
    return bindings

def _eval_rule(process: Process,
               rule: asts.Rule) \
               -> Generator[Tuple[Any, ...], None, None]:
    """
    `_eval_rule(process, rule)` generates all the tuples produced by evaluating
    the rule. For example, given the following rule:

        triangles(X, Y, Z) :- g(X, Y), g(Y, Z), g(Z, X).

    and a fully connected graph `g` on vertices a, b, and c, `_eval_rule` would
    return the tuples (a, b, c), (b, c, a), (c, a, b), (a, c, b), (c, b, a),
    and (b, a, c).
    """
    positive_atoms = [l.atom for l in rule.body if l.is_positive()]
    negative_atoms = [l.atom for l in rule.body if l.is_negative()]
    positive_predicates = [atom.predicate for atom in positive_atoms]
    negative_predicates = [atom.predicate for atom in negative_atoms]

    db = process.database
    positive_relations = [db[p] for p in positive_predicates]
    for tuples in product(*positive_relations):
        bindings = _unify(positive_atoms, tuples)
        if bindings is None:
            continue

        if any(_subst(a, bindings) in db[a.predicate] for a in negative_atoms):
            continue

        yield _subst(rule.head, bindings)

def _stratify(pdg: nx.DiGraph) -> List[nx.DiGraph]:
    """
    Given a stratifiable PDG `pdg`, `_stratify(pdg)` returns a list of strata.
    For example, consider the following datalog program:

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

    It's PDG looks like this:

         _________
        v         |
        b -> c -> a--.   _________
        |            |  v         |
        |            '> f -> g -> h
        v                    ^
        d -> e --------------'
        ^    |
        '----

    Running _stratify on this PDG will return a list of three graphs. The first
    will be the [a, b, c] subgraph. The second will be the [e, d] subgraph. The
    third graph will be the [f, g, h] subgraph.
    """
    components: List[FrozenSet[asts.Predicate]] = \
        [frozenset(c) for c in nx.strongly_connected_components(pdg)]
    components_by_node = {node: c for c in components for node in c}

    collapsed_pdg = nx.DiGraph()
    collapsed_pdg.add_nodes_from(components)
    for (src, dst) in pdg.edges:
        src_component = components_by_node[src]
        dst_component = components_by_node[dst]
        if src_component != dst_component:
            collapsed_pdg.add_edge(src_component, dst_component)

    stratification: List[nx.DiGraph] = []
    for nodes in nx.topological_sort(collapsed_pdg):
        g = pdg.copy()
        g.remove_nodes_from(set(pdg.nodes) - nodes)
        stratification.append(g)
    return stratification

def spawn(program: asts.Program, randint: RandInt = None) -> Process:
    """Spawn a program into a process."""
    database = _empty_database(program)
    async_buffer: AsyncBuffer = defaultdict(_empty_default_database)
    randint = randint or (lambda: random.randint(1, 10))
    return Process(program, 0, database, async_buffer, randint)

def step(process: Process) -> Process:
    """Perform a single step of a Dedalus program."""
    process = deepcopy(process)

    def is_constant_rule(rule):
        rule_type = rule.rule_type
        if isinstance(rule.rule_type, asts.ConstantTimeRule):
            return rule_type.time == process.timestep
        else:
            return False

    constant_rules = [r for r in process.program.rules if is_constant_rule(r)]
    deductive_rules = [r for r in process.program.rules if r.is_deductive()]
    inductive_rules = [r for r in process.program.rules if r.is_inductive()]
    async_rules = [r for r in process.program.rules if r.is_async()]

    db = process.database

    # Async buffer.
    for (p, r) in db.items():
        db[p] = process.async_buffer[process.timestep][p]

    # Constant rules.
    for rule in constant_rules:
        for tuple_ in _eval_rule(process, rule):
            db[rule.head.predicate].add(tuple_)

    # Deductive rules.
    for strata in _stratify(process.program.deductive_pdg()):
        strata_rules = [r for r in deductive_rules
                          if r.head.predicate in strata.nodes]

        data_changed = True
        while data_changed:
            data_changed = False
            for rule in strata_rules:
                tuples = set(_eval_rule(process, rule))
                if len(tuples - db[rule.head.predicate]) != 0:
                    data_changed = True
                db[rule.head.predicate] |= tuples

    # Inductive rules.
    next_timestep = process.timestep + 1
    for rule in inductive_rules:
        p = rule.head.predicate
        tuples = set(_eval_rule(process, rule))
        process.async_buffer[next_timestep][p] |= tuples

    # Async rules.
    for rule in async_rules:
        for tuple_ in _eval_rule(process, rule):
            p = rule.head.predicate
            async_timestep = process.timestep + process.randint()
            process.async_buffer[async_timestep][p].add(tuple_)

    timestep = process.timestep
    process = process._replace(timestep=next_timestep)
    del process.async_buffer[timestep]
    return process

def run(process: Process, timesteps: int) -> Process:
    """Perform multiple steps of a Dedalus program."""
    for _ in range(timesteps):
        process = step(process)
    return process
