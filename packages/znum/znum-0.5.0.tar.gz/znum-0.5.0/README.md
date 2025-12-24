# Znum

A Python library for Z-number arithmetic and multi-criteria decision making (MCDM).

A Z-number is a fuzzy number with two components:
- **A**: The main fuzzy set values (restriction on values)
- **B**: The confidence/belief values (reliability of A)

Znum supports full mathematical operations (addition, subtraction, multiplication, division, power), comparison operators, and includes implementations of TOPSIS, VIKOR, and PROMETHEE optimization methods.

## Installation

```bash
pip install znum
```

## Quick Start

```python
from znum import Znum

# Create Z-numbers
z1 = Znum([1, 2, 3, 4], [0.1, 0.2, 0.3, 0.4])
z2 = Znum([2, 4, 8, 10], [0.5, 0.6, 0.7, 0.8])

# Arithmetic operations
z3 = z1 + z2
z4 = z1 * z2
z5 = z1 - z2
z6 = z1 / z2

# Comparison
print(z1 > z2)  # False
print(z1 < z2)  # True

# Power
z7 = z1 ** 2
```

## MCDM Methods

### TOPSIS

```python
from znum import Znum, Topsis, Beast

# Create weights, alternatives, and criteria types
weights = [Znum([0.2, 0.3, 0.4, 0.5], [0.1, 0.2, 0.3, 0.4])]
alternatives = [[Znum([7, 8, 9, 10], [0.6, 0.7, 0.8, 0.9])]]
criteria_types = [Beast.CriteriaType.BENEFIT]

table = [weights, *alternatives, criteria_types]
topsis = Topsis(table)
result = topsis.solve()

# Access results
best_idx = topsis.index_of_best_alternative
worst_idx = topsis.index_of_worst_alternative
ranking = topsis.ordered_indices
```

### PROMETHEE

```python
from znum import Znum, Promethee, Beast

table = [weights, *alternatives, criteria_types]
promethee = Promethee(table)
sorted_alternatives = promethee.solve()

# Access results
best_idx = promethee.index_of_best_alternative
worst_idx = promethee.index_of_worst_alternative
ranking = promethee.ordered_indices
```

## Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest
```

## License

MIT
