"""Tests for the number_theory module."""

import pytest
from discrete_math import number_theory


def test_gcd():
    """Test GCD calculation."""
    assert number_theory.gcd(48, 18) == 6
    assert number_theory.gcd(17, 19) == 1


def test_lcm():
    """Test LCM calculation."""
    assert number_theory.lcm(12, 18) == 36
    assert number_theory.lcm(7, 5) == 35


def test_is_prime():
    """Test primality testing."""
    assert number_theory.is_prime(17)
    assert number_theory.is_prime(2)
    assert not number_theory.is_prime(18)
    assert not number_theory.is_prime(1)


def test_prime_factorization():
    """Test prime factorization."""
    result = number_theory.prime_factorization(60)
    assert result == {2: 2, 3: 1, 5: 1}


def test_sieve_of_eratosthenes():
    """Test prime sieve."""
    primes = number_theory.sieve_of_eratosthenes(20)
    assert primes == [2, 3, 5, 7, 11, 13, 17, 19]


def test_mod_inverse():
    """Test modular inverse."""
    assert number_theory.mod_inverse(3, 11) == 4
    assert (3 * 4) % 11 == 1


def test_mod_exp():
    """Test modular exponentiation."""
    assert number_theory.mod_exp(2, 10, 1000) == 24


def test_euler_totient():
    """Test Euler's totient function."""
    assert number_theory.euler_totient(9) == 6
    assert number_theory.euler_totient(10) == 4


def test_chinese_remainder_theorem():
    """Test Chinese Remainder Theorem."""
    result = number_theory.chinese_remainder_theorem([2, 3, 2], [3, 5, 7])
    assert result % 3 == 2
    assert result % 5 == 3
    assert result % 7 == 2


def test_divisors():
    """Test divisor finding."""
    assert number_theory.divisors(12) == [1, 2, 3, 4, 6, 12]


def test_is_perfect_number():
    """Test perfect number detection."""
    assert number_theory.is_perfect_number(6)
    assert number_theory.is_perfect_number(28)
    assert not number_theory.is_perfect_number(12)
