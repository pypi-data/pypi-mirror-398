# Python API Reference

This page documents the Python API for the `apyds` package.

```python
from apyds import (
    buffer_size,
    scoped_buffer_size,
    String,
    Variable,
    Item,
    List,
    Term,
    Rule,
    Search,
)
```

## buffer_size

Gets the current buffer size, or sets a new buffer size and returns the previous value.

```python
def buffer_size(size: int = 0) -> int
```

**Parameters:**

- `size` (optional): The new buffer size to set. If 0 (default), returns current size without modification.

**Returns:** The previous buffer size value.

**Example:**

```python
current_size = buffer_size()       # Get current size
old_size = buffer_size(2048)       # Set new size, returns old size
```

---

## scoped_buffer_size

Context manager for temporarily changing the buffer size.

```python
@contextmanager
def scoped_buffer_size(size: int = 0)
```

**Parameters:**

- `size`: The temporary buffer size to set.

**Example:**

```python
with scoped_buffer_size(4096):
    # Operations here use buffer size of 4096
    pass
# Buffer size is restored to previous value
```

---

## String

Wrapper class for deductive system strings.

### Constructor

```python
def __init__(self, value: String | str | bytes, size: int | None = None)
```

**Parameters:**

- `value`: Initial value (string, bytes, or another String)
- `size` (optional): Buffer capacity for internal storage

### Methods

#### \_\_str\_\_()

Convert the value to a string representation.

```python
def __str__(self) -> str
```

#### data()

Get the binary representation of the value.

```python
def data(self) -> bytes
```

#### size()

Get the size of the data in bytes.

```python
def size(self) -> int
```

**Example:**

```python
str1 = String("hello")
str2 = String(str1.data())  # From binary
print(str1)  # "hello"
```

---

## Variable

Wrapper class for logical variables in the deductive system.

### Constructor

```python
def __init__(self, value: Variable | str | bytes, size: int | None = None)
```

**Parameters:**

- `value`: Initial value (string starting with backtick, bytes, or another Variable)
- `size` (optional): Buffer capacity for internal storage

### Properties

#### name

Get the name of this variable (without the backtick prefix).

```python
@property
def name(self) -> String
```

**Example:**

```python
var1 = Variable("`X")
print(var1.name)  # "X"
print(var1)       # "`X"
```

---

## Item

Wrapper class for items (constants/functors) in the deductive system.

### Constructor

```python
def __init__(self, value: Item | str | bytes, size: int | None = None)
```

### Properties

#### name

Get the name of this item.

```python
@property
def name(self) -> String
```

**Example:**

```python
item = Item("atom")
print(item.name)  # "atom"
```

---

## List

Wrapper class for lists in the deductive system.

### Constructor

```python
def __init__(self, value: List | str | bytes, size: int | None = None)
```

### Methods

#### \_\_len\_\_()

Get the number of elements in the list.

```python
def __len__(self) -> int
```

#### \_\_getitem\_\_()

Get an element from the list by index.

```python
def __getitem__(self, index: int) -> Term
```

**Example:**

```python
lst = List("(a b c)")
print(len(lst))   # 3
print(lst[0])     # "a"
```

---

## Term

Wrapper class for logical terms in the deductive system. A term can be a variable, item, or list.

### Constructor

```python
def __init__(self, value: Term | str | bytes, size: int | None = None)
```

### Properties

#### term

Extracts the underlying term and returns it as its concrete type.

```python
@property
def term(self) -> Variable | Item | List
```

### Methods

#### ground()

Ground this term using a dictionary to substitute variables with values.

```python
def ground(self, other: Term, scope: str | None = None) -> Term | None
```

**Parameters:**

- `other`: A term representing a dictionary (list of pairs)
- `scope` (optional): Scope string for variable scoping

**Returns:** The grounded term, or None if grounding fails.

**Example:**

```python
a = Term("`a")
dict = Term("((`a b))")
result = a.ground(dict)
if result is not None:
    print(result)  # "b"
```

#### \_\_matmul\_\_() / match

Match two terms and return the unification result as a dictionary.

```python
def __matmul__(self, other: Term) -> Term | None
```

**Parameters:**

- `other`: The term to match with this term

**Returns:** A term representing the unification dictionary (list of tuples), or None if matching fails.

**Example:**

```python
a = Term("`a")
b = Term("b")
result = a @ b
if result is not None:
    print(result)  # "((1 2 `a b))"
```

#### rename()

Rename all variables in this term by adding prefix and suffix.

```python
def rename(self, prefix_and_suffix: Term) -> Term | None
```

**Parameters:**

- `prefix_and_suffix`: A term with format `((prefix) (suffix))`

**Returns:** The renamed term, or None if renaming fails.

**Example:**

```python
term = Term("`x")
spec = Term("((pre_) (_suf))")
result = term.rename(spec)
if result is not None:
    print(result)  # "`pre_x_suf"
```

---

## Rule

Wrapper class for logical rules in the deductive system.

### Constructor

```python
def __init__(self, value: Rule | str | bytes, size: int | None = None)
```

### Properties

#### conclusion

Get the conclusion of the rule.

```python
@property
def conclusion(self) -> Term
```

### Methods

#### \_\_len\_\_()

Get the number of premises in the rule.

```python
def __len__(self) -> int
```

#### \_\_getitem\_\_()

Get a premise term by index.

```python
def __getitem__(self, index: int) -> Term
```

#### ground()

Ground this rule using a dictionary.

```python
def ground(self, other: Rule, scope: str | None = None) -> Rule | None
```

#### \_\_matmul\_\_() / match

Match this rule with another rule using unification.

```python
def __matmul__(self, other: Rule) -> Rule | None
```

**Parameters:**

- `other`: The rule to match against (must be a fact without premises)

**Returns:** The matched rule, or None if matching fails.

**Example:**

```python
mp = Rule("(`p -> `q)\n`p\n`q\n")
pq = Rule("((! (! `x)) -> `x)")
result = mp @ pq
if result is not None:
    print(result)
    # "(! (! `x))\n----------\n`x\n"
```

#### rename()

Rename all variables in this rule.

```python
def rename(self, prefix_and_suffix: Rule) -> Rule | None
```

---

## Search

Search engine for the deductive system.

### Constructor

```python
def __init__(self, limit_size: int = 1000, buffer_size: int = 10000)
```

**Parameters:**

- `limit_size` (optional): Size of the buffer for storing rules/facts (default: 1000)
- `buffer_size` (optional): Size of the buffer for internal operations (default: 10000)

### Methods

#### set_limit_size()

Set the size of the buffer for storing final objects.

```python
def set_limit_size(self, limit_size: int) -> None
```

#### set_buffer_size()

Set the buffer size for internal operations.

```python
def set_buffer_size(self, buffer_size: int) -> None
```

#### reset()

Reset the search engine, clearing all rules and facts.

```python
def reset(self) -> None
```

#### add()

Add a rule or fact to the knowledge base.

```python
def add(self, text: str) -> bool
```

**Returns:** True if successfully added, False otherwise.

#### execute()

Execute the search engine with a callback for each inferred rule.

```python
def execute(self, callback: Callable[[Rule], bool]) -> int
```

**Parameters:**

- `callback`: Function called for each candidate rule. Return False to continue, True to stop.

**Returns:** The number of rules processed.

**Example:**

```python
search = Search(1000, 10000)
search.add("(`P -> `Q) `P `Q")
search.add("(! (! X))")

def callback(candidate):
    print(candidate)
    return False  # Continue searching

search.execute(callback)
```

---

## Complete Example

Here's a complete example demonstrating most of the API:

```python
import apyds

# Configure buffer size for operations
apyds.buffer_size(2048)

# Create terms
var = apyds.Variable("`X")
item = apyds.Item("hello")
lst = apyds.List("(a b c)")
term = apyds.Term("(f `x `y)")

print(f"Variable: {var}, name: {var.name}")
print(f"Item: {item}, name: {item.name}")
print(f"List: {lst}, length: {len(lst)}")
print(f"Term: {term}, type: {type(term.term)}")

# Work with rules
fact = apyds.Rule("(parent john mary)")
rule = apyds.Rule("(father `X `Y)\n----------\n(parent `X `Y)\n")

print(f"\nFact: {fact}")
print(f"Rule premises: {len(rule)}, conclusion: {rule.conclusion}")

# Grounding
term_a = apyds.Term("`a")
dictionary = apyds.Term("((`a hello))")
grounded = term_a // dictionary
print(f"\nGrounding `a with ((` hello)): {grounded}")

# Matching
mp = apyds.Rule("(`p -> `q)\n`p\n`q\n")
axiom = apyds.Rule("((A) -> B)")
matched = mp @ axiom
print(f"\nMatching modus ponens with (A -> B):\n{matched}")

# Search engine
search = apyds.Search(1000, 10000)
search.add("p q")  # p implies q
search.add("q r")  # q implies r
search.add("p")    # fact: p

print("\nRunning inference:")
for i in range(3):
    count = search.execute(lambda r: print(f"  Derived: {r}") or False)
    if count == 0:
        break

# Using context manager for buffer size
with apyds.scoped_buffer_size(4096):
    big_term = apyds.Term("(a b c d e f g h i j)")
    print(f"\nBig term: {big_term}")
```
