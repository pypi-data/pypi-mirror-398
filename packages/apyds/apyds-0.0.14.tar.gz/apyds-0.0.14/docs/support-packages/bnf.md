# BNF Support Package

The BNF support package provides bidirectional conversion between DS's two syntax formats:

- **Ds**: The S-expression (lisp-like) syntax used internally by DS
- **Dsp**: A traditional, human-readable syntax with infix operators

This package enables you to write logical rules in a more natural, mathematical notation and convert them to the DS internal format, or vice versa.

## Installation

### Python

```bash
pip install apyds-bnf
```

Requires Python 3.11-3.14.

### JavaScript/TypeScript

```bash
npm install atsds-bnf
```

## Usage

### Python Example

```python
from apyds_bnf import parse, unparse

# Parse: Convert from readable Dsp to DS format
dsp_input = "a, b => c"
ds_output = parse(dsp_input)
print(ds_output)
# Output:
# a
# b
# ----
# c

# Unparse: Convert from DS format to readable Dsp
ds_input = "a\nb\n----\nc\n"
dsp_output = unparse(ds_input)
print(dsp_output)
# Output: a, b => c
```

### JavaScript/TypeScript Example

```javascript
import { parse, unparse } from "atsds-bnf";

// Parse: Convert from readable Dsp to DS format
const dsp_input = "a, b => c";
const ds_output = parse(dsp_input);
console.log(ds_output);
// Output:
// a
// b
// ----
// c

// Unparse: Convert from DS format to readable Dsp
const ds_input = "a\nb\n----\nc\n";
const dsp_output = unparse(ds_input);
console.log(dsp_output);
// Output: a, b => c
```

## Syntax Formats

### Ds Format (Internal)

The Ds format uses S-expressions (lisp-like syntax) for representing logical rules:

```
premise1
premise2
----------
conclusion
```

For structured terms:

- Functions: `(function f a b)`
- Subscripts: `(subscript a i j)`
- Binary operators: `(binary + a b)`
- Unary operators: `(unary ~ a)`

### Dsp Format (Human-Readable)

The Dsp format uses traditional mathematical notation:

```
premise1, premise2 => conclusion
```

For structured terms:

- Functions: `f(a, b)`
- Subscripts: `a[i, j]`
- Binary operators: `(a + b)` (parenthesized)
- Unary operators: `(~ a)` (parenthesized)

### Syntax Comparison

| Description | Dsp Format | Ds Format |
|-------------|------------|-----------|
| Simple rule | `a, b => c` | `a\nb\n----\nc\n` |
| Axiom | `a` | `----\na\n` |
| Function call | `f(a, b) => c` | `(function f a b)\n----------------\nc\n` |
| Subscript | `a[i, j] => b` | `(subscript a i j)\n-----------------\nb\n` |
| Binary operator | `(a + b) => c` | `(binary + a b)\n--------------\nc\n` |
| Unary operator | `~ a => b` | `(unary ~ a)\n-----------\nb\n` |
| Complex expression | `((a + b) * c), d[i] => f(g, h)` | `(binary * (binary + a b) c)\n(subscript d i)\n---------------------------\n(function f g h)\n` |

## Package Information

- **Python Package**: [apyds-bnf](https://pypi.org/project/apyds-bnf/)
- **npm Package**: [atsds-bnf](https://www.npmjs.com/package/atsds-bnf)
- **Source Code**: [GitHub - bnf directory](https://github.com/USTC-KnowledgeComputingLab/ds/tree/main/bnf)
