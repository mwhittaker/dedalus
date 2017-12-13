from typing import Dict

import asts


def _fixed_arities(program: asts.Program):
    """
    The arity of every predicate in a dedalus program must be fixed. For
    example, the following program is ill-formed because `p` has both arity 1
    and 2:

        p(X, Y) :- p(X), p(Y)
    """
    arities: Dict[str, int] = {}
    for rule in program.rules:
        for atom in [rule.head] + [l.atom for l in rule.body]:
            p = atom.predicate.x
            arity = len(atom.terms)
            if p in arities and arities[p] != arity:
                msg = f'Predicate {p} has inconsistent arities.'
                raise ValueError(msg)
            else:
                arities[p] = arity

def _range_restricted(program: asts.Program):
    """
    A dedalus rule is range restricted if (1) every variable in the head of the
    rule appears in some positive literal in the body and (2) every variable in
    a negative literal in the body appears in some positive literal in the
    body. For example, this is a range restricted rule:

      p(X, Y, Z) :- q(X, Y), r(Y, Z), !s(Y).

    This rule is not range restricted because X and Y do not appear in a
    positive literal:

      p(X) :- !q(Y), r(Z).
    """
    def range_restricted_rule(rule: asts.Rule):
        positive_atoms = [l.atom for l in rule.body if l.is_positive()]
        negative_atoms = [l.atom for l in rule.body if l.is_negative()]
        head_vars = {v.x for v in rule.head.variables()}
        postive_vars = {v.x for a in positive_atoms for v in a.variables()}
        negative_vars = {v.x for a in negative_atoms for v in a.variables()}

        if not (head_vars <= postive_vars):
            unrestricted_head_vars = head_vars - postive_vars
            msg = (f'The head variables {unrestricted_head_vars} in the rule '
                   f'"{rule}" do not appear in any positive literal in the '
                   f'body of the rule.')
            raise ValueError(msg)

        if not (negative_vars <= postive_vars):
            unrestricted_body_vars = negative_vars - postive_vars
            msg = (f'The body variables {unrestricted_body_vars} in the rule '
                   f'"{rule}" do not appear in any positive literal in the '
                   f'body of the rule.')
            raise ValueError(msg)

    for rule in program.rules:
        range_restricted_rule(rule)

def _timestamp_restricted(program: asts.Program):
    """
    A dedalus rule is timestamp restricted if constant time rules have empty
    bodies. For example, the following rules are timestamp restricted:

        p(x)@42 :- .
        p(x, y)@42 :- .

    The following rules are not timestamp restricted:

        p(X)@42 :- p(X).
        p(x)@42 :- p(x).
    """
    for rule in program.rules:
        if rule.is_constant_time() and len(rule.body) != 0:
            msg = f'The constant time rule "{rule}" has a non-empty body.'
            raise ValueError(msg)

def _location_restricted(program: asts.Program):
    """
    A dedalus rule is location restricted if

      1. the first term of every atom is a location term,
      2. no other terms are location terms,
      3. the location of all body atoms are the same, and
      4. for deductive and inductive rules, the location of the head and body
         are the same.

    For example, the following rules are location restricted:

      p(#X) :- q(#X), r(#X). // Also with @next and @async.
      p(#a) :- q(#a), r(#a). // Also with @next and @async.
      p() :- q(), r(). // Desugars to p(#_L) :- q(#_L), r(#_L).
      p(#Y)@async :- q(#X, Y), r(#X, Z).

    The following rules are _NOT_ range restricted:

      p(#X) :- q(#X), r(#Y).
      p(#X) :- q(#X), r(#x).
      p(#Y) :- q(#X, Y), r(#X, Y).
      p(#Y)@next :- q(#X, Y), r(#X, Y).
    """
    def location_restricted_rule(rule: asts.Rule):
        for atom in [rule.head] + [l.atom for l in rule.body]:
            if len(atom.terms) == 0:
                msg = (f'Atom {atom} of rule "{rule}" does not have a '
                       f'location specifier.')
                raise ValueError(msg)

            if not atom.terms[0].is_location:
                msg = (f'The first term of atom {atom} of rule "{rule}" is '
                       f'not a location specifier.')
                raise ValueError(msg)

            if any(t.is_location for t in atom.terms[1:]):
                msg = (f'The atom {atom} of rule "{rule}" contains a location '
                        f'term that does not appear at the head of the atom.')
                raise ValueError(msg)

        head_location = rule.head.terms[0]
        body_locations = {l.atom.terms[0] for l in rule.body}
        locations = {head_location} | body_locations

        if len(body_locations) > 1:
            msg = (f'The body of rule "{rule}" contains multiple locations: '
                   f'{body_locations}.')
            raise ValueError(msg)

        if (rule.is_deductive() or rule.is_inductive()) and len(locations) != 1:
            msg = (f'The head and body of rule "{rule}" contain different '
                   f'locations. Only async rules are allowed to do this.')
            raise ValueError(msg)

    for rule in program.rules:
        location_restricted_rule(rule)

def typecheck(program: asts.Program) -> asts.Program:
    _fixed_arities(program)
    _range_restricted(program)
    _timestamp_restricted(program)
    _location_restricted(program)
    return program

def typechecks(program: asts.Program) -> bool:
    try:
        typecheck(program)
        return True
    except ValueError:
        return False
