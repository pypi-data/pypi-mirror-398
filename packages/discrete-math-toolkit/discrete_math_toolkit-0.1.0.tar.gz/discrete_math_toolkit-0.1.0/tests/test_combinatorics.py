"""Tests for the combinatorics module."""

import pytest
from discrete_math import combinatorics


def test_factorial():
    """Test factorial calculation."""
    assert combinatorics.factorial(5) == 120
    assert combinatorics.factorial(0) == 1


def test_permutations():
    """Test permutations calculation."""
    assert combinatorics.permutations(5, 2) == 20
    assert combinatorics.permutations(5) == 120


def test_combinations():
    """Test combinations calculation."""
    assert combinatorics.combinations(5, 2) == 10
    assert combinatorics.combinations(10, 3) == 120


def test_binomial_coefficient():
    """Test binomial coefficient."""
    assert combinatorics.binomial_coefficient(5, 2) == 10
    assert combinatorics.binomial_coefficient(6, 3) == 20


def test_pascals_triangle():
    """Test Pascal's triangle generation."""
    triangle = combinatorics.pascals_triangle(4)
    assert len(triangle) == 5
    assert triangle[4] == [1, 4, 6, 4, 1]


def test_catalan_number():
    """Test Catalan numbers."""
    assert combinatorics.catalan_number(3) == 5
    assert combinatorics.catalan_number(4) == 14


def test_fibonacci():
    """Test Fibonacci sequence."""
    assert combinatorics.fibonacci(6) == 8
    assert combinatorics.fibonacci(10) == 55


def test_derangements():
    """Test derangements calculation."""
    assert combinatorics.derangements(3) == 2
    assert combinatorics.derangements(4) == 9
