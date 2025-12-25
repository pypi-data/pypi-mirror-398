"""
Discrete Math Toolkit
====================

A comprehensive Python package for automating discrete mathematics operations.

Modules:
    - logic: Propositional logic and truth tables
    - sets: Set theory operations
    - relations: Binary relations and properties
    - functions: Function analysis
    - combinatorics: Permutations, combinations, and counting
    - graphs: Graph theory and algorithms
    - number_theory: Number theory utilities

Author: CodewithTanzeel
License: MIT
"""

__version__ = "0.1.0"
__author__ = "CodewithTanzeel"

# Import main modules
from . import logic
from . import sets
from . import relations
from . import functions
from . import combinatorics
from . import graphs
from . import number_theory

__all__ = [
    "logic",
    "sets",
    "relations",
    "functions",
    "combinatorics",
    "graphs",
    "number_theory",
]
