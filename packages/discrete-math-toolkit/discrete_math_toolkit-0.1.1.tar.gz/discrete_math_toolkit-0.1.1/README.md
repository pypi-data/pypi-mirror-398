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
## 1️⃣ Logic Module – Work with Logical Statements

**What it does:**  
Analyze propositional logic expressions, generate truth tables, evaluate expressions, check logical properties, convert to normal forms, and extract minterms/maxterms.

This module is ideal for **Discrete Mathematics**, **Logic Design**, and **Computer Organization** students.

---

## 🔹 Supported Logical Operators

| Operator | Syntax |
|--------|-------|
| AND | `AND`, `&`, `∧` |
| OR | `OR`, `|`, `∨` |
| NOT | `NOT`, `~`, `¬` |
| IMPLIES | `IMPLIES`, `->` |
| IFF (↔) | `IFF`, `<->` |
| XOR | `XOR`, `^` |

---

## 📘 Example Usage

```python
from discrete_math.logic import *
````


## ✅ 1. Generate Truth Tables

```python

table = generate_truth_table("p AND q")
print(table)
```

**Output:**

```text
[
 {'p': False, 'q': False, 'result': False},
 {'p': False, 'q': True, 'result': False},
 {'p': True, 'q': False, 'result': False},
 {'p': True, 'q': True, 'result': True}
]
```

📌 *Useful for understanding all possible outcomes of a logical expression.*

---

## ✅ 2. Check Logical Properties

### 🔹 Tautology (Always True)

```python
print(is_tautology("p OR (NOT p)"))
```

✔️ Output:

```text
True
```

---

### 🔹 Contradiction (Always False)

```python
print(is_contradiction("p AND (NOT p)"))
```

✔️ Output:

```text
True
```

---

### 🔹 Contingency (Sometimes True, Sometimes False)

```python
print(is_contingency("p AND q"))
```

✔️ Output:

```text
True
```

---

## ✅ 3. Evaluate an Expression with Given Values

```python
result = evaluate("p AND q", {"p": True, "q": False})
print(result)
```

✔️ Output:

```text
False
```

📌 *Helpful in exams and quick verification.*

---

## ✅ 4. Convert to Normal Forms

### 🔹 Conjunctive Normal Form (CNF)

```python
cnf = convert_to_cnf("(p OR q) IMPLIES r")
print(cnf)
```

✔️ Output:

```text
(~p | r) & (~q | r)
```

---

### 🔹 Disjunctive Normal Form (DNF)

```python
dnf = convert_to_dnf("(p AND q) OR (p AND r)")
print(dnf)
```

✔️ Output:

```text
p & (q | r)
```

---

## ✅ 5. Simplify Logical Expressions

```python
simple = simplify("(p AND p) OR (q AND True)")
print(simple)
```

✔️ Output:

```text
p | q
```

📌 *Applies logical identities automatically.*

---

## ✅ 6. Check Logical Equivalence

```python
expr1 = "p IMPLIES q"
expr2 = "(NOT p) OR q"

print(are_equivalent(expr1, expr2))
```

✔️ Output:

```text
True
```

📌 *Confirms whether two expressions mean the same thing.*

---

## ✅ 7. Find Minterms

```python
print(get_minterms("p OR q"))
```

✔️ Output:

```text
[1, 2, 3]
```

📌 *Indexes represent rows where the expression is TRUE.*

---

## ✅ 8. Find Maxterms

```python
print(get_maxterms("p OR q"))
```

✔️ Output:

```text
[0]
```

📌 *Indexes represent rows where the expression is FALSE.*

---

## 🎓 Student Tip

* Use **truth tables** to verify exam answers
* Use **CNF/DNF** for SAT solvers and logic circuits
* Use **minterms/maxterms** in Boolean algebra & K-maps

---


## 2️⃣ Sets Module – Master Set Operations

**What it does:**  
Perform all fundamental and advanced set theory operations such as union, intersection, difference, power sets, Cartesian products, partitions, and set relationships.

This module is ideal for **Discrete Mathematics**, **Computer Science**, and **Logic Foundations**.

---

## 📘 Example Usage

```python
from discrete_math.sets import *
````

---

## ✅ 1. Basic Set Operations

### 🔹 Union

```python
result = union({1, 2}, {2, 3}, {3, 4})
print(result)
```

**Output:**

```text
{1, 2, 3, 4}
```

---

### 🔹 Intersection

```python
result = intersection({1, 2, 3}, {2, 3, 4})
print(result)
```

**Output:**

```text
{2, 3}
```

---

### 🔹 Difference (A − B)

```python
result = difference({1, 2, 3}, {2, 3, 4})
print(result)
```

**Output:**

```text
{1}
```

---

### 🔹 Symmetric Difference (A △ B)

```python
result = symmetric_difference({1, 2, 3}, {2, 3, 4})
print(result)
```

**Output:**

```text
{1, 4}
```

---

### 🔹 Complement

```python
universal = {1, 2, 3, 4, 5}
subset = {1, 2}
print(complement(subset, universal))
```

**Output:**

```text
{3, 4, 5}
```

---

## ✅ 2. Power Sets

### 🔹 Generate Power Set

```python
ps = power_set({1, 2})
print(ps)
```

**Output:**

```text
{frozenset(), frozenset({1}), frozenset({2}), frozenset({1, 2})}
```

📌 *Each subset is returned as a `frozenset`.*

---

### 🔹 Power Set Cardinality (Without Generating)

```python
print(power_set_cardinality({1, 2, 3}))
```

**Output:**

```text
8
```

📌 *Uses the formula: 2ⁿ*

---

## ✅ 3. Cartesian Products

### 🔹 Cartesian Product of Two Sets

```python
pairs = cartesian_product({1, 2}, {'a', 'b'})
print(pairs)
```

**Output:**

```text
{(1, 'a'), (1, 'b'), (2, 'a'), (2, 'b')}
```

---

### 🔹 Cartesian Product of N Sets

```python
result = cartesian_product_n({1, 2}, {'a', 'b'}, {True, False})
print(result)
```

📌 *Returns all possible n-tuples.*

---

## ✅ 4. Set Relationships

### 🔹 Subset (⊆)

```python
print(is_subset({1, 2}, {1, 2, 3}))
```

**Output:**

```text
True
```

---

### 🔹 Proper Subset (⊂)

```python
print(is_proper_subset({1, 2}, {1, 2, 3}))
```

**Output:**

```text
True
```

---

### 🔹 Superset (⊇)

```python
print(is_superset({1, 2, 3}, {1, 2}))
```

**Output:**

```text
True
```

---

### 🔹 Disjoint Sets

```python
print(is_disjoint({1, 2}, {3, 4}))
```

**Output:**

```text
True
```

---

### 🔹 Set Equality

```python
print(are_equal({1, 2, 3}, {3, 2, 1}))
```

**Output:**

```text
True
```

---

## ✅ 5. Cardinality

```python
print(cardinality({10, 20, 30, 40}))
```

**Output:**

```text
4
```

📌 *Returns the number of elements in a set.*

---

## ✅ 6. Partition of a Set

```python
result = partition({1, 2, 3, 4}, {1, 2}, {3}, {4})
print(result)
```

**Output:**

```text
True
```

📌 *Checks whether subsets form a valid partition.*

---

## ✅ 7. Set-Builder Notation

```python
evens = set_builder(lambda x: x % 2 == 0, {1, 2, 3, 4, 5, 6})
print(evens)
```

**Output:**

```text
{2, 4, 6}
```

📌 *Mimics mathematical set-builder notation.*


---

Got it 👍
I’ll **fix and extend your README section** so that it **covers *all* public functions** exposed by your **Combinatorics Module**, based strictly on the `__all__` list in your code.

Below is a **drop-in replacement** for your current README section, written in the **same style**, with **clear examples for every function**.

---

## 3️⃣ Combinatorics Module – Count Like a Pro

**What it does:**
Perform combinatorial calculations such as permutations, combinations, binomial coefficients, and advanced counting sequences used in probability, algorithms, and discrete mathematics.

---

### 🎓 Real-World Use Case: Counting, Probability & Algorithms

```python
from discrete_math.combinatorics import *
```

---

### 🔢 Basic Building Block

#### Factorial

```python
# 5! = 5 × 4 × 3 × 2 × 1
print(factorial(5))  # 120
```

---

### 🔁 Permutations & Combinations

#### Permutations (order matters)

```python
# Arrange 3 items from 5
print(permutations(5, 3))  # 60
```

#### Combinations (order does NOT matter)

```python
# Choose 3 students from 10
print(combinations(10, 3))  # 120
```

---

### 🔂 With Repetition Allowed

#### Permutations with repetition

```python
# 3-character password from 4 symbols (repetition allowed)
print(permutations_with_repetition(4, 3))  # 64
```

#### Combinations with repetition

```python
# Choose 3 candies from 5 types
print(combinations_with_repetition(5, 3))  # 35
```

---

### 📐 Binomial & Multinomial Coefficients

#### Binomial Coefficient

```python
# C(5,2)
print(binomial_coefficient(5, 2))  # 10
```

#### Multinomial Coefficient

```python
# Distribute items into groups of sizes 2,1,1
print(multinomial_coefficient([2, 1, 1]))  # 12
```

---

### 📊 Pascal’s Triangle

```python
triangle = pascals_triangle(5)
for row in triangle:
    print(row)

# [1]
# [1, 1]
# [1, 2, 1]
# [1, 3, 3, 1]
# [1, 4, 6, 4, 1]
```

---

### 🌱 Famous Sequences

#### Fibonacci Numbers

```python
print(fibonacci(10))  # 55
```

#### Catalan Numbers

```python
# Used in counting trees, valid parentheses, etc.
print(catalan_number(5))  # 42
```

---

### 🔄 Special Counting Problems

#### Derangements (no element in original position)

```python
# Secret Santa problem
print(derangements(4))  # 9
```

#### Stirling Numbers (Second Kind)

```python
# Partition 5 elements into 2 non-empty sets
print(stirling_second_kind(5, 2))  # 15
```

#### Bell Numbers

```python
# Number of ways to partition a set of size 4
print(bell_number(4))  # 15
```

---

### 🔁 Generators (Actual Arrangements)

#### Generate permutations

```python
for p in generate_permutations([1, 2, 3], 2):
    print(p)

# (1, 2)
# (1, 3)
# (2, 1)
# ...
```

#### Generate combinations

```python
for c in generate_combinations([1, 2, 3, 4], 2):
    print(c)
```

#### Generate combinations with repetition

```python
for c in generate_combinations_with_repetition([1, 2, 3], 2):
    print(c)
```

---

### 💡 Student Tip

* **Permutations** → order matters (rankings, passwords)
* **Combinations** → order doesn’t matter (teams, selections)
* **Catalan & Stirling numbers** often appear in **DSA, trees, and recursion problems**






## 5️⃣ Number Theory Module - Explore Number Properties

Perfect — I’ll **repeat the same process** as before 👍
Below is a **clean, complete, drop-in README.md section** for your **Number Theory Module**, **covering *every function listed in `__all__`***, written in the **same tone, structure, and teaching style** you used.

You can **copy-paste this directly** into `README.md`.

---

## 5️⃣ Number Theory Module – Explore Number Properties

**What it does:**
Work with prime numbers, divisibility, GCD/LCM, modular arithmetic, and classic number-theoretic functions used in cryptography, algorithms, and discrete mathematics.

---

### 🎓 Real-World Use Case: Cryptography, Scheduling & Mathematics

```python
from discrete_math.number_theory import *
```

---

### 🔢 Fundamental Operations

#### Greatest Common Divisor (GCD)

```python
# Simplifying fractions, checking coprimality
print(gcd(48, 18))  # 6
print(gcd(17, 19))  # 1
```

#### Least Common Multiple (LCM)

```python
# Scheduling and periodic events
print(lcm(12, 18))  # 36
print(lcm(7, 5))    # 35
```

---

### 🔁 Extended Euclidean Algorithm

```python
# Finds gcd(a, b) and x, y such that ax + by = gcd(a, b)
g, x, y = extended_gcd(30, 20)
print(g, x, y)  # 10, 1, -1
```

📌 **Used in:** Modular inverse, cryptography, Diophantine equations

---

### 🔍 Prime Number Utilities

#### Prime Test

```python
print(is_prime(17))  # True
print(is_prime(100)) # False
```

#### Prime Factorization

```python
factors = prime_factorization(60)
print(factors)  # {2: 2, 3: 1, 5: 1}
# 60 = 2² × 3¹ × 5¹
```

#### Generate Primes (Sieve of Eratosthenes)

```python
print(sieve_of_eratosthenes(30))
# [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
```

---

### 🔐 Modular Arithmetic (Cryptography Core)

#### Modular Inverse

```python
# Find x such that (a * x) % m == 1
inverse = mod_inverse(3, 11)
print(inverse)  # 4
```

⚠️ Raises error if inverse does not exist.

---

#### Fast Modular Exponentiation

```python
print(mod_exp(2, 100, 17))  # Efficient for huge powers
print(mod_exp(3, 10, 7))    # 4
```

📌 **Used in:** RSA, Diffie-Hellman, hashing

---

### 🔢 Euler’s Totient Function

```python
# Counts integers ≤ n that are coprime with n
print(euler_totient(9))   # 6
print(euler_totient(10))  # 4
```

📌 **Key idea in RSA encryption**

---

### 🧮 Chinese Remainder Theorem (CRT)

```python
# Solve:
# x ≡ 2 (mod 3)
# x ≡ 3 (mod 5)
# x ≡ 2 (mod 7)
solution = chinese_remainder_theorem([2, 3, 2], [3, 5, 7])
print(solution)  # 23
```

📌 **Used in:** Distributed systems, cryptography, time synchronization

---

### 🔗 Coprimality

```python
print(is_coprime(15, 28))  # True
print(is_coprime(15, 25))  # False
```

---

### 📐 Divisor Functions

#### All Divisors

```python
print(divisors(24))
# [1, 2, 3, 4, 6, 8, 12, 24]
```

#### Sum of Divisors

```python
print(sum_of_divisors(12))  # 28
```

---

### ⭐ Perfect Numbers

```python
print(is_perfect_number(6))   # True
print(is_perfect_number(28))  # True
print(is_perfect_number(12))  # False
```

📌 A **perfect number** equals the sum of its proper divisors.




Got it 👍
Below is the **complete, polished README.md section for the Relations Module**, written in **the same style, structure, tone, and teaching depth** as your previous modules.
It **covers *all functions listed in `__all__`*** and aligns perfectly with the code you shared.

You can **copy-paste this directly into `README.md`**.

---

## 6️⃣ Relations Module – Analyze Relationships

**What it does:**
Work with binary relations, check their properties, compute closures, and analyze structured relationships mathematically.

---

### 🎓 Real-World Use Case: Databases, Hierarchies & Graphs

```python
from discrete_math.relations import *
```

---

### 🔗 Defining a Relation

```python
# Relation R on set {1, 2, 3, 4}
# (a, b) means "a is related to b"
R = {(1, 1), (1, 2), (2, 2), (3, 3), (4, 4), (2, 3)}
domain = {1, 2, 3, 4}
```

---

### ✅ Relation Properties

#### Reflexive

```python
print(is_reflexive(R, domain))  # True
```

📌 Every element relates to itself
**Example:** “Every person knows themselves”

---

#### Symmetric

```python
print(is_symmetric(R))  # False
```

📌 If `a → b`, then `b → a`
**Example:** Friendship (symmetric), Twitter follow (not symmetric)

---

#### Antisymmetric

```python
print(is_antisymmetric(R))  # True or False depending on R
```

📌 If `a → b` and `b → a`, then `a = b`
**Used in:** Partial orders (≤)

---

#### Transitive

```python
print(is_transitive(R))  # False
```

📌 If `a → b` and `b → c`, then `a → c`
**Example:** Ancestor relationships

---

### 🟰 Special Relations

#### Equivalence Relation

```python
print(is_equivalence_relation(R, domain))
```

✔ Reflexive
✔ Symmetric
✔ Transitive

📌 **Partitions a set into equivalence classes**

---

#### Partial Order

```python
partial_order = {(1,1), (2,2), (3,3), (1,2), (2,3), (1,3)}
print(is_partial_order(partial_order, {1, 2, 3}))  # True
```

📌 **Used in:** Task scheduling, version control systems

---

### 🔁 Relation Closures

#### Reflexive Closure

```python
ref_closure = reflexive_closure(R, domain)
print(ref_closure)
```

Adds `(a, a)` for all `a ∈ domain`

---

#### Symmetric Closure

```python
sym_closure = symmetric_closure(R)
print(sym_closure)
```

Makes every relation bidirectional

---

#### Transitive Closure

```python
trans_closure = transitive_closure(R)
print(trans_closure)
```

Adds all **implied indirect relationships**

📌 Uses **Warshall’s Algorithm**

---

### 🧩 Equivalence Classes

```python
R_eq = {(1,1), (2,2), (3,3), (1,2), (2,1)}
classes = equivalence_classes(R_eq, {1, 2, 3})
print(classes)  # [{1, 2}, {3}]
```

📌 **Only valid for equivalence relations**

---

### 🔄 Relation Operations

#### Composition of Relations

```python
R1 = {(1, 2), (2, 3)}
R2 = {(0, 1), (1, 2)}
print(compose(R1, R2))  # {(0, 2), (1, 3)}
```

📌 Used in **function chaining and graph traversal**

---

#### Inverse Relation

```python
print(inverse_relation({(1, 2), (2, 3)}))
# {(2, 1), (3, 2)}
```

📌 Swaps direction of every pair

---

### 📦 Domain & Range

```python
print(get_domain(R))  # {1, 2, 3, 4}
print(get_range(R))   # {1, 2, 3, 4}
```

📌 Helps analyze inputs and outputs of relations

---

### 🧮 Matrix Representation

```python
matrix = relation_matrix({(1, 2), (2, 3)}, {1, 2, 3})
for row in matrix:
    print(row)
```

**Output:**

```
[0, 1, 0]
[0, 0, 1]
[0, 0, 0]
```

📌 **Used in:** Graph theory, adjacency matrices, algorithms


Perfect — repeating **the exact same style, depth, and structure** as your previous modules.
Below is a **clean, complete, production-ready `README.md` section** for the **Functions Module**, fully aligned with your code and `__all__`.

You can **copy-paste this directly**.

---

## 7️⃣ Functions Module – Analyze Mappings

**What it does:**
Analyze mathematical functions, verify their properties (injective, surjective, bijective), perform composition, inversion, and convert between representations.

---

### 🎓 Real-World Use Case: Data Mapping & Transformations

```python
from discrete_math.functions import *
```

---

### 🔗 Defining a Function

Functions are represented as **sets of ordered pairs** or **Python dictionaries**.

```python
# Function as a dictionary
grades = {
    101: 'A',
    102: 'B',
    103: 'A',
    104: 'C',
    105: 'B'
}

domain = {101, 102, 103, 104, 105}
codomain = {'A', 'B', 'C', 'D', 'F'}

# Convert dictionary to function form
relation = dict_to_function(grades)
```

---

### ✅ Valid Function Check

```python
print(is_function(relation, domain))  # True
```

📌 Each domain element must map to **exactly one** output.

---

### 🔍 Function Properties

#### Injective (One-to-One)

```python
print(is_injective(relation))  # False
```

📌 No two inputs share the same output
❌ Here, multiple students received `'A'`

---

#### Surjective (Onto)

```python
print(is_surjective(relation, codomain))  # False
```

📌 Every element of codomain must be used
❌ Grades `'D'` and `'F'` are unused

---

#### Bijective (One-to-One & Onto)

```python
print(is_bijective(relation, domain, codomain))  # False
```

📌 **Only bijective functions are invertible**

---

### 🔁 Function Composition

```python
# f(x) = x + 1
f = {(1, 2), (2, 3), (3, 4)}

# g(x) = 2x
g = {(2, 4), (3, 6), (4, 8)}

# Composition: g ∘ f
composition = compose_functions(g, f)
print(composition)  # {(1, 4), (2, 6), (3, 8)}
```

📌 Apply **f first**, then **g**

---

### 🔄 Inverse Function

```python
bijection = {(1, 'a'), (2, 'b'), (3, 'c')}
inverse = inverse_function(bijection, {1, 2, 3}, {'a', 'b', 'c'})
print(inverse)  # {('a', 1), ('b', 2), ('c', 3)}
```

⚠️ Only works for **bijective functions**

---

### 🧠 Real-Life Mapping Example

```python
age_mapping = {
    'Alice': 25,
    'Bob': 30,
    'Charlie': 25,
    'David': 35
}

relation = dict_to_function(age_mapping)
print(is_injective(relation))  # False
```

📌 Two people share the same age → not injective

---

### 📦 Domain & Range

```python
print(get_domain(relation))
# {'Alice', 'Bob', 'Charlie', 'David'}

print(get_range(relation))
# {25, 30, 35}
```

📌 Helps analyze **inputs vs outputs**

---

### 🔁 Representation Conversion

#### Function → Dictionary

```python
print(function_to_dict({(1, 'a'), (2, 'b')}))
# {1: 'a', 2: 'b'}
```

#### Dictionary → Function

```python
print(dict_to_function({1: 'x', 2: 'y'}))
# {(1, 'x'), (2, 'y')}
```

---

### ⚙️ Function Evaluation (Callable)

```python
square = lambda x: x * x
print(evaluate_function(square, 5))  # 25
```

📌 Works with **any Python callable**




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

