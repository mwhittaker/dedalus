from collections import defaultdict
from copy import deepcopy
from itertools import product
from tabulate import tabulate
from typing import (Any, Callable, DefaultDict, Dict, Generator, List,
                    NamedTuple, Optional, Set, Tuple)
import random

import ast


Relation = Set[Tuple[Any, ...]]
Database = Dict[ast.Predicate, Relation]
DefaultDatabase = DefaultDict[ast.Predicate, Relation]
AsyncBuffer = DefaultDict[int, DefaultDatabase]
Bindings = Dict[ast.Variable, str]
RandInt = Callable[[], int]


class Process(NamedTuple):
    program: ast.Program
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

def _empty_database(program: ast.Program) -> Database:
    return {p: set() for p in program.predicates()}

def _empty_default_database() -> DefaultDatabase:
    return defaultdict(set)

def _subst(atom: ast.Atom, bindings: Bindings) -> Tuple[Any, ...]:
    values = []
    for term in atom.terms:
        if isinstance(term, ast.Constant):
            values.append(term.x)
        else:
            assert isinstance(term, ast.Variable)
            assert term in bindings
            values.append(bindings[term])
    return tuple(values)

def _unify(atoms: List[ast.Atom],
           tuples: List[Tuple[Any, ...]]) \
           -> Optional[Bindings]:
    bindings: Dict[ast.Variable, str] = {}
    for (atom, tuple_) in zip(atoms, tuples):
        for (term, value) in zip(atom.terms, tuple_):
            if isinstance(term, ast.Constant):
                if term.x != value:
                    return None
            else:
                assert isinstance(term, ast.Variable)
                if term in bindings and bindings[term] != value:
                    return None
                bindings[term] = value
    return bindings

def _eval_rule(process: Process,
               rule: ast.Rule) \
               -> Generator[Tuple[Any, ...], None, None]:
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

def spawn(program: ast.Program, randint: RandInt = None) -> Process:
    database = _empty_database(program)
    async_buffer: AsyncBuffer = defaultdict(_empty_default_database)
    randint = randint or (lambda: random.randint(1, 10))
    return Process(program, 0, database, async_buffer, randint)

def step(process: Process) -> Process:
    process = deepcopy(process)

    def is_constant_rule(rule):
        rule_type = rule.rule_type
        if isinstance(rule.rule_type, ast.ConstantTimeRule):
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
    data_changed = True
    while data_changed:
        data_changed = False
        for rule in deductive_rules:
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
    for _ in range(timesteps):
        process = step(process)
    return process
