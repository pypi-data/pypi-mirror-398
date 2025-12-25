# 🧮 Discrete Math Toolkit

**Your Python companion for discrete mathematics!**

Whether you're a student tackling homework, an educator creating examples, or a researcher exploring mathematical concepts, this toolkit automates the tedious calculations so you can focus on understanding the concepts.

## 🎯 What Can You Do With This?

### For Students 📚
- ✅ Verify your homework answers instantly
- ✅ Generate truth tables for logic assignments
- ✅ Calculate permutations and combinations without manual work
- ✅ Visualize graph algorithms step-by-step
- ✅ Check if your relations are reflexive, symmetric, or transitive

### For Educators 👨‍🏫
- ✅ Generate examples and test cases quickly
- ✅ Create consistent problem sets
- ✅ Demonstrate algorithms programmatically
- ✅ Build interactive demonstrations

### For Developers 🚀
- ✅ Integrate discrete math operations into your applications
- ✅ Build educational tools and games
- ✅ Prototype algorithms before optimization
- ✅ Add mathematical validation to your systems

## 📦 Installation

Super simple! Just one command:

```bash
pip install discrete-math-toolkit
```

That's it! No complicated setup, no additional dependencies to worry about.

## 🚀 Quick Start - Get Results in 30 Seconds

```python
from discrete_math import logic, sets, combinatorics

# Example 1: Check if a logical statement is always true
print(logic.is_tautology("p OR (NOT p)"))  # True - this is always true!

# Example 2: Find what elements two sets share
students_in_math = {1, 2, 3, 4, 5}
students_in_cs = {3, 4, 5, 6, 7}
print(sets.intersection(students_in_math, students_in_cs))  # {3, 4, 5}

# Example 3: How many ways can you choose 3 people from 10?
print(combinatorics.combinations(10, 3))  # 120 different ways!
```

## 📚 Complete Feature Guide

---

## 1️⃣ Logic Module - Work with Logical Statements

**What it does:** Analyze logical expressions, generate truth tables, and check for tautologies or contradictions.

### 🎓 Real-World Use Case: Validating Circuit Logic

Imagine you're designing a digital circuit and need to verify that your logic gates always produce the correct output.

```python
from discrete_math.logic import *

# Example 1: Is this statement always true? (Tautology)
statement = "p OR (NOT p)"  # The law of excluded middle
print(is_tautology(statement))  # True - always true regardless of p!

# Example 2: Generate a complete truth table
# Useful for homework or understanding complex expressions
table = generate_truth_table("(p AND q) OR (NOT r)")
print(table)
# Shows all possible combinations of p, q, r and the result

# Example 3: Check if something is always false (Contradiction)
print(is_contradiction("p AND (NOT p)"))  # True - impossible!

# Example 4: Convert to Conjunctive Normal Form (CNF)
# Useful for SAT solvers and formal verification
cnf_form = convert_to_cnf("(p OR q) AND (r OR s)")
print(cnf_form)

# Example 5: Convert to Disjunctive Normal Form (DNF)
dnf_form = convert_to_dnf("p IMPLIES q")
print(dnf_form)

# Example 6: Check if two expressions are logically equivalent
expr1 = "p IMPLIES q"
expr2 = "(NOT p) OR q"
print(are_equivalent(expr1, expr2))  # True - these mean the same thing!
```

**💡 Student Tip:** Use `generate_truth_table()` to verify your homework before submitting!

---

## 2️⃣ Sets Module - Master Set Operations

**What it does:** Perform all standard set operations like union, intersection, and power sets.

### 🎓 Real-World Use Case: Analyzing Student Enrollment

```python
from discrete_math.sets import *

# Students enrolled in different courses
math_students = {101, 102, 103, 104, 105}
cs_students = {103, 104, 105, 106, 107}
physics_students = {102, 104, 106, 108}

# Example 1: Find students taking both Math and CS
both_math_cs = intersection(math_students, cs_students)
print(f"Students in both Math & CS: {both_math_cs}")  # {103, 104, 105}

# Example 2: Find all students across all courses
all_students = union(union(math_students, cs_students), physics_students)
print(f"Total unique students: {len(all_students)}")  # 8 students

# Example 3: Find students only in Math (not in CS)
only_math = difference(math_students, cs_students)
print(f"Only Math students: {only_math}")  # {101, 102}

# Example 4: Find students in either Math or CS, but not both
either_not_both = symmetric_difference(math_students, cs_students)
print(f"Exclusively one course: {either_not_both}")  # {101, 102, 106, 107}

# Example 5: Generate all possible subsets (Power Set)
small_group = {1, 2, 3}
all_subsets = power_set(small_group)
print(f"All possible team combinations: {all_subsets}")
# Returns: {∅, {1}, {2}, {3}, {1,2}, {1,3}, {2,3}, {1,2,3}}

# Example 6: Cartesian Product - All possible pairs
sizes = {'S', 'M', 'L'}
colors = {'Red', 'Blue'}
all_tshirts = cartesian_product(sizes, colors)
print(f"All T-shirt variants: {all_tshirts}")
# Returns: {('S','Red'), ('S','Blue'), ('M','Red'), ...}

# Example 7: Check relationships between sets
print(is_subset({1, 2}, {1, 2, 3, 4}))  # True
print(is_disjoint({1, 2}, {3, 4}))  # True - no common elements

# Example 8: Find complement (elements not in set)
universal_set = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10}
my_set = {2, 4, 6, 8, 10}
odd_numbers = complement(my_set, universal_set)
print(f"Odd numbers: {odd_numbers}")  # {1, 3, 5, 7, 9}
```

**💡 Pro Tip:** Use power sets to explore all possible combinations in decision-making scenarios!

---

## 3️⃣ Combinatorics Module - Count Like a Pro

**What it does:** Calculate permutations, combinations, and other counting problems without manual calculation.

### 🎓 Real-World Use Case: Planning and Probability

```python
from discrete_math.combinatorics import *

# Example 1: Password Combinations
# How many 4-digit PIN codes are possible?
print(f"Possible 4-digit PINs: {10**4}")  # 10,000
# How many if all digits must be different?
print(f"PINs with unique digits: {permutations(10, 4)}")  # 5,040

# Example 2: Team Selection
# Choose 3 students from a class of 25 for a project
ways_to_choose = combinations(25, 3)
print(f"Ways to form a 3-person team: {ways_to_choose}")  # 2,300

# Example 3: Ordering Matters (Permutations)
# 5 runners in a race - how many possible finishing orders?
finishing_orders = permutations(5, 5)
print(f"Possible race outcomes: {finishing_orders}")  # 120

# Example 4: Podium Positions (first 3 places from 10 runners)
podium_arrangements = permutations(10, 3)
print(f"Podium possibilities: {podium_arrangements}")  # 720

# Example 5: Binomial Coefficient (used in probability)
# Probability calculations, Pascal's triangle
coeff = binomial_coefficient(5, 2)
print(f"C(5,2) = {coeff}")  # 10

# Example 6: Pascal's Triangle (row by row)
# Useful for expanding binomials and probability
triangle = pascals_triangle(5)
print("Pascal's Triangle (first 5 rows):")
for row in triangle:
    print(row)
# Output:
# [1]
# [1, 1]
# [1, 2, 1]
# [1, 3, 3, 1]
# [1, 4, 6, 4, 1]

# Example 7: Fibonacci Numbers
# Natural sequences appearing everywhere in nature
fib_10 = fibonacci(10)
print(f"10th Fibonacci number: {fib_10}")  # 55

# Example 8: Catalan Numbers
# Counting binary trees, valid parentheses, etc.
catalan_5 = catalan_number(5)
print(f"5th Catalan number: {catalan_5}")  # 42

# Example 9: Derangements
# Permutations where no element appears in its original position
# Useful for "Secret Santa" problems
derange_4 = derangements(4)
print(f"Ways to shuffle 4 items so none is in original spot: {derange_4}")  # 9
```

**💡 Student Tip:** Permutations = order matters (race positions). Combinations = order doesn't matter (team selection).

---

## 4️⃣ Graph Theory Module - Visualize Connections

**What it does:** Create graphs, traverse them, find shortest paths, and analyze connectivity.

### 🎓 Real-World Use Case: Social Networks and Navigation

```python
from discrete_math.graphs import Graph

# Example 1: Building a Social Network
social_network = Graph()
social_network.add_edge('Alice', 'Bob')
social_network.add_edge('Bob', 'Charlie')
social_network.add_edge('Charlie', 'David')
social_network.add_edge('Alice', 'David')

# Example 2: Find Shortest Path (Friend Connections)
path = social_network.shortest_path('Alice', 'Charlie')
print(f"Connection path from Alice to Charlie: {path}")
# Shows: Alice -> Bob -> Charlie

# Example 3: Breadth-First Search (BFS)
# Explore network level by level
bfs_order = social_network.bfs('Alice')
print(f"BFS traversal from Alice: {bfs_order}")

# Example 4: Depth-First Search (DFS)
# Explore as deep as possible first
dfs_order = social_network.dfs('Alice')
print(f"DFS traversal from Alice: {dfs_order}")

# Example 5: Check if Graph is Connected
# Can everyone reach everyone?
print(f"Is network fully connected? {social_network.is_connected()}")

# Example 6: Detect Cycles
# Are there circular relationships?
print(f"Network has cycles? {social_network.has_cycle()}")

# Example 7: Check if Bipartite
# Can we split into two groups with no internal connections?
print(f"Can split into two groups? {social_network.is_bipartite()}")

# Example 8: Create Special Graphs
# Complete graph (everyone knows everyone)
complete = Graph.complete_graph(5)
print(f"Complete graph K5 has {len(complete.edges)} edges")  # 10 edges

# Cycle graph (circular connections)
cycle = Graph.cycle_graph(6)
print(f"Cycle C6 has {len(cycle.vertices)} vertices")  # 6 vertices

# Example 9: Weighted Graph (Road Network with Distances)
road_network = Graph(directed=False)
road_network.add_edge('CityA', 'CityB', weight=50)
road_network.add_edge('CityB', 'CityC', weight=30)
road_network.add_edge('CityA', 'CityC', weight=100)

shortest = road_network.shortest_path('CityA', 'CityC')
print(f"Shortest route: {shortest}")  # Via CityB: 80 km total

# Example 10: Minimum Spanning Tree (Efficient Network Design)
mst = road_network.minimum_spanning_tree()
print(f"Minimum roads needed to connect all cities: {mst}")

# Example 11: Euler Path (Visit every road exactly once)
# The famous "Seven Bridges of Königsberg" problem
print(f"Can traverse all connections exactly once? {social_network.is_eulerian()}")
```

**💡 Pro Tip:** BFS finds shortest paths in unweighted graphs. DFS is great for maze-solving!

---

## 5️⃣ Number Theory Module - Explore Number Properties

**What it does:** Work with primes, GCD/LCM, modular arithmetic, and number properties.

### 🎓 Real-World Use Case: Cryptography and Scheduling

```python
from discrete_math.number_theory import *

# Example 1: Greatest Common Divisor (GCD)
# Simplifying fractions, finding common factors
print(f"GCD of 48 and 18: {gcd(48, 18)}")  # 6
# So 48/18 simplifies to 8/3

# Example 2: Least Common Multiple (LCM)
# Scheduling problems (when do events align?)
print(f"LCM of 12 and 18: {lcm(12, 18)}")  # 36
# Bus A comes every 12 min, Bus B every 18 min
# They align every 36 minutes

# Example 3: Prime Number Testing
# Cryptography, security
print(f"Is 17 prime? {is_prime(17)}")  # True
print(f"Is 100 prime? {is_prime(100)}")  # False

# Example 4: Prime Factorization
# Breaking numbers into prime components
factors = prime_factorization(60)
print(f"60 = {factors}")  # {2: 2, 3: 1, 5: 1} means 2²×3¹×5¹

# Example 5: Generate Prime Numbers (Sieve of Eratosthenes)
primes_under_30 = sieve_of_eratosthenes(30)
print(f"Primes under 30: {primes_under_30}")
# [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]

# Example 6: Modular Inverse (Cryptography)
# Find x where (a * x) % m = 1
inverse = mod_inverse(3, 11)
print(f"3 * {inverse} ≡ 1 (mod 11)")  # 3 * 4 = 12 ≡ 1 (mod 11)
# Used in RSA encryption!

# Example 7: Modular Exponentiation (Fast Power)
# Calculate (base^exp) % mod efficiently
result = mod_exp(2, 100, 17)
print(f"2^100 mod 17 = {result}")  # Efficient even for huge exponents

# Example 8: Euler's Totient Function
# Count numbers coprime to n (important in RSA)
phi = euler_totient(9)
print(f"φ(9) = {phi}")  # 6 numbers less than 9 and coprime to it

# Example 9: Chinese Remainder Theorem
# Solve system of modular equations
# x ≡ 2 (mod 3), x ≡ 3 (mod 5), x ≡ 2 (mod 7)
remainders = [2, 3, 2]
moduli = [3, 5, 7]
solution = chinese_remainder_theorem(remainders, moduli)
print(f"Solution to system: x = {solution}")  # x = 23

# Example 10: Find All Divisors
divisors_24 = divisors(24)
print(f"All divisors of 24: {divisors_24}")  # [1,2,3,4,6,8,12,24]

# Example 11: Perfect Numbers
# Number equals sum of its proper divisors
print(f"Is 6 perfect? {is_perfect_number(6)}")  # True (6=1+2+3)
print(f"Is 28 perfect? {is_perfect_number(28)}")  # True
```

**💡 Security Note:** Modular arithmetic and prime numbers are the foundation of modern cryptography!

---

## 6️⃣ Relations Module - Analyze Relationships

**What it does:** Check properties of relations and compute closures.

### 🎓 Real-World Use Case: Database Relationships and Hierarchies

```python
from discrete_math.relations import *

# Example 1: Define a Relation
# Relation R on set {1, 2, 3, 4}
# (a, b) means "a is related to b"
R = {(1, 1), (1, 2), (2, 2), (3, 3), (4, 4), (2, 3)}
universe = {1, 2, 3, 4}

# Example 2: Check Reflexivity
# Is every element related to itself?
print(f"Is R reflexive? {is_reflexive(R, universe)}")  # True
# Useful for: "Every person knows themselves"

# Example 3: Check Symmetry
# If a→b, is b→a also true?
print(f"Is R symmetric? {is_symmetric(R)}")  # False (1→2 but not 2→1)
# Useful for: Friendship (usually symmetric), Following (not symmetric)

# Example 4: Check Transitivity
# If a→b and b→c, is a→c also true?
print(f"Is R transitive? {is_transitive(R)}")  # False (1→2→3 but not 1→3)
# Useful for: "Ancestor of" relation

# Example 5: Equivalence Relation
# Must be reflexive, symmetric, AND transitive
print(f"Is R an equivalence relation? {is_equivalence_relation(R, universe)}")
# Equivalence relations partition sets into classes (like "same birthday")

# Example 6: Reflexive Closure
# Add minimum pairs to make reflexive
reflexive_R = reflexive_closure(R, universe)
print(f"Reflexive closure: {reflexive_R}")
# Ensures everyone is related to themselves

# Example 7: Symmetric Closure
# Add minimum pairs to make symmetric
symmetric_R = symmetric_closure(R)
print(f"Symmetric closure: {symmetric_R}")
# Makes all relationships bidirectional

# Example 8: Transitive Closure
# Add all implied relationships
transitive_R = transitive_closure(R)
print(f"Transitive closure: {transitive_R}")
# Example: If A manages B, and B manages C, then A (indirectly) manages C

# Example 9: Partial Order Relation
# Check if it's a partial ordering (≤ relation)
partial_order = {(1, 1), (2, 2), (3, 3), (1, 2), (1, 3), (2, 3)}
print(f"Is this a partial order? {is_partial_order(partial_order, {1, 2, 3})}")
# Used in: Task scheduling, version control

# Example 10: Hasse Diagram Data
# Get minimal representation for visualization
hasse = generate_hasse_diagram(partial_order, {1, 2, 3})
print(f"Hasse diagram edges: {hasse}")
# Removes redundant connections for cleaner visualization
```

**💡 Academic Tip:** Equivalence relations partition sets into equivalence classes - super useful in abstract algebra!

---

## 7️⃣ Functions Module - Analyze Mappings

**What it does:** Check function properties and perform function operations.

### 🎓 Real-World Use Case: Data Mapping and Transformations

```python
from discrete_math.functions import *

# Example 1: Define a Function (as a dictionary)
# Maps student IDs to grades
grades = {101: 'A', 102: 'B', 103: 'A', 104: 'C', 105: 'B'}
domain = {101, 102, 103, 104, 105}
codomain = {'A', 'B', 'C', 'D', 'F'}

# Example 2: Check if Injective (One-to-One)
# No two students have the same grade?
print(f"Is grading injective? {is_injective(grades, domain)}")  # False
# Multiple students can have 'A'

# Example 3: Check if Surjective (Onto)
# Are all possible grades actually given?
print(f"Is grading surjective? {is_surjective(grades, codomain)}")  # False
# No one got 'D' or 'F'

# Example 4: Check if Bijective (One-to-One AND Onto)
# Perfect pairing between domain and codomain
print(f"Is grading bijective? {is_bijective(grades, domain, codomain)}")  # False

# Example 5: Function Composition
# Apply multiple transformations in sequence
f = {1: 2, 2: 3, 3: 4}  # Add 1
g = {2: 4, 3: 6, 4: 8}  # Multiply by 2
# g∘f means: first apply f, then apply g
composition = compose(g, f)
print(f"(g∘f)(1) = {composition}")  # 1 →f→ 2 →g→ 4

# Example 6: Inverse Function
# Reverse the mapping (only works for bijections)
bijection = {1: 'a', 2: 'b', 3: 'c'}
inverse = function_inverse(bijection)
print(f"Inverse: {inverse}")  # {'a': 1, 'b': 2, 'c': 3}

# Example 7: Function Properties Check
age_mapping = {
    'Alice': 25,
    'Bob': 30,
    'Charlie': 25,
    'David': 35
}
print(f"Is age mapping injective? {is_injective(age_mapping, set(age_mapping.keys()))}")
# False - Alice and Charlie are both 25

# Example 8: Image and Pre-image
# What values does the function actually produce? (Image)
# What inputs give a specific output? (Pre-image)
print(f"All ages in the mapping: {set(age_mapping.values())}")  # {25, 30, 35}
```

**💡 Math Tip:** Bijective functions are invertible - they have a unique reverse operation!

---

## 🛠️ Development & Contributing

### Want to Contribute? We'd Love Your Help!

This is an open-source project, and contributions are always welcome! Whether you're fixing bugs, adding features, or improving documentation - every contribution matters.

### Setup Your Development Environment

```bash
# Step 1: Fork and clone the repository
git clone https://github.com/CodewithTanzeel/pypi-package-dm.git
cd pypi-package-dm

# Step 2: Create a virtual environment
python -m venv venv

# Step 3: Activate it
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Step 4: Install in development mode with all dev tools
pip install -e ".[dev]"
```

### Running Tests

Make sure everything works before submitting changes:

```bash
# Run all tests
pytest

# Run tests with coverage report (see which code is tested)
pytest --cov=discrete_math --cov-report=html

# Run a specific test file
pytest tests/test_logic.py

# Run tests in verbose mode (see each test individually)
pytest -v
```

### Code Quality Tools

Keep the codebase clean and consistent:

```bash
# Auto-format your code (makes it pretty!)
black src/

# Check for code style issues
flake8 src/

# Type checking (catch bugs early)
mypy src/
```

### How to Contribute

1. **Fork** the repository on GitHub
2. **Create a branch** for your feature: `git checkout -b feature/AmazingFeature`
3. **Make your changes** and add tests
4. **Run tests** to ensure nothing breaks: `pytest`
5. **Commit** your changes: `git commit -m 'Add some AmazingFeature'`
6. **Push** to your branch: `git push origin feature/AmazingFeature`
7. **Open a Pull Request** on GitHub

**For major changes, please open an issue first to discuss what you'd like to change!**

---

## 📖 Common Use Cases & Recipes

### Recipe 1: Homework Helper - Verify Set Theory Answers

```python
from discrete_math import sets

# Your homework problem:
# Given A = {1,2,3,4,5} and B = {4,5,6,7}
# Find: A ∪ B, A ∩ B, A - B, |P(A)|

A = {1, 2, 3, 4, 5}
B = {4, 5, 6, 7}

print(f"A ∪ B = {sets.union(A, B)}")  # {1,2,3,4,5,6,7}
print(f"A ∩ B = {sets.intersection(A, B)}")  # {4,5}
print(f"A - B = {sets.difference(A, B)}")  # {1,2,3}
print(f"|P(A)| = {len(sets.power_set(A))}")  # 32 subsets
```

### Recipe 2: Password Strength Analyzer

```python
from discrete_math import combinatorics

def analyze_password_strength(length, use_lowercase=True, use_uppercase=True,
                              use_digits=True, use_special=True):
    """Calculate how many possible passwords exist."""
    charset_size = 0
    if use_lowercase: charset_size += 26  # a-z
    if use_uppercase: charset_size += 26  # A-Z
    if use_digits: charset_size += 10     # 0-9
    if use_special: charset_size += 32    # !@#$%^&*...
    
    total_combinations = charset_size ** length
    print(f"Password length: {length}")
    print(f"Character set size: {charset_size}")
    print(f"Total possible passwords: {total_combinations:,}")
    print(f"Entropy: {length * charset_size} bits")
    return total_combinations

# 8-character password with all character types
analyze_password_strength(8, True, True, True, True)
# Result: Over 6 quadrillion combinations!
```

### Recipe 3: Social Network Analysis

```python
from discrete_math.graphs import Graph

def analyze_social_network(friendships):
    """Analyze a social network graph."""
    network = Graph()
    
    # Build the network
    for person1, person2 in friendships:
        network.add_edge(person1, person2)
    
    # Analysis
    print(f"Total people: {len(network.vertices)}")
    print(f"Total friendships: {len(network.edges)}")
    print(f"Network is connected: {network.is_connected()}")
    
    # Find most central person (most connections)
    connections = {person: network.degree(person) for person in network.vertices}
    most_connected = max(connections, key=connections.get)
    print(f"Most connected person: {most_connected} ({connections[most_connected]} friends)")
    
    return network

friendships = [
    ('Alice', 'Bob'), ('Bob', 'Charlie'), ('Charlie', 'David'),
    ('Alice', 'David'), ('Eve', 'Alice')
]
analyze_social_network(friendships)
```

### Recipe 4: Class Scheduling Conflict Checker

```python
from discrete_math import sets

def check_schedule_conflicts(student_schedule):
    """Check if a student's schedule has time conflicts."""
    # Each course is (course_name, time_slot)
    time_slots = {}
    conflicts = []
    
    for course, time in student_schedule:
        if time in time_slots:
            conflicts.append((time_slots[time], course, time))
        else:
            time_slots[time] = course
    
    if conflicts:
        print("⚠️ Schedule conflicts found:")
        for course1, course2, time in conflicts:
            print(f"  {course1} and {course2} both at {time}")
    else:
        print("✅ No conflicts! Schedule is valid.")
    
    return len(conflicts) == 0

schedule = [
    ('Math 101', 'Mon 9AM'),
    ('CS 201', 'Mon 11AM'),
    ('Physics 101', 'Mon 9AM'),  # Conflict!
    ('History 101', 'Tue 10AM')
]
check_schedule_conflicts(schedule)
```

### Recipe 5: Cryptography - Simple RSA Key Generation

```python
from discrete_math.number_theory import *

def generate_simple_rsa_keys(p, q):
    """Generate RSA public and private keys (simplified educational version)."""
    # Step 1: Calculate n
    n = p * q
    
    # Step 2: Calculate Euler's totient φ(n)
    phi_n = (p - 1) * (q - 1)
    
    # Step 3: Choose public exponent e (commonly 65537)
    e = 65537
    if gcd(e, phi_n) != 1:
        e = 3  # Fallback
    
    # Step 4: Calculate private exponent d
    d = mod_inverse(e, phi_n)
    
    print(f"Public Key: (e={e}, n={n})")
    print(f"Private Key: (d={d}, n={n})")
    print(f"φ(n) = {phi_n}")
    
    return (e, n), (d, n)

# Example with small primes (educational only!)
if is_prime(61) and is_prime(53):
    public_key, private_key = generate_simple_rsa_keys(61, 53)
    
    # Encrypt a message (m = 42)
    m = 42
    e, n = public_key
    encrypted = mod_exp(m, e, n)
    print(f"\nOriginal message: {m}")
    print(f"Encrypted: {encrypted}")
    
    # Decrypt
    d, n = private_key
    decrypted = mod_exp(encrypted, d, n)
    print(f"Decrypted: {decrypted}")
```

---

## ❓ FAQ - Frequently Asked Questions

**Q: Do I need to know advanced math to use this library?**  
A: Not at all! The library is designed to help you *learn* discrete math. Start with the examples and experiment.

**Q: Can I use this for my homework?**  
A: Yes! It's a great tool to verify your answers and understand concepts. But make sure you understand *why* the answers are correct.

**Q: Is this suitable for production applications?**  
A: The library is educational-focused. For production cryptography, use established libraries like `cryptography` or `pycryptodome`.

**Q: How can I visualize graphs?**  
A: The library uses NetworkX under the hood. You can export graphs and use matplotlib for visualization.

**Q: What Python version do I need?**  
A: Python 3.8 or higher. Check with `python --version`.

**Q: The library is missing feature X. Can I request it?**  
A: Absolutely! Open an issue on GitHub with your feature request.

**Q: I found a bug. What should I do?**  
A: Please report it on [GitHub Issues](https://github.com/CodewithTanzeel/pypi-package-dm/issues) with:
- Python version
- Code that reproduces the bug
- Expected vs actual behavior

---

## 📚 Learning Resources

**Want to dive deeper into Discrete Mathematics?**

### Recommended Books
- "Discrete Mathematics and Its Applications" by Kenneth Rosen
- "Concrete Mathematics" by Graham, Knuth, Patashnik
- "Introduction to Graph Theory" by Douglas West

### Online Courses
- MIT OpenCourseWare: Mathematics for Computer Science
- Coursera: Discrete Mathematics Specialization
- Khan Academy: Discrete Math Topics

### Practice Problems
- Use this library to verify your solutions
- Check out [Project Euler](https://projecteuler.net/) for challenging problems
- LeetCode has many discrete math algorithm problems

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**What does this mean?**  
You can freely use, modify, and distribute this library, even for commercial purposes. Just include the original license.

---

## 👤 Author

**CodewithTanzeel**

- GitHub: [@CodewithTanzeel](https://github.com/CodewithTanzeel)
- Email: Tanzeelofficial@outlook.com

---

## 🙏 Acknowledgments

- **Students of MS-207 Discrete Mathematics** - This library was built with you in mind!
- **Open Source Community** - Built on amazing libraries like NumPy, SymPy, NetworkX, and Matplotlib
- **Educators worldwide** - For inspiring the need for better educational tools
- **Contributors** - Everyone who has helped improve this project

---

## 💬 Support & Community

- **Questions?** Open a [GitHub Discussion](https://github.com/CodewithTanzeel/pypi-package-dm/discussions)
- **Found a bug?** File an [Issue](https://github.com/CodewithTanzeel/pypi-package-dm/issues)
- **Want to contribute?** Check out our [Contributing Guidelines](#-development--contributing)
- **Need help?** Reach out via email or GitHub

---

## 📊 Project Stats

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-active-success)

---

## 🗺️ Roadmap

### Version 0.2.0 (Coming Soon)
- [ ] Interactive Jupyter Notebook examples
- [ ] Graph visualization helpers
- [ ] More number theory algorithms
- [ ] Performance optimizations
- [ ] Enhanced documentation

### Version 0.3.0 (Planned)
- [ ] CLI tool for quick calculations
- [ ] LaTeX output for formulas
- [ ] Step-by-step solution explanations
- [ ] More real-world examples

**Have ideas?** Share them in GitHub Issues!

---

## 📝 Changelog

### Version 0.1.0 (Initial Release)
- ✅ Logic operations and truth tables
- ✅ Complete set theory operations
- ✅ Relations and properties
- ✅ Combinatorics functions
- ✅ Graph theory algorithms
- ✅ Number theory utilities
- ✅ Function analysis tools
- ✅ Comprehensive test suite (46 tests passing)
- ✅ Full documentation and examples

---

**Happy Computing! 🎉**

*Remember: Discrete mathematics is everywhere - from computer science to cryptography, from scheduling to social networks. This library is your companion in exploring these fascinating concepts!*

