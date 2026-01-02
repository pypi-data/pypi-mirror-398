"""
Logic Module
============

Provides functions for propositional logic operations, truth tables,
logical equivalences, and conversions to normal forms.
"""

from itertools import product
from typing import Dict, List, Tuple, Any
import sympy
from sympy import symbols, simplify_logic, to_cnf, to_dnf
from sympy.logic.boolalg import And, Or, Not, Implies, Equivalent


def generate_truth_table(expression: str) -> List[Dict[str, Any]]:
    """
    Generate a truth table for a given logical expression.
    
    Args:
        expression: Logical expression as string (e.g., "p AND q", "p IMPLIES q")
                   Supported operators: AND, OR, NOT, IMPLIES (->), IFF (<->), XOR
    
    Returns:
        List of dictionaries representing each row of the truth table
    
    Example:
        >>> generate_truth_table("p AND q")
        [{'p': False, 'q': False, 'result': False},
         {'p': False, 'q': True, 'result': False},
         {'p': True, 'q': False, 'result': False},
         {'p': True, 'q': True, 'result': True}]
    """
    # Parse expression and extract variables
    expr = _parse_expression(expression)
    variables = sorted(expr.free_symbols, key=lambda x: str(x))
    
    # Generate all combinations of truth values
    truth_table = []
    for values in product([False, True], repeat=len(variables)):
        row = dict(zip([str(v) for v in variables], values))
        # Substitute values and evaluate
        subs_dict = dict(zip(variables, values))
        result = bool(expr.subs(subs_dict))
        row['result'] = result
        truth_table.append(row)
    
    return truth_table


def is_tautology(expression: str) -> bool:
    """
    Check if a logical expression is a tautology (always true).
    
    Args:
        expression: Logical expression as string
    
    Returns:
        True if expression is a tautology, False otherwise
    
    Example:
        >>> is_tautology("p OR (NOT p)")
        True
    """
    truth_table = generate_truth_table(expression)
    return all(row['result'] for row in truth_table)


def is_contradiction(expression: str) -> bool:
    """
    Check if a logical expression is a contradiction (always false).
    
    Args:
        expression: Logical expression as string
    
    Returns:
        True if expression is a contradiction, False otherwise
    
    Example:
        >>> is_contradiction("p AND (NOT p)")
        True
    """
    truth_table = generate_truth_table(expression)
    return all(not row['result'] for row in truth_table)


def is_contingency(expression: str) -> bool:
    """
    Check if a logical expression is a contingency (sometimes true, sometimes false).
    
    Args:
        expression: Logical expression as string
    
    Returns:
        True if expression is contingent, False otherwise
    """
    return not (is_tautology(expression) or is_contradiction(expression))


def convert_to_cnf(expression: str) -> str:
    """
    Convert a logical expression to Conjunctive Normal Form (CNF).
    
    Args:
        expression: Logical expression as string
    
    Returns:
        Expression in CNF as string
    
    Example:
        >>> convert_to_cnf("(p OR q) IMPLIES r")
        '(~p | r) & (~q | r)'
    """
    expr = _parse_expression(expression)
    cnf = to_cnf(expr)
    return str(cnf)


def convert_to_dnf(expression: str) -> str:
    """
    Convert a logical expression to Disjunctive Normal Form (DNF).
    
    Args:
        expression: Logical expression as string
    
    Returns:
        Expression in DNF as string
    
    Example:
        >>> convert_to_dnf("(p AND q) OR (p AND r)")
        'p & (q | r)'
    """
    expr = _parse_expression(expression)
    dnf = to_dnf(expr)
    return str(dnf)


def are_equivalent(expr1: str, expr2: str) -> bool:
    """
    Check if two logical expressions are logically equivalent.
    
    Args:
        expr1: First logical expression
        expr2: Second logical expression
    
    Returns:
        True if expressions are equivalent, False otherwise
    
    Example:
        >>> are_equivalent("p IMPLIES q", "(NOT p) OR q")
        True
    """
    e1 = _parse_expression(expr1)
    e2 = _parse_expression(expr2)
    
    # Get all variables from both expressions
    vars1 = e1.free_symbols
    vars2 = e2.free_symbols
    all_vars = sorted(vars1.union(vars2), key=lambda x: str(x))
    
    # Check equivalence for all truth value combinations
    for values in product([False, True], repeat=len(all_vars)):
        subs_dict = dict(zip(all_vars, values))
        if bool(e1.subs(subs_dict)) != bool(e2.subs(subs_dict)):
            return False
    
    return True


def simplify(expression: str) -> str:
    """
    Simplify a logical expression.
    
    Args:
        expression: Logical expression as string
    
    Returns:
        Simplified expression as string
    
    Example:
        >>> simplify("(p AND p) OR (q AND True)")
        'p | q'
    """
    expr = _parse_expression(expression)
    simplified = simplify_logic(expr)
    return str(simplified)


def evaluate(expression: str, values: Dict[str, bool]) -> bool:
    """
    Evaluate a logical expression with given variable values.
    
    Args:
        expression: Logical expression as string
        values: Dictionary mapping variable names to boolean values
    
    Returns:
        Boolean result of evaluation
    
    Example:
        >>> evaluate("p AND q", {"p": True, "q": False})
        False
    """
    expr = _parse_expression(expression)
    # Convert string keys to symbols
    subs_dict = {symbols(k): v for k, v in values.items()}
    return bool(expr.subs(subs_dict))


def _parse_expression(expression: str):
    """
    Parse a string expression into a SymPy logic expression.
    
    Supported operators:
        - AND, &, ∧
        - OR, |, ∨
        - NOT, ~, ¬
        - IMPLIES, ->, →
        - IFF, <->, ↔
        - XOR, ⊕
    """
    # Replace text operators with symbols
    expr_str = expression.replace(" ", "")
    expr_str = expr_str.replace("AND", "&")
    expr_str = expr_str.replace("OR", "|")
    expr_str = expr_str.replace("NOT", "~")
    expr_str = expr_str.replace("IMPLIES", ">>")
    expr_str = expr_str.replace("->", ">>")
    expr_str = expr_str.replace("IFF", "<<>>")
    expr_str = expr_str.replace("<->", "<<>>")
    expr_str = expr_str.replace("XOR", "^")
    
    # Use sympy to parse the expression
    try:
        return sympy.sympify(expr_str)
    except Exception as e:
        raise ValueError(f"Invalid expression: {expression}. Error: {e}")


def get_minterms(expression: str) -> List[int]:
    """
    Get the minterms (rows where expression is True) from truth table.
    
    Args:
        expression: Logical expression as string
    
    Returns:
        List of minterm indices
    
    Example:
        >>> get_minterms("p OR q")
        [1, 2, 3]  # True for rows 1, 2, 3 (binary: 01, 10, 11)
    """
    truth_table = generate_truth_table(expression)
    minterms = []
    
    for i, row in enumerate(truth_table):
        if row['result']:
            minterms.append(i)
    
    return minterms


def get_maxterms(expression: str) -> List[int]:
    """
    Get the maxterms (rows where expression is False) from truth table.
    
    Args:
        expression: Logical expression as string
    
    Returns:
        List of maxterm indices
    
    Example:
        >>> get_maxterms("p OR q")
        [0]  # False only for row 0 (binary: 00)
    """
    truth_table = generate_truth_table(expression)
    maxterms = []
    
    for i, row in enumerate(truth_table):
        if not row['result']:
            maxterms.append(i)
    
    return maxterms


__all__ = [
    'generate_truth_table',
    'is_tautology',
    'is_contradiction',
    'is_contingency',
    'convert_to_cnf',
    'convert_to_dnf',
    'are_equivalent',
    'simplify',
    'evaluate',
    'get_minterms',
    'get_maxterms',
]
