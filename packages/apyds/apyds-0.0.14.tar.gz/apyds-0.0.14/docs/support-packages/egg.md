# E-Graph Support Package

The E-Graph support package provides efficient management and manipulation of equivalence classes of terms for the DS deductive system.

An E-Graph (Equality Graph) is a data structure that efficiently represents equivalence classes of terms and automatically maintains congruence closure. This implementation follows the egg-style approach with deferred rebuilding for optimal performance. Inspired by the [egg library](https://egraphs-good.github.io/).

## Installation

### Python

```bash
pip install apyds-egg
```

Requires Python 3.11-3.14.

### TypeScript/JavaScript

```bash
npm install atsds-egg
```

## Usage

### Python Example

```python
import apyds
from apyds_egg import EGraph

# Create an E-Graph
eg = EGraph()

# Add terms to the E-Graph
a = eg.add(apyds.Term("a"))
b = eg.add(apyds.Term("b"))
x = eg.add(apyds.Term("x"))

# Add compound terms
ax = eg.add(apyds.Term("(+ a x)"))
bx = eg.add(apyds.Term("(+ b x)"))

# Initially, (+ a x) and (+ b x) are in different E-classes
assert eg.find(ax) != eg.find(bx)

# Merge a and b
eg.merge(a, b)

# Rebuild to restore congruence
eg.rebuild()

# Now (+ a x) and (+ b x) are in the same E-class
assert eg.find(ax) == eg.find(bx)
```

### TypeScript Example

```typescript
import { Term } from "atsds";
import { EGraph } from "atsds-egg";

// Create an E-Graph
const eg = new EGraph();

// Add terms to the E-Graph
const a = eg.add(new Term("a"));
const b = eg.add(new Term("b"));
const x = eg.add(new Term("x"));

// Add compound terms
const ax = eg.add(new Term("(+ a x)"));
const bx = eg.add(new Term("(+ b x)"));

// Initially, (+ a x) and (+ b x) are in different E-classes
if (eg.find(ax) === eg.find(bx)) throw new Error("Should be different");

// Merge a and b
eg.merge(a, b);

// Rebuild to restore congruence
eg.rebuild();

// Now (+ a x) and (+ b x) are in the same E-class
if (eg.find(ax) !== eg.find(bx)) throw new Error("Should be same");
```

### Congruence Closure

The E-Graph automatically maintains congruence closure. When two E-classes are merged, the `rebuild()` method ensures that all congruent terms remain in the same E-class.

#### Python Example

```python
eg = EGraph()

# Add terms with nested structure
fa = eg.add(apyds.Term("(f a)"))
fb = eg.add(apyds.Term("(f b)"))
gfa = eg.add(apyds.Term("(g (f a))"))
gfb = eg.add(apyds.Term("(g (f b))"))

# Merge a and b
a = eg.add(apyds.Term("a"))
b = eg.add(apyds.Term("b"))
eg.merge(a, b)

# Rebuild propagates equivalence
eg.rebuild()

# Now all derived terms are equivalent
assert eg.find(fa) == eg.find(fb)
assert eg.find(gfa) == eg.find(gfb)
```

#### TypeScript Example

```typescript
import { Term } from "atsds";
import { EGraph } from "atsds-egg";

const eg = new EGraph();

// Add terms with nested structure
const fa = eg.add(new Term("(f a)"));
const fb = eg.add(new Term("(f b)"));
const gfa = eg.add(new Term("(g (f a))"));
const gfb = eg.add(new Term("(g (f b))"));

// Merge a and b
const a = eg.add(new Term("a"));
const b = eg.add(new Term("b"));
eg.merge(a, b);

// Rebuild propagates equivalence
eg.rebuild();

// Now all derived terms are equivalent
if (eg.find(fa) !== eg.find(fb)) throw new Error("fa != fb");
if (eg.find(gfa) !== eg.find(gfb)) throw new Error("gfa != gfb");
```

## Core Concepts

### E-Graph Structure

An E-Graph consists of several key components:

- **E-Nodes**: Represent terms with an operator and children
- **E-classes**: Equivalence classes of E-Nodes
- **Hash-consing (Hashcons)**: Ensures uniqueness of E-Nodes by mapping identical nodes to the same E-class
- **Union-Find**: Manages E-class equivalence relationships
- **Parents**: Tracks which terms depend on each E-class
- **Worklist**: Manages deferred congruence rebuilding

### Deferred Rebuilding

The implementation uses egg-style deferred rebuilding:

1. **Merge**: Combine two E-classes and add to worklist
2. **Rebuild**: Process worklist to restore congruence
3. **Repair**: Re-canonicalize parent nodes and merge congruent ones

This approach provides better performance than immediate rebuilding by batching congruence updates.

### Adding Terms

Terms are converted to E-Nodes and added to the E-Graph:

- **Items (constants/functors) and Variables**: Atomic terms like `a`, `b`, or backtick-prefixed variables like `x` are represented as E-Nodes with no children
- **Lists**: Compound terms like `(+ a b)` are represented as E-Nodes with operator `"()"` and children for each list element

The hash-consing mechanism ensures that identical E-Nodes share the same E-class ID.

## API Reference

### Python (apyds-egg)

- `EGraph()`: Create a new E-Graph
- `add(term: apyds.Term) -> EClassId`: Add a term to the E-Graph
- `merge(a: EClassId, b: EClassId) -> EClassId`: Merge two E-classes
- `rebuild() -> None`: Restore congruence closure
- `find(eclass: EClassId) -> EClassId`: Find canonical E-class representative

### TypeScript (atsds-egg)

- `new EGraph()`: Create a new E-Graph
- `add(term: atsds.Term): EClassId`: Add a term to the E-Graph
- `merge(a: EClassId, b: EClassId): EClassId`: Merge two E-classes
- `rebuild(): void`: Restore congruence closure
- `find(eclass: EClassId): EClassId`: Find canonical E-class representative

## Package Information

- **Python Package**: [apyds-egg](https://pypi.org/project/apyds-egg/)
- **npm Package**: [atsds-egg](https://www.npmjs.com/package/atsds-egg)
- **Source Code**: [GitHub - egg directory](https://github.com/USTC-KnowledgeComputingLab/ds/tree/main/egg)
