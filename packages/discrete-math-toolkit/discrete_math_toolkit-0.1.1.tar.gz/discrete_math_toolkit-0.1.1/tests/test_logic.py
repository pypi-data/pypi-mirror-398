"""Tests for the logic module."""

import pytest
from discrete_math import logic


def test_truth_table():
    """Test truth table generation."""
    table = logic.generate_truth_table("p AND q")
    assert len(table) == 4
    assert table[-1]['result'] == True  # Both True


def test_tautology():
    """Test tautology detection."""
    assert logic.is_tautology("p OR (NOT p)")
    assert not logic.is_tautology("p AND q")


def test_contradiction():
    """Test contradiction detection."""
    assert logic.is_contradiction("p AND (NOT p)")
    assert not logic.is_contradiction("p OR q")


def test_cnf_conversion():
    """Test CNF conversion."""
    result = logic.convert_to_cnf("p OR q")
    assert "p" in result and "q" in result


def test_dnf_conversion():
    """Test DNF conversion."""
    result = logic.convert_to_dnf("p AND q")
    assert "p" in result and "q" in result


def test_equivalence():
    """Test logical equivalence."""
    assert logic.are_equivalent("p >> q", "(~p) | q")
    assert not logic.are_equivalent("p AND q", "p OR q")


def test_evaluate():
    """Test expression evaluation."""
    assert logic.evaluate("p AND q", {"p": True, "q": True})
    assert not logic.evaluate("p AND q", {"p": True, "q": False})
