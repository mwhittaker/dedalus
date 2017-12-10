import copy

import ast

def _atom_contains_location(atom: ast.Atom) -> bool:
    return any(term.is_location for term in atom.terms)

def desugar(program: ast.Program) -> ast.Program:
    program = copy.deepcopy(program)

    # If a rule doesn't have any explicit location specifiers, then we inject a
    # location specifier to the head of every atom in the rule. For example,
    # this rule:
    #
    #   p(X, Y) :- p(X, Z), q(Z, Y)
    #
    # is desugared into this rule:
    #
    #   p(#_L, X, Y) :- p(#_L, X, Z), q(#_L, Z, Y)
    #
    # The variable name `_L` begins with an underscore, so it is guaranteed not
    # to conflict with any of the constants or variables in the rule. If any
    # atom in the rule has an explicit location specifier, then the rule is
    # left unchanged.
    for rule in program.rules:
        atoms = [rule.head] + [literal.atom for literal in rule.body]
        if any(_atom_contains_location(atom) for atom in atoms):
            continue
        L = ast.Variable("_L", is_location=True)
        for atom in atoms:
            atom.terms.insert(0, L)

    return program
