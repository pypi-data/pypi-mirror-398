"""
Functions Module
===============

Provides utilities for analyzing mathematical functions and their properties.
"""

from typing import Set, Dict, Callable, Any, Tuple


def is_function(relation: Set[Tuple], domain: Set) -> bool:
    """
    Check if a relation is a function.
    
    A relation is a function if each element in the domain maps to exactly one element.
    
    Args:
        relation: Set of ordered pairs (x, y)
        domain: Domain set
    
    Returns:
        True if relation is a function, False otherwise
    
    Example:
        >>> is_function({(1, 2), (2, 3), (3, 4)}, {1, 2, 3})
        True
        >>> is_function({(1, 2), (1, 3)}, {1, 2})
        False
    """
    seen = set()
    for x, y in relation:
        if x in domain:
            if x in seen:
                return False
            seen.add(x)
    return seen == domain


def is_injective(relation: Set[Tuple]) -> bool:
    """
    Check if a function is injective (one-to-one).
    
    A function is injective if different inputs map to different outputs.
    
    Args:
        relation: Set of ordered pairs representing the function
    
    Returns:
        True if function is injective, False otherwise
    
    Example:
        >>> is_injective({(1, 2), (2, 3), (3, 4)})
        True
        >>> is_injective({(1, 2), (2, 2)})
        False
    """
    outputs = set()
    for x, y in relation:
        if y in outputs:
            return False
        outputs.add(y)
    return True


def is_surjective(relation: Set[Tuple], codomain: Set) -> bool:
    """
    Check if a function is surjective (onto).
    
    A function is surjective if every element in the codomain is mapped to.
    
    Args:
        relation: Set of ordered pairs representing the function
        codomain: Codomain set
    
    Returns:
        True if function is surjective, False otherwise
    
    Example:
        >>> is_surjective({(1, 'a'), (2, 'b')}, {'a', 'b'})
        True
        >>> is_surjective({(1, 'a'), (2, 'a')}, {'a', 'b'})
        False
    """
    outputs = {y for x, y in relation}
    return outputs == codomain


def is_bijective(relation: Set[Tuple], domain: Set, codomain: Set) -> bool:
    """
    Check if a function is bijective (one-to-one and onto).
    
    A function is bijective if it is both injective and surjective.
    
    Args:
        relation: Set of ordered pairs representing the function
        domain: Domain set
        codomain: Codomain set
    
    Returns:
        True if function is bijective, False otherwise
    
    Example:
        >>> is_bijective({(1, 'a'), (2, 'b')}, {1, 2}, {'a', 'b'})
        True
    """
    return (is_function(relation, domain) and 
            is_injective(relation) and 
            is_surjective(relation, codomain))


def compose_functions(f: Set[Tuple], g: Set[Tuple]) -> Set[Tuple]:
    """
    Compose two functions: (f ∘ g)(x) = f(g(x)).
    
    Args:
        f: First function as set of ordered pairs
        g: Second function as set of ordered pairs
    
    Returns:
        Composition f ∘ g as set of ordered pairs
    
    Example:
        >>> f = {(1, 2), (2, 3), (3, 4)}
        >>> g = {(0, 1), (1, 2), (2, 3)}
        >>> compose_functions(f, g)
        {(0, 2), (1, 3), (2, 4)}
    """
    # Convert to dictionaries for easier lookup
    f_dict = dict(f)
    g_dict = dict(g)
    
    composition = set()
    for x, y in g:
        if y in f_dict:
            composition.add((x, f_dict[y]))
    
    return composition


def inverse_function(relation: Set[Tuple], domain: Set, codomain: Set) -> Set[Tuple]:
    """
    Find the inverse of a bijective function.
    
    Args:
        relation: Set of ordered pairs representing the function
        domain: Domain set
        codomain: Codomain set
    
    Returns:
        Inverse function as set of ordered pairs
    
    Raises:
        ValueError: If function is not bijective
    
    Example:
        >>> inverse_function({(1, 'a'), (2, 'b')}, {1, 2}, {'a', 'b'})
        {('a', 1), ('b', 2)}
    """
    if not is_bijective(relation, domain, codomain):
        raise ValueError("Function must be bijective to have an inverse")
    
    return {(y, x) for x, y in relation}


def evaluate_function(func: Callable, *args: Any) -> Any:
    """
    Evaluate a function at given arguments.
    
    Args:
        func: Python callable function
        *args: Arguments to pass to the function
    
    Returns:
        Result of function evaluation
    
    Example:
        >>> evaluate_function(lambda x: x**2, 5)
        25
    """
    return func(*args)


def get_domain(relation: Set[Tuple]) -> Set:
    """
    Extract the domain from a function representation.
    
    Args:
        relation: Set of ordered pairs
    
    Returns:
        Domain set (all first elements)
    
    Example:
        >>> get_domain({(1, 2), (2, 3), (3, 4)})
        {1, 2, 3}
    """
    return {x for x, y in relation}


def get_range(relation: Set[Tuple]) -> Set:
    """
    Extract the range from a function representation.
    
    Args:
        relation: Set of ordered pairs
    
    Returns:
        Range set (all second elements)
    
    Example:
        >>> get_range({(1, 2), (2, 3), (3, 4)})
        {2, 3, 4}
    """
    return {y for x, y in relation}


def function_to_dict(relation: Set[Tuple]) -> Dict:
    """
    Convert a function from set of pairs to dictionary.
    
    Args:
        relation: Set of ordered pairs
    
    Returns:
        Dictionary representation
    
    Example:
        >>> function_to_dict({(1, 'a'), (2, 'b'), (3, 'c')})
        {1: 'a', 2: 'b', 3: 'c'}
    """
    return dict(relation)


def dict_to_function(d: Dict) -> Set[Tuple]:
    """
    Convert a dictionary to function as set of pairs.
    
    Args:
        d: Dictionary mapping inputs to outputs
    
    Returns:
        Function as set of ordered pairs
    
    Example:
        >>> dict_to_function({1: 'a', 2: 'b', 3: 'c'})
        {(1, 'a'), (2, 'b'), (3, 'c')}
    """
    return set(d.items())


__all__ = [
    'is_function',
    'is_injective',
    'is_surjective',
    'is_bijective',
    'compose_functions',
    'inverse_function',
    'evaluate_function',
    'get_domain',
    'get_range',
    'function_to_dict',
    'dict_to_function',
]
