"""Tests for the sets module."""

import pytest
from discrete_math import sets


def test_union():
    """Test set union."""
    result = sets.union({1, 2}, {2, 3}, {3, 4})
    assert result == {1, 2, 3, 4}


def test_intersection():
    """Test set intersection."""
    result = sets.intersection({1, 2, 3}, {2, 3, 4}, {2, 3, 5})
    assert result == {2, 3}


def test_difference():
    """Test set difference."""
    result = sets.difference({1, 2, 3}, {2, 3, 4})
    assert result == {1}


def test_symmetric_difference():
    """Test symmetric difference."""
    result = sets.symmetric_difference({1, 2, 3}, {2, 3, 4})
    assert result == {1, 4}


def test_complement():
    """Test set complement."""
    result = sets.complement({1, 2}, {1, 2, 3, 4, 5})
    assert result == {3, 4, 5}


def test_power_set():
    """Test power set generation."""
    result = sets.power_set({1, 2})
    assert len(result) == 4


def test_cartesian_product():
    """Test Cartesian product."""
    result = sets.cartesian_product({1, 2}, {'a', 'b'})
    assert len(result) == 4
    assert (1, 'a') in result


def test_is_subset():
    """Test subset checking."""
    assert sets.is_subset({1, 2}, {1, 2, 3})
    assert not sets.is_subset({1, 4}, {1, 2, 3})


def test_is_disjoint():
    """Test disjoint checking."""
    assert sets.is_disjoint({1, 2}, {3, 4})
    assert not sets.is_disjoint({1, 2}, {2, 3})


def test_partition():
    """Test partition checking."""
    assert sets.partition({1, 2, 3, 4}, {1, 2}, {3}, {4})
    assert not sets.partition({1, 2, 3}, {1, 2}, {2, 3})
