"""
Sets Module
===========

Provides functions for set theory operations including union, intersection,
power sets, Cartesian products, and set properties.
"""

from typing import Set, List, Tuple, FrozenSet, Any
from itertools import product, combinations


def union(*sets: Set) -> Set:
    """
    Return the union of multiple sets.
    
    Args:
        *sets: Variable number of sets
    
    Returns:
        Union of all input sets
    
    Example:
        >>> union({1, 2}, {2, 3}, {3, 4})
        {1, 2, 3, 4}
    """
    if not sets:
        return set()
    result = sets[0].copy()
    for s in sets[1:]:
        result = result.union(s)
    return result


def intersection(*sets: Set) -> Set:
    """
    Return the intersection of multiple sets.
    
    Args:
        *sets: Variable number of sets
    
    Returns:
        Intersection of all input sets
    
    Example:
        >>> intersection({1, 2, 3}, {2, 3, 4}, {2, 3, 5})
        {2, 3}
    """
    if not sets:
        return set()
    result = sets[0].copy()
    for s in sets[1:]:
        result = result.intersection(s)
    return result


def difference(set_a: Set, set_b: Set) -> Set:
    """
    Return the difference of two sets (elements in A but not in B).
    
    Args:
        set_a: First set
        set_b: Second set
    
    Returns:
        Set difference A - B
    
    Example:
        >>> difference({1, 2, 3}, {2, 3, 4})
        {1}
    """
    return set_a.difference(set_b)


def symmetric_difference(set_a: Set, set_b: Set) -> Set:
    """
    Return the symmetric difference of two sets (elements in A or B but not both).
    
    Args:
        set_a: First set
        set_b: Second set
    
    Returns:
        Symmetric difference A △ B
    
    Example:
        >>> symmetric_difference({1, 2, 3}, {2, 3, 4})
        {1, 4}
    """
    return set_a.symmetric_difference(set_b)


def complement(set_a: Set, universal_set: Set) -> Set:
    """
    Return the complement of a set with respect to a universal set.
    
    Args:
        set_a: Set to complement
        universal_set: Universal set
    
    Returns:
        Complement of A in U (U - A)
    
    Example:
        >>> complement({1, 2}, {1, 2, 3, 4, 5})
        {3, 4, 5}
    """
    return universal_set.difference(set_a)


def power_set(s: Set) -> Set[FrozenSet]:
    """
    Return the power set (set of all subsets) of a given set.
    
    Args:
        s: Input set
    
    Returns:
        Power set as a set of frozen sets
    
    Example:
        >>> power_set({1, 2})
        {frozenset(), frozenset({1}), frozenset({2}), frozenset({1, 2})}
    """
    s_list = list(s)
    result = set()
    
    for i in range(len(s_list) + 1):
        for subset in combinations(s_list, i):
            result.add(frozenset(subset))
    
    return result


def cartesian_product(set_a: Set, set_b: Set) -> Set[Tuple]:
    """
    Return the Cartesian product of two sets (A × B).
    
    Args:
        set_a: First set
        set_b: Second set
    
    Returns:
        Set of ordered pairs (a, b) where a ∈ A and b ∈ B
    
    Example:
        >>> cartesian_product({1, 2}, {'a', 'b'})
        {(1, 'a'), (1, 'b'), (2, 'a'), (2, 'b')}
    """
    return set(product(set_a, set_b))


def cartesian_product_n(*sets: Set) -> Set[Tuple]:
    """
    Return the Cartesian product of n sets.
    
    Args:
        *sets: Variable number of sets
    
    Returns:
        Set of n-tuples
    
    Example:
        >>> cartesian_product_n({1, 2}, {'a', 'b'}, {True, False})
        {(1, 'a', True), (1, 'a', False), ...}
    """
    if not sets:
        return set()
    return set(product(*sets))


def is_subset(set_a: Set, set_b: Set) -> bool:
    """
    Check if set_a is a subset of set_b (A ⊆ B).
    
    Args:
        set_a: First set
        set_b: Second set
    
    Returns:
        True if A ⊆ B, False otherwise
    
    Example:
        >>> is_subset({1, 2}, {1, 2, 3})
        True
    """
    return set_a.issubset(set_b)


def is_proper_subset(set_a: Set, set_b: Set) -> bool:
    """
    Check if set_a is a proper subset of set_b (A ⊂ B).
    
    Args:
        set_a: First set
        set_b: Second set
    
    Returns:
        True if A ⊂ B (A is subset but not equal), False otherwise
    
    Example:
        >>> is_proper_subset({1, 2}, {1, 2, 3})
        True
        >>> is_proper_subset({1, 2}, {1, 2})
        False
    """
    return set_a < set_b


def is_superset(set_a: Set, set_b: Set) -> bool:
    """
    Check if set_a is a superset of set_b (A ⊇ B).
    
    Args:
        set_a: First set
        set_b: Second set
    
    Returns:
        True if A ⊇ B, False otherwise
    
    Example:
        >>> is_superset({1, 2, 3}, {1, 2})
        True
    """
    return set_a.issuperset(set_b)


def is_disjoint(set_a: Set, set_b: Set) -> bool:
    """
    Check if two sets are disjoint (have no common elements).
    
    Args:
        set_a: First set
        set_b: Second set
    
    Returns:
        True if A ∩ B = ∅, False otherwise
    
    Example:
        >>> is_disjoint({1, 2}, {3, 4})
        True
    """
    return set_a.isdisjoint(set_b)


def cardinality(s: Set) -> int:
    """
    Return the cardinality (number of elements) of a set.
    
    Args:
        s: Input set
    
    Returns:
        Number of elements in the set
    
    Example:
        >>> cardinality({1, 2, 3, 4})
        4
    """
    return len(s)


def partition(s: Set, *subsets: Set) -> bool:
    """
    Check if the given subsets form a partition of set s.
    
    A partition must satisfy:
    1. All subsets are non-empty
    2. Subsets are pairwise disjoint
    3. Union of all subsets equals s
    
    Args:
        s: The set to partition
        *subsets: Variable number of subsets
    
    Returns:
        True if subsets form a partition, False otherwise
    
    Example:
        >>> partition({1, 2, 3, 4}, {1, 2}, {3}, {4})
        True
    """
    if not subsets:
        return False
    
    # Check all subsets are non-empty
    if any(len(subset) == 0 for subset in subsets):
        return False
    
    # Check pairwise disjoint
    for i, subset_i in enumerate(subsets):
        for j, subset_j in enumerate(subsets):
            if i < j and not is_disjoint(subset_i, subset_j):
                return False
    
    # Check union equals s
    return union(*subsets) == s


def set_builder(predicate, universal_set: Set) -> Set:
    """
    Create a set using set-builder notation.
    
    Args:
        predicate: Function that returns True for elements to include
        universal_set: Universal set to filter from
    
    Returns:
        Set of elements satisfying the predicate
    
    Example:
        >>> set_builder(lambda x: x % 2 == 0, {1, 2, 3, 4, 5, 6})
        {2, 4, 6}
    """
    return {x for x in universal_set if predicate(x)}


def are_equal(set_a: Set, set_b: Set) -> bool:
    """
    Check if two sets are equal.
    
    Args:
        set_a: First set
        set_b: Second set
    
    Returns:
        True if sets are equal, False otherwise
    
    Example:
        >>> are_equal({1, 2, 3}, {3, 2, 1})
        True
    """
    return set_a == set_b


def power_set_cardinality(s: Set) -> int:
    """
    Return the cardinality of the power set without generating it.
    
    Args:
        s: Input set
    
    Returns:
        Number of subsets (2^|s|)
    
    Example:
        >>> power_set_cardinality({1, 2, 3})
        8
    """
    return 2 ** len(s)


__all__ = [
    'union',
    'intersection',
    'difference',
    'symmetric_difference',
    'complement',
    'power_set',
    'cartesian_product',
    'cartesian_product_n',
    'is_subset',
    'is_proper_subset',
    'is_superset',
    'is_disjoint',
    'cardinality',
    'partition',
    'set_builder',
    'are_equal',
    'power_set_cardinality',
]
