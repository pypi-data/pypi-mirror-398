"""
Relations Module
===============

Provides functions for working with binary relations, checking properties,
and computing closures.
"""

from typing import Set, Tuple, Dict, List
from itertools import product


Relation = Set[Tuple]


def is_reflexive(relation: Relation, domain: Set) -> bool:
    """
    Check if a relation is reflexive.
    
    A relation R on set A is reflexive if (a, a) ∈ R for all a ∈ A.
    
    Args:
        relation: Set of ordered pairs representing the relation
        domain: The domain set
    
    Returns:
        True if relation is reflexive, False otherwise
    
    Example:
        >>> is_reflexive({(1, 1), (2, 2), (3, 3)}, {1, 2, 3})
        True
    """
    for element in domain:
        if (element, element) not in relation:
            return False
    return True


def is_symmetric(relation: Relation) -> bool:
    """
    Check if a relation is symmetric.
    
    A relation R is symmetric if (a, b) ∈ R implies (b, a) ∈ R.
    
    Args:
        relation: Set of ordered pairs representing the relation
    
    Returns:
        True if relation is symmetric, False otherwise
    
    Example:
        >>> is_symmetric({(1, 2), (2, 1), (3, 3)})
        True
    """
    for a, b in relation:
        if (b, a) not in relation:
            return False
    return True


def is_antisymmetric(relation: Relation) -> bool:
    """
    Check if a relation is antisymmetric.
    
    A relation R is antisymmetric if (a, b) ∈ R and (b, a) ∈ R implies a = b.
    
    Args:
        relation: Set of ordered pairs representing the relation
    
    Returns:
        True if relation is antisymmetric, False otherwise
    
    Example:
        >>> is_antisymmetric({(1, 2), (2, 3), (1, 1)})
        True
    """
    for a, b in relation:
        if a != b and (b, a) in relation:
            return False
    return True


def is_transitive(relation: Relation) -> bool:
    """
    Check if a relation is transitive.
    
    A relation R is transitive if (a, b) ∈ R and (b, c) ∈ R implies (a, c) ∈ R.
    
    Args:
        relation: Set of ordered pairs representing the relation
    
    Returns:
        True if relation is transitive, False otherwise
    
    Example:
        >>> is_transitive({(1, 2), (2, 3), (1, 3)})
        True
    """
    for a, b in relation:
        for c, d in relation:
            if b == c and (a, d) not in relation:
                return False
    return True


def is_equivalence_relation(relation: Relation, domain: Set) -> bool:
    """
    Check if a relation is an equivalence relation.
    
    A relation is an equivalence relation if it is reflexive, symmetric, and transitive.
    
    Args:
        relation: Set of ordered pairs representing the relation
        domain: The domain set
    
    Returns:
        True if relation is an equivalence relation, False otherwise
    
    Example:
        >>> R = {(1, 1), (2, 2), (3, 3), (1, 2), (2, 1)}
        >>> is_equivalence_relation(R, {1, 2, 3})
        False
    """
    return (is_reflexive(relation, domain) and 
            is_symmetric(relation) and 
            is_transitive(relation))


def is_partial_order(relation: Relation, domain: Set) -> bool:
    """
    Check if a relation is a partial order.
    
    A relation is a partial order if it is reflexive, antisymmetric, and transitive.
    
    Args:
        relation: Set of ordered pairs representing the relation
        domain: The domain set
    
    Returns:
        True if relation is a partial order, False otherwise
    
    Example:
        >>> R = {(1, 1), (2, 2), (3, 3), (1, 2), (2, 3), (1, 3)}
        >>> is_partial_order(R, {1, 2, 3})
        True
    """
    return (is_reflexive(relation, domain) and 
            is_antisymmetric(relation) and 
            is_transitive(relation))


def reflexive_closure(relation: Relation, domain: Set) -> Relation:
    """
    Compute the reflexive closure of a relation.
    
    The reflexive closure adds all pairs (a, a) for a ∈ domain.
    
    Args:
        relation: Set of ordered pairs representing the relation
        domain: The domain set
    
    Returns:
        Reflexive closure as a set of ordered pairs
    
    Example:
        >>> reflexive_closure({(1, 2)}, {1, 2, 3})
        {(1, 2), (1, 1), (2, 2), (3, 3)}
    """
    closure = relation.copy()
    for element in domain:
        closure.add((element, element))
    return closure


def symmetric_closure(relation: Relation) -> Relation:
    """
    Compute the symmetric closure of a relation.
    
    The symmetric closure adds (b, a) for each (a, b) in the relation.
    
    Args:
        relation: Set of ordered pairs representing the relation
    
    Returns:
        Symmetric closure as a set of ordered pairs
    
    Example:
        >>> symmetric_closure({(1, 2), (2, 3)})
        {(1, 2), (2, 1), (2, 3), (3, 2)}
    """
    closure = relation.copy()
    for a, b in relation:
        closure.add((b, a))
    return closure


def transitive_closure(relation: Relation) -> Relation:
    """
    Compute the transitive closure of a relation using Warshall's algorithm.
    
    Args:
        relation: Set of ordered pairs representing the relation
    
    Returns:
        Transitive closure as a set of ordered pairs
    
    Example:
        >>> transitive_closure({(1, 2), (2, 3)})
        {(1, 2), (2, 3), (1, 3)}
    """
    closure = relation.copy()
    
    # Get all elements
    elements = set()
    for a, b in relation:
        elements.add(a)
        elements.add(b)
    
    # Warshall's algorithm
    changed = True
    while changed:
        changed = False
        new_pairs = set()
        for a, b in closure:
            for c, d in closure:
                if b == c and (a, d) not in closure:
                    new_pairs.add((a, d))
                    changed = True
        closure.update(new_pairs)
    
    return closure


def equivalence_classes(relation: Relation, domain: Set) -> List[Set]:
    """
    Compute equivalence classes for an equivalence relation.
    
    Args:
        relation: Set of ordered pairs representing the equivalence relation
        domain: The domain set
    
    Returns:
        List of equivalence classes (each class is a set)
    
    Example:
        >>> R = {(1,1), (2,2), (3,3), (1,2), (2,1)}
        >>> equivalence_classes(R, {1, 2, 3})
        [{1, 2}, {3}]
    """
    if not is_equivalence_relation(relation, domain):
        raise ValueError("Relation must be an equivalence relation")
    
    classes = []
    remaining = domain.copy()
    
    while remaining:
        element = remaining.pop()
        # Find all elements related to this element
        equiv_class = {element}
        for a, b in relation:
            if a == element and b in remaining:
                equiv_class.add(b)
                remaining.discard(b)
            elif b == element and a in remaining:
                equiv_class.add(a)
                remaining.discard(a)
        classes.append(equiv_class)
    
    return classes


def compose(relation1: Relation, relation2: Relation) -> Relation:
    """
    Compute the composition of two relations.
    
    R₁ ∘ R₂ = {(a, c) | ∃b: (a, b) ∈ R₂ and (b, c) ∈ R₁}
    
    Args:
        relation1: First relation (R₁)
        relation2: Second relation (R₂)
    
    Returns:
        Composition R₁ ∘ R₂
    
    Example:
        >>> R1 = {(1, 2), (2, 3)}
        >>> R2 = {(0, 1), (1, 2)}
        >>> compose(R1, R2)
        {(0, 2), (1, 3)}
    """
    composition = set()
    for a, b in relation2:
        for c, d in relation1:
            if b == c:
                composition.add((a, d))
    return composition


def inverse_relation(relation: Relation) -> Relation:
    """
    Compute the inverse of a relation.
    
    R⁻¹ = {(b, a) | (a, b) ∈ R}
    
    Args:
        relation: Set of ordered pairs representing the relation
    
    Returns:
        Inverse relation
    
    Example:
        >>> inverse_relation({(1, 2), (2, 3), (3, 4)})
        {(2, 1), (3, 2), (4, 3)}
    """
    return {(b, a) for a, b in relation}


def get_domain(relation: Relation) -> Set:
    """
    Get the domain of a relation.
    
    Args:
        relation: Set of ordered pairs representing the relation
    
    Returns:
        Set of all first elements
    
    Example:
        >>> get_domain({(1, 2), (3, 4), (1, 5)})
        {1, 3}
    """
    return {a for a, b in relation}


def get_range(relation: Relation) -> Set:
    """
    Get the range (codomain) of a relation.
    
    Args:
        relation: Set of ordered pairs representing the relation
    
    Returns:
        Set of all second elements
    
    Example:
        >>> get_range({(1, 2), (3, 4), (1, 5)})
        {2, 4, 5}
    """
    return {b for a, b in relation}


def relation_matrix(relation: Relation, domain: Set) -> List[List[int]]:
    """
    Convert a relation to its matrix representation.
    
    Args:
        relation: Set of ordered pairs representing the relation
        domain: The domain set
    
    Returns:
        Matrix representation (2D list) where M[i][j] = 1 if (i, j) ∈ R
    
    Example:
        >>> relation_matrix({(1, 2), (2, 3)}, {1, 2, 3})
        [[0, 1, 0], [0, 0, 1], [0, 0, 0]]
    """
    domain_list = sorted(domain)
    n = len(domain_list)
    matrix = [[0] * n for _ in range(n)]
    
    index_map = {elem: i for i, elem in enumerate(domain_list)}
    
    for a, b in relation:
        if a in index_map and b in index_map:
            matrix[index_map[a]][index_map[b]] = 1
    
    return matrix


__all__ = [
    'is_reflexive',
    'is_symmetric',
    'is_antisymmetric',
    'is_transitive',
    'is_equivalence_relation',
    'is_partial_order',
    'reflexive_closure',
    'symmetric_closure',
    'transitive_closure',
    'equivalence_classes',
    'compose',
    'inverse_relation',
    'get_domain',
    'get_range',
    'relation_matrix',
]
