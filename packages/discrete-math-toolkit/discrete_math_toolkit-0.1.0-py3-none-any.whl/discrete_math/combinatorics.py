"""
Combinatorics Module
===================

Provides functions for combinatorial calculations including permutations,
combinations, binomial coefficients, and special sequences.
"""

import math
from typing import List, Iterator
from itertools import permutations as iter_permutations
from itertools import combinations as iter_combinations
from itertools import combinations_with_replacement


def factorial(n: int) -> int:
    """
    Calculate the factorial of n (n!).
    
    Args:
        n: Non-negative integer
    
    Returns:
        n! = n × (n-1) × ... × 2 × 1
    
    Example:
        >>> factorial(5)
        120
        >>> factorial(0)
        1
    """
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    return math.factorial(n)


def permutations(n: int, r: int = None) -> int:
    """
    Calculate the number of permutations P(n, r).
    
    P(n, r) = n! / (n - r)! represents the number of ways to arrange
    r items from n items where order matters.
    
    Args:
        n: Total number of items
        r: Number of items to arrange (default: n)
    
    Returns:
        Number of permutations
    
    Example:
        >>> permutations(5, 2)
        20
        >>> permutations(5)
        120
    """
    if r is None:
        r = n
    
    if n < 0 or r < 0:
        raise ValueError("n and r must be non-negative")
    
    if r > n:
        return 0
    
    return factorial(n) // factorial(n - r)


def combinations(n: int, r: int) -> int:
    """
    Calculate the number of combinations C(n, r) or binomial coefficient.
    
    C(n, r) = n! / (r! × (n - r)!) represents the number of ways to choose
    r items from n items where order doesn't matter.
    
    Args:
        n: Total number of items
        r: Number of items to choose
    
    Returns:
        Number of combinations
    
    Example:
        >>> combinations(5, 2)
        10
        >>> combinations(10, 3)
        120
    """
    if n < 0 or r < 0:
        raise ValueError("n and r must be non-negative")
    
    if r > n:
        return 0
    
    return factorial(n) // (factorial(r) * factorial(n - r))


def binomial_coefficient(n: int, k: int) -> int:
    """
    Calculate the binomial coefficient C(n, k).
    
    This is equivalent to combinations(n, k).
    
    Args:
        n: Total number of items
        k: Number of items to choose
    
    Returns:
        Binomial coefficient C(n, k)
    
    Example:
        >>> binomial_coefficient(5, 2)
        10
    """
    return combinations(n, k)


def permutations_with_repetition(n: int, r: int) -> int:
    """
    Calculate permutations with repetition.
    
    When items can be repeated, the number of r-permutations from n items is n^r.
    
    Args:
        n: Number of different items
        r: Number of positions to fill
    
    Returns:
        Number of permutations with repetition
    
    Example:
        >>> permutations_with_repetition(3, 2)
        9
    """
    if n < 0 or r < 0:
        raise ValueError("n and r must be non-negative")
    
    return n ** r


def combinations_with_repetition(n: int, r: int) -> int:
    """
    Calculate combinations with repetition (multicombinations).
    
    C_rep(n, r) = C(n + r - 1, r) represents the number of ways to choose
    r items from n types where repetition is allowed.
    
    Args:
        n: Number of different items
        r: Number of items to choose
    
    Returns:
        Number of combinations with repetition
    
    Example:
        >>> combinations_with_repetition(3, 2)
        6
    """
    if n < 0 or r < 0:
        raise ValueError("n and r must be non-negative")
    
    return combinations(n + r - 1, r)


def pascals_triangle(n: int) -> List[List[int]]:
    """
    Generate Pascal's triangle up to row n.
    
    Args:
        n: Number of rows to generate
    
    Returns:
        List of lists representing Pascal's triangle
    
    Example:
        >>> pascals_triangle(4)
        [[1], [1, 1], [1, 2, 1], [1, 3, 3, 1], [1, 4, 6, 4, 1]]
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    
    triangle = []
    for i in range(n + 1):
        row = [binomial_coefficient(i, j) for j in range(i + 1)]
        triangle.append(row)
    
    return triangle


def catalan_number(n: int) -> int:
    """
    Calculate the nth Catalan number.
    
    C_n = (1/(n+1)) × C(2n, n) = C(2n, n) - C(2n, n+1)
    
    Args:
        n: Index of Catalan number
    
    Returns:
        nth Catalan number
    
    Example:
        >>> catalan_number(3)
        5
        >>> catalan_number(4)
        14
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    
    return binomial_coefficient(2 * n, n) // (n + 1)


def stirling_second_kind(n: int, k: int) -> int:
    """
    Calculate Stirling number of the second kind S(n, k).
    
    S(n, k) represents the number of ways to partition n elements into k non-empty subsets.
    
    Args:
        n: Number of elements
        k: Number of subsets
    
    Returns:
        Stirling number of the second kind
    
    Example:
        >>> stirling_second_kind(4, 2)
        7
    """
    if n < 0 or k < 0:
        raise ValueError("n and k must be non-negative")
    
    if n == 0 and k == 0:
        return 1
    if n == 0 or k == 0:
        return 0
    if k > n:
        return 0
    if k == n:
        return 1
    
    # Dynamic programming approach
    dp = [[0] * (k + 1) for _ in range(n + 1)]
    dp[0][0] = 1
    
    for i in range(1, n + 1):
        for j in range(1, min(i, k) + 1):
            dp[i][j] = j * dp[i - 1][j] + dp[i - 1][j - 1]
    
    return dp[n][k]


def bell_number(n: int) -> int:
    """
    Calculate the nth Bell number.
    
    B_n represents the number of ways to partition a set of n elements.
    B_n = sum of S(n, k) for k from 0 to n.
    
    Args:
        n: Number of elements
    
    Returns:
        nth Bell number
    
    Example:
        >>> bell_number(3)
        5
        >>> bell_number(4)
        15
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    
    return sum(stirling_second_kind(n, k) for k in range(n + 1))


def derangements(n: int) -> int:
    """
    Calculate the number of derangements of n items.
    
    A derangement is a permutation where no element appears in its original position.
    D_n = n! × sum_{i=0}^{n} ((-1)^i / i!)
    
    Args:
        n: Number of items
    
    Returns:
        Number of derangements
    
    Example:
        >>> derangements(3)
        2
        >>> derangements(4)
        9
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    
    if n == 0:
        return 1
    if n == 1:
        return 0
    
    # Using recurrence: D_n = (n-1) × (D_{n-1} + D_{n-2})
    d_prev2 = 1  # D_0
    d_prev1 = 0  # D_1
    
    for i in range(2, n + 1):
        d_curr = (i - 1) * (d_prev1 + d_prev2)
        d_prev2 = d_prev1
        d_prev1 = d_curr
    
    return d_prev1


def multinomial_coefficient(*args: int) -> int:
    """
    Calculate the multinomial coefficient.
    
    (n; k1, k2, ..., km) = n! / (k1! × k2! × ... × km!)
    where n = k1 + k2 + ... + km
    
    Args:
        *args: Values k1, k2, ..., km
    
    Returns:
        Multinomial coefficient
    
    Example:
        >>> multinomial_coefficient(2, 3, 4)
        1260
    """
    if any(k < 0 for k in args):
        raise ValueError("All arguments must be non-negative")
    
    n = sum(args)
    result = factorial(n)
    
    for k in args:
        result //= factorial(k)
    
    return result


def fibonacci(n: int) -> int:
    """
    Calculate the nth Fibonacci number.
    
    F_0 = 0, F_1 = 1, F_n = F_{n-1} + F_{n-2}
    
    Args:
        n: Index of Fibonacci number
    
    Returns:
        nth Fibonacci number
    
    Example:
        >>> fibonacci(6)
        8
        >>> fibonacci(10)
        55
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    
    if n == 0:
        return 0
    if n == 1:
        return 1
    
    prev2, prev1 = 0, 1
    for _ in range(2, n + 1):
        curr = prev1 + prev2
        prev2, prev1 = prev1, curr
    
    return prev1


def generate_permutations(items: list, r: int = None) -> Iterator:
    """
    Generate all permutations of items.
    
    Args:
        items: List of items to permute
        r: Length of permutations (default: len(items))
    
    Yields:
        Tuples representing permutations
    
    Example:
        >>> list(generate_permutations([1, 2, 3], 2))
        [(1, 2), (1, 3), (2, 1), (2, 3), (3, 1), (3, 2)]
    """
    return iter_permutations(items, r)


def generate_combinations(items: list, r: int) -> Iterator:
    """
    Generate all combinations of items.
    
    Args:
        items: List of items to choose from
        r: Number of items to choose
    
    Yields:
        Tuples representing combinations
    
    Example:
        >>> list(generate_combinations([1, 2, 3, 4], 2))
        [(1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4)]
    """
    return iter_combinations(items, r)


def generate_combinations_with_repetition(items: list, r: int) -> Iterator:
    """
    Generate all combinations with repetition.
    
    Args:
        items: List of items to choose from
        r: Number of items to choose
    
    Yields:
        Tuples representing combinations with repetition
    
    Example:
        >>> list(generate_combinations_with_repetition([1, 2], 2))
        [(1, 1), (1, 2), (2, 2)]
    """
    return combinations_with_replacement(items, r)


__all__ = [
    'factorial',
    'permutations',
    'combinations',
    'binomial_coefficient',
    'permutations_with_repetition',
    'combinations_with_repetition',
    'pascals_triangle',
    'catalan_number',
    'stirling_second_kind',
    'bell_number',
    'derangements',
    'multinomial_coefficient',
    'fibonacci',
    'generate_permutations',
    'generate_combinations',
    'generate_combinations_with_repetition',
]
