"""
Number Theory Module
===================

Provides number theory utilities including GCD, LCM, primality testing,
and modular arithmetic operations.
"""

import math
from typing import List, Dict, Tuple


def gcd(a: int, b: int) -> int:
    """
    Calculate the greatest common divisor using Euclidean algorithm.
    
    Args:
        a: First integer
        b: Second integer
    
    Returns:
        GCD of a and b
    
    Example:
        >>> gcd(48, 18)
        6
        >>> gcd(17, 19)
        1
    """
    return math.gcd(abs(a), abs(b))


def lcm(a: int, b: int) -> int:
    """
    Calculate the least common multiple.
    
    Args:
        a: First integer
        b: Second integer
    
    Returns:
        LCM of a and b
    
    Example:
        >>> lcm(12, 18)
        36
        >>> lcm(7, 5)
        35
    """
    if a == 0 or b == 0:
        return 0
    return abs(a * b) // gcd(a, b)


def extended_gcd(a: int, b: int) -> Tuple[int, int, int]:
    """
    Extended Euclidean algorithm.
    
    Returns gcd(a, b) and coefficients x, y such that ax + by = gcd(a, b).
    
    Args:
        a: First integer
        b: Second integer
    
    Returns:
        Tuple (gcd, x, y)
    
    Example:
        >>> extended_gcd(30, 20)
        (10, 1, -1)  # 30*1 + 20*(-1) = 10
    """
    if b == 0:
        return (a, 1, 0)
    
    gcd_val, x1, y1 = extended_gcd(b, a % b)
    x = y1
    y = x1 - (a // b) * y1
    
    return (gcd_val, x, y)


def is_prime(n: int) -> bool:
    """
    Check if a number is prime.
    
    Args:
        n: Integer to check
    
    Returns:
        True if n is prime, False otherwise
    
    Example:
        >>> is_prime(17)
        True
        >>> is_prime(18)
        False
    """
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    
    # Check odd divisors up to sqrt(n)
    for i in range(3, int(math.sqrt(n)) + 1, 2):
        if n % i == 0:
            return False
    
    return True


def prime_factorization(n: int) -> Dict[int, int]:
    """
    Find the prime factorization of a number.
    
    Args:
        n: Positive integer to factorize
    
    Returns:
        Dictionary mapping primes to their exponents
    
    Example:
        >>> prime_factorization(60)
        {2: 2, 3: 1, 5: 1}  # 60 = 2^2 * 3^1 * 5^1
    """
    if n < 2:
        return {}
    
    factors = {}
    d = 2
    
    while d * d <= n:
        while n % d == 0:
            factors[d] = factors.get(d, 0) + 1
            n //= d
        d += 1
    
    if n > 1:
        factors[n] = factors.get(n, 0) + 1
    
    return factors


def sieve_of_eratosthenes(n: int) -> List[int]:
    """
    Generate all prime numbers up to n using Sieve of Eratosthenes.
    
    Args:
        n: Upper limit
    
    Returns:
        List of all primes <= n
    
    Example:
        >>> sieve_of_eratosthenes(20)
        [2, 3, 5, 7, 11, 13, 17, 19]
    """
    if n < 2:
        return []
    
    is_prime_arr = [True] * (n + 1)
    is_prime_arr[0] = is_prime_arr[1] = False
    
    for i in range(2, int(math.sqrt(n)) + 1):
        if is_prime_arr[i]:
            for j in range(i * i, n + 1, i):
                is_prime_arr[j] = False
    
    return [i for i in range(n + 1) if is_prime_arr[i]]


def mod_inverse(a: int, m: int) -> int:
    """
    Find modular multiplicative inverse of a modulo m.
    
    Returns x such that (a * x) % m == 1.
    
    Args:
        a: Number to find inverse of
        m: Modulus
    
    Returns:
        Modular inverse
    
    Raises:
        ValueError: If inverse doesn't exist (when gcd(a, m) != 1)
    
    Example:
        >>> mod_inverse(3, 11)
        4  # Because (3 * 4) % 11 == 1
    """
    g, x, _ = extended_gcd(a, m)
    
    if g != 1:
        raise ValueError(f"Modular inverse doesn't exist (gcd({a}, {m}) != 1)")
    
    return x % m


def mod_exp(base: int, exp: int, mod: int) -> int:
    """
    Compute (base^exp) % mod efficiently using binary exponentiation.
    
    Args:
        base: Base number
        exp: Exponent
        mod: Modulus
    
    Returns:
        (base^exp) % mod
    
    Example:
        >>> mod_exp(2, 10, 1000)
        24
        >>> mod_exp(3, 100, 7)
        4
    """
    return pow(base, exp, mod)


def euler_totient(n: int) -> int:
    """
    Calculate Euler's totient function φ(n).
    
    φ(n) counts positive integers up to n that are coprime to n.
    
    Args:
        n: Positive integer
    
    Returns:
        φ(n)
    
    Example:
        >>> euler_totient(9)
        6  # Numbers coprime to 9: 1, 2, 4, 5, 7, 8
        >>> euler_totient(10)
        4  # Numbers coprime to 10: 1, 3, 7, 9
    """
    if n <= 0:
        return 0
    
    result = n
    p = 2
    
    while p * p <= n:
        if n % p == 0:
            while n % p == 0:
                n //= p
            result -= result // p
        p += 1
    
    if n > 1:
        result -= result // n
    
    return result


def chinese_remainder_theorem(remainders: List[int], moduli: List[int]) -> int:
    """
    Solve system of congruences using Chinese Remainder Theorem.
    
    Args:
        remainders: List of remainders [a1, a2, ...]
        moduli: List of moduli [m1, m2, ...]
    
    Returns:
        Solution x such that x ≡ ai (mod mi) for all i
    
    Raises:
        ValueError: If moduli are not pairwise coprime
    
    Example:
        >>> chinese_remainder_theorem([2, 3, 2], [3, 5, 7])
        23  # 23 ≡ 2 (mod 3), 23 ≡ 3 (mod 5), 23 ≡ 2 (mod 7)
    """
    if len(remainders) != len(moduli):
        raise ValueError("Remainders and moduli lists must have same length")
    
    # Check if moduli are pairwise coprime
    for i in range(len(moduli)):
        for j in range(i + 1, len(moduli)):
            if gcd(moduli[i], moduli[j]) != 1:
                raise ValueError("Moduli must be pairwise coprime")
    
    total_mod = 1
    for m in moduli:
        total_mod *= m
    
    result = 0
    for remainder, modulus in zip(remainders, moduli):
        partial_product = total_mod // modulus
        result += remainder * mod_inverse(partial_product, modulus) * partial_product
    
    return result % total_mod


def is_coprime(a: int, b: int) -> bool:
    """
    Check if two numbers are coprime (gcd = 1).
    
    Args:
        a: First integer
        b: Second integer
    
    Returns:
        True if a and b are coprime, False otherwise
    
    Example:
        >>> is_coprime(15, 28)
        True
        >>> is_coprime(15, 25)
        False
    """
    return gcd(a, b) == 1


def divisors(n: int) -> List[int]:
    """
    Find all divisors of a number.
    
    Args:
        n: Positive integer
    
    Returns:
        Sorted list of all divisors
    
    Example:
        >>> divisors(12)
        [1, 2, 3, 4, 6, 12]
    """
    if n <= 0:
        return []
    
    divs = []
    for i in range(1, int(math.sqrt(n)) + 1):
        if n % i == 0:
            divs.append(i)
            if i != n // i:
                divs.append(n // i)
    
    return sorted(divs)


def sum_of_divisors(n: int) -> int:
    """
    Calculate sum of all divisors of n.
    
    Args:
        n: Positive integer
    
    Returns:
        Sum of divisors
    
    Example:
        >>> sum_of_divisors(12)
        28  # 1 + 2 + 3 + 4 + 6 + 12
    """
    return sum(divisors(n))


def is_perfect_number(n: int) -> bool:
    """
    Check if n is a perfect number (equals sum of its proper divisors).
    
    Args:
        n: Positive integer
    
    Returns:
        True if n is perfect, False otherwise
    
    Example:
        >>> is_perfect_number(6)
        True  # 6 = 1 + 2 + 3
        >>> is_perfect_number(28)
        True  # 28 = 1 + 2 + 4 + 7 + 14
    """
    if n <= 1:
        return False
    return sum_of_divisors(n) - n == n


__all__ = [
    'gcd',
    'lcm',
    'extended_gcd',
    'is_prime',
    'prime_factorization',
    'sieve_of_eratosthenes',
    'mod_inverse',
    'mod_exp',
    'euler_totient',
    'chinese_remainder_theorem',
    'is_coprime',
    'divisors',
    'sum_of_divisors',
    'is_perfect_number',
]
