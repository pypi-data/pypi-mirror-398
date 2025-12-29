# TypeScript API Reference

This page documents the TypeScript API for the `atsds` package. The documentation is generated from the TypeScript source code.

```typescript
import { 
    buffer_size,
    String_, 
    Variable, 
    Item, 
    List, 
    Term, 
    Rule, 
    Search 
} from "atsds";
```

## buffer_size

Gets the current buffer size, or sets a new buffer size and returns the previous value.

```typescript
function buffer_size(size?: number): number;
```

**Parameters:**

- `size` (optional): The new buffer size to set. If 0 or omitted, returns current size without modification.

**Returns:** The previous buffer size value.

**Example:**

```typescript
const currentSize = buffer_size();     // Get current size
const oldSize = buffer_size(2048);     // Set new size, returns old size
```

---

## String_

Wrapper class for deductive system strings.

### Constructor

```typescript
constructor(value: string | Buffer | String_, size?: number)
```

**Parameters:**

- `value`: Initial value (string, buffer, or another String_)
- `size` (optional): Buffer capacity for internal storage

### Methods

#### toString()

Convert the value to a string representation.

```typescript
toString(): string
```

#### data()

Get the binary representation of the value.

```typescript
data(): Buffer
```

#### size()

Get the size of the data in bytes.

```typescript
size(): number
```

#### copy()

Create a deep copy of this instance.

```typescript
copy(): String_
```

#### key()

Get a key representation for equality comparison.

```typescript
key(): string
```

**Example:**

```typescript
const str1 = new String_("hello");
const str2 = new String_(str1.data());
console.log(str1.toString());  // "hello"
```

---

## Variable

Wrapper class for logical variables in the deductive system.

### Constructor

```typescript
constructor(value: string | Buffer | Variable, size?: number)
```

**Parameters:**

- `value`: Initial value (string starting with backtick, buffer, or another Variable)
- `size` (optional): Buffer capacity for internal storage

### Methods

Inherits all methods from `String_`, plus:

#### name()

Get the name of this variable (without the backtick prefix).

```typescript
name(): String_
```

**Example:**

```typescript
const var1 = new Variable("`X");
console.log(var1.name().toString());  // "X"
console.log(var1.toString());         // "`X"
```

---

## Item

Wrapper class for items (constants/functors) in the deductive system.

### Constructor

```typescript
constructor(value: string | Buffer | Item, size?: number)
```

### Methods

Inherits all methods from `String_`, plus:

#### name()

Get the name of this item.

```typescript
name(): String_
```

**Example:**

```typescript
const item = new Item("atom");
console.log(item.name().toString());  // "atom"
```

---

## List

Wrapper class for lists in the deductive system.

### Constructor

```typescript
constructor(value: string | Buffer | List, size?: number)
```

### Methods

Inherits all methods from `String_`, plus:

#### length()

Get the number of elements in the list.

```typescript
length(): number
```

#### getitem()

Get an element from the list by index.

```typescript
getitem(index: number): Term
```

**Example:**

```typescript
const list = new List("(a b c)");
console.log(list.length());           // 3
console.log(list.getitem(0).toString());  // "a"
```

---

## Term

Wrapper class for logical terms in the deductive system. A term can be a variable, item, or list.

### Constructor

```typescript
constructor(value: string | Buffer | Term, size?: number)
```

### Methods

Inherits all methods from `String_`, plus:

#### term()

Extracts the underlying term and returns it as its concrete type.

```typescript
term(): Variable | Item | List
```

#### ground()

Ground this term using a dictionary to substitute variables with values.

```typescript
ground(other: Term, scope?: string): Term | null
```

**Parameters:**

- `other`: A term representing a dictionary (list of pairs)
- `scope` (optional): Scope string for variable scoping

**Returns:** The grounded term, or null if grounding fails.

**Example:**

```typescript
const a = new Term("`a");
const dict = new Term("((`a b))");
const result = a.ground(dict);
if (result !== null) {
    console.log(result.toString());  // "b"
}
```

#### match()

Match two terms and return the unification result as a dictionary.

```typescript
match(other: Term): Term | null
```

**Parameters:**

- `other`: The term to match with this term

**Returns:** A term representing the unification dictionary (list of tuples), or null if matching fails.

**Example:**

```typescript
const a = new Term("`a");
const b = new Term("b");
const result = a.match(b);
if (result !== null) {
    console.log(result.toString());  // "((1 2 `a b))"
}
```

#### rename()

Rename all variables in this term by adding prefix and suffix.

```typescript
rename(prefix_and_suffix: Term): Term | null
```

**Parameters:**

- `prefix_and_suffix`: A term with format `((prefix) (suffix))`

**Returns:** The renamed term, or null if renaming fails.

**Example:**

```typescript
const term = new Term("`x");
const spec = new Term("((pre_) (_suf))");
const result = term.rename(spec);
if (result !== null) {
    console.log(result.toString());  // "`pre_x_suf"
}
```

---

## Rule

Wrapper class for logical rules in the deductive system.

### Constructor

```typescript
constructor(value: string | Buffer | Rule, size?: number)
```

### Methods

Inherits all methods from `String_`, plus:

#### length()

Get the number of premises in the rule.

```typescript
length(): number
```

#### getitem()

Get a premise term by index.

```typescript
getitem(index: number): Term
```

#### conclusion()

Get the conclusion of the rule.

```typescript
conclusion(): Term
```

#### ground()

Ground this rule using a dictionary.

```typescript
ground(other: Rule, scope?: string): Rule | null
```

#### match()

Match this rule with another rule using unification.

```typescript
match(other: Rule): Rule | null
```

**Parameters:**

- `other`: The rule to match against (must be a fact without premises)

**Returns:** The matched rule, or null if matching fails.

**Example:**

```typescript
const mp = new Rule("(`p -> `q)\n`p\n`q\n");
const pq = new Rule("((! (! `x)) -> `x)");
const result = mp.match(pq);
if (result !== null) {
    console.log(result.toString());
    // "(! (! `x))\n----------\n`x\n"
}
```

#### rename()

Rename all variables in this rule.

```typescript
rename(prefix_and_suffix: Rule): Rule | null
```

---

## Search

Search engine for the deductive system.

### Constructor

```typescript
constructor(limit_size?: number, buffer_size?: number)
```

**Parameters:**

- `limit_size` (optional): Size of the buffer for storing rules/facts (default: 1000)
- `buffer_size` (optional): Size of the buffer for internal operations (default: 10000)

### Methods

#### set_limit_size()

Set the size of the buffer for storing final objects.

```typescript
set_limit_size(limit_size: number): void
```

#### set_buffer_size()

Set the buffer size for internal operations.

```typescript
set_buffer_size(buffer_size: number): void
```

#### reset()

Reset the search engine, clearing all rules and facts.

```typescript
reset(): void
```

#### add()

Add a rule or fact to the knowledge base.

```typescript
add(text: string): boolean
```

**Returns:** True if successfully added, false otherwise.

#### execute()

Execute the search engine with a callback for each inferred rule.

```typescript
execute(callback: (candidate: Rule) => boolean): number
```

**Parameters:**

- `callback`: Function called for each candidate rule. Return false to continue, true to stop.

**Returns:** The number of rules processed.

**Example:**

```typescript
const search = new Search(1000, 10000);
search.add("(`P -> `Q) `P `Q");
search.add("(! (! X))");

search.execute((candidate) => {
    console.log(candidate.toString());
    return false;  // Continue searching
});
```

---

## Complete Example

Here's a complete example demonstrating most of the TypeScript API:

```typescript
import { 
    buffer_size, 
    String_, 
    Variable, 
    Item, 
    List, 
    Term, 
    Rule, 
    Search 
} from "atsds";

// Configure buffer size
buffer_size(2048);

// Create terms
const varX = new Variable("`X");
const item = new Item("hello");
const lst = new List("(a b c)");
const term = new Term("(f `x `y)");

console.log(`Variable: ${varX.toString()}, name: ${varX.name().toString()}`);
console.log(`Item: ${item.toString()}, name: ${item.name().toString()}`);
console.log(`List: ${lst.toString()}, length: ${lst.length()}`);
console.log(`Term: ${term.toString()}`);

// Work with rules
const fact = new Rule("(parent john mary)");
const rule = new Rule("(father `X `Y)\n----------\n(parent `X `Y)\n");

console.log(`\nFact: ${fact.toString()}`);
console.log(`Rule premises: ${rule.length()}, conclusion: ${rule.conclusion().toString()}`);

// Grounding
const termA = new Term("`a");
const dictionary = new Term("((`a hello))");
const grounded = termA.ground(dictionary);
if (grounded) {
    console.log(`\nGrounding \`a with ((\`a hello)): ${grounded.toString()}`);
}

// Matching
const mp = new Rule("(`p -> `q)\n`p\n`q\n");
const axiom = new Rule("((A) -> B)");
const matched = mp.match(axiom);
if (matched) {
    console.log(`\nMatching modus ponens with (A -> B):\n${matched.toString()}`);
}

// Search engine
const search = new Search(1000, 10000);
search.add("p q");  // p implies q
search.add("q r");  // q implies r
search.add("p");    // fact: p

console.log("\nRunning inference:");
for (let i = 0; i < 3; i++) {
    const count = search.execute((r) => {
        console.log(`  Derived: ${r.toString()}`);
        return false;
    });
    if (count === 0) break;
}

// Copying and comparison
const rule1 = new Rule("(a b c)");
const rule2 = rule1.copy();
console.log(`\nRule comparison: ${rule1.key() === rule2.key()}`);  // true
```
