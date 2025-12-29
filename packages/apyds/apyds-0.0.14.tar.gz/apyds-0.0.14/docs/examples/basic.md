# Basic Examples

This section contains examples demonstrating the DS deductive system in various languages.

## Propositional Logic Inference

The classic example demonstrates double negation elimination using propositional logic axioms:

- **Modus Ponens**: If P implies Q, and P is true, then Q is true
- **Axiom 1**: P → (Q → P)
- **Axiom 2**: (P → (Q → R)) → ((P → Q) → (P → R))
- **Axiom 3**: (¬P → ¬Q) → (Q → P)

Given the premise ¬¬X (double negation of X), we can derive X.

=== "Python"

    ```python
    import apyds

    # Create a search engine
    search = apyds.Search(1000, 10000)

    # Modus ponens: P -> Q, P |- Q
    search.add("(`P -> `Q) `P `Q")
    # Axiom schema 1: p -> (q -> p)
    search.add("(`p -> (`q -> `p))")
    # Axiom schema 2: (p -> (q -> r)) -> ((p -> q) -> (p -> r))
    search.add("((`p -> (`q -> `r)) -> ((`p -> `q) -> (`p -> `r)))")
    # Axiom schema 3: (!p -> !q) -> (q -> p)
    search.add("(((! `p) -> (! `q)) -> (`q -> `p))")

    # Premise: !!X
    search.add("(! (! X))")

    # Target: X (double negation elimination)
    target = apyds.Rule("X")

    # Execute search until target is found
    while True:
        found = False
        def callback(candidate):
            global found
            if candidate == target:
                print("Found:", candidate)
                found = True
                return True  # Stop search
            return False  # Continue searching
        search.execute(callback)
        if found:
            break
    ```

=== "TypeScript"

    ```typescript
    import { Rule, Search } from "atsds";

    // Create a search engine
    const search = new Search(1000, 10000);

    // Modus ponens: P -> Q, P |- Q
    search.add("(`P -> `Q) `P `Q");
    // Axiom schema 1: p -> (q -> p)
    search.add("(`p -> (`q -> `p))");
    // Axiom schema 2: (p -> (q -> r)) -> ((p -> q) -> (p -> r))
    search.add("((`p -> (`q -> `r)) -> ((`p -> `q) -> (`p -> `r)))");
    // Axiom schema 3: (!p -> !q) -> (q -> p)
    search.add("(((! `p) -> (! `q)) -> (`q -> `p))");

    // Premise: !!X
    search.add("(! (! X))");

    // Target: X (double negation elimination)
    const target = new Rule("X");

    // Execute search until target is found
    while (true) {
        let found = false;
        search.execute((candidate) => {
            if (candidate.key() === target.key()) {
                console.log("Found:", candidate.toString());
                found = true;
                return true; // Stop search
            }
            return false; // Continue searching
        });
        if (found) break;
    }
    ```

=== "C++"

    ```cpp
    #include <cstdio>
    #include <cstring>
    #include <ds/ds.hh>
    #include <ds/search.hh>
    #include <ds/utility.hh>

    int main() {
        ds::search_t search(1000, 10000);
        
        // Modus ponens: P -> Q, P |- Q
        search.add("(`P -> `Q) `P `Q");
        // Axiom schema 1: p -> (q -> p)
        search.add("(`p -> (`q -> `p))");
        // Axiom schema 2: (p -> (q -> r)) -> ((p -> q) -> (p -> r))
        search.add("((`p -> (`q -> `r)) -> ((`p -> `q) -> (`p -> `r)))");
        // Axiom schema 3: (!p -> !q) -> (q -> p)
        search.add("(((! `p) -> (! `q)) -> (`q -> `p))");
        
        // Premise: !!X
        search.add("(! (! X))");
        
        // Target: X (double negation elimination)
        auto target = ds::text_to_rule("X", 1000);
        
        // Execute search until target is found
        while (true) {
            bool found = false;
            search.execute([&](ds::rule_t* candidate) {
                if (candidate->data_size() == target->data_size() &&
                    memcmp(candidate->head(), target->head(), candidate->data_size()) == 0) {
                    printf("Found: %s", ds::rule_to_text(candidate, 1000).get());
                    found = true;
                    return true; // Stop search
                }
                return false; // Continue searching
            });
            if (found) break;
        }
        
        return 0;
    }
    ```

## Running the Examples

Example files are provided in the repository under `examples/`:

- `examples/main.py` - Python example
- `examples/main.mjs` - TypeScript/JavaScript example
- `examples/main.cc` - C++ example

### Python

```bash
pip install apyds
python examples/main.py
```

### TypeScript/JavaScript

```bash
npm install atsds
node examples/main.mjs
```

### C++

```bash
cmake -B build
cmake --build build
./build/main
```
