# Search Engine

The search engine is the core inference mechanism in DS. It manages a knowledge base of rules and facts, and performs logical inference by matching rules with facts.

## Overview

The search engine:

1. Maintains a collection of rules and facts
2. Iteratively applies rules to generate new facts
3. Notifies you of each new inference via a callback
4. Automatically prevents duplicate inferences

!!! info "How It Works"
    The search engine uses a forward-chaining inference approach:
    
    1. When you call `execute()`, the engine tries to match the first premise of each rule with existing facts
    2. When a match is found, variables in the rule are substituted and a new rule (with one fewer premise) is created
    3. If the new rule has no premises, it becomes a new fact
    4. The callback is invoked for each newly derived rule
    5. Duplicate rules are automatically filtered out

## Creating a Search Engine

=== "TypeScript"

    ```typescript
    import { Search } from "atsds";

    // Create with default sizes
    const search = new Search();

    // Create with custom sizes
    const search2 = new Search(1000, 10000);
    ```

=== "Python"

    ```python
    import apyds

    # Create with default sizes
    search = apyds.Search()

    # Create with custom sizes
    search = apyds.Search(limit_size=1000, buffer_size=10000)
    ```

=== "C++"

    ```cpp
    #include <ds/search.hh>

    // Create search engine
    ds::search_t search(1000, 10000);
    ```

### Parameters

- **limit_size**: Maximum size (in bytes) for each stored rule/fact (default: 1000). Rules or facts larger than this are rejected.
- **buffer_size**: Size of the internal buffer for intermediate operations (default: 10000). Increase this if you work with complex rules.

## Adding Rules and Facts

Use the `add()` method to add rules and facts to the knowledge base.

=== "TypeScript"

    ```typescript
    import { Search } from "atsds";

    const search = new Search();

    // Add a fact
    search.add("(parent john mary)");

    // Add a rule with premises
    search.add("(father `X `Y)\n----------\n(parent `X `Y)\n");
    ```

=== "Python"

    ```python
    import apyds

    search = apyds.Search()

    # Add a fact
    search.add("(parent john mary)")

    # Add a rule with premises
    search.add("(father `X `Y)\n----------\n(parent `X `Y)\n")
    ```

=== "C++"

    ```cpp
    ds::search_t search(1000, 10000);

    // Add a fact
    search.add("(parent john mary)");

    // Add a rule
    search.add("(father `X `Y)\n----------\n(parent `X `Y)\n");
    ```

## Executing Search

The `execute()` method performs one round of inference. It matches all rules against all facts and generates new conclusions.

=== "TypeScript"

    ```typescript
    import { Search } from "atsds";

    const search = new Search();
    search.add("(father `X `Y)\n----------\n(parent `X `Y)\n");
    search.add("(father john mary)");

    const count = search.execute((rule) => {
        console.log(`Found: ${rule.toString()}`);
        return false;  // Continue searching
    });

    console.log(`Generated ${count} new facts`);
    ```

=== "Python"

    ```python
    import apyds

    search = apyds.Search()
    search.add("(father `X `Y)\n----------\n(parent `X `Y)\n")
    search.add("(father john mary)")

    def callback(rule):
        print(f"Found: {rule}")
        return False  # Continue searching

    # Execute one round
    count = search.execute(callback)
    print(f"Generated {count} new facts")
    ```

=== "C++"

    ```cpp
    ds::search_t search(1000, 10000);
    search.add("(father `X `Y)\n----------\n(parent `X `Y)\n");
    search.add("(father john mary)");

    auto count = search.execute([](ds::rule_t* rule) {
        printf("Found: %s\n", ds::rule_to_text(rule, 1000).get());
        return false;  // Continue searching
    });

    printf("Generated %lu new facts\n", count);
    ```

### Callback Function

The callback receives each newly inferred rule and should return:

- `False` (Python) / `false` (TypeScript/C++): Continue searching
- `True` (Python) / `true` (TypeScript/C++): Stop searching

## Searching for a Target

To search until a specific target is found:

=== "TypeScript"

    ```typescript
    import { Rule, Search } from "atsds";

    const search = new Search(1000, 10000);

    // Set up propositional logic
    search.add("(`P -> `Q) `P `Q");
    search.add("(`p -> (`q -> `p))");
    search.add("((`p -> (`q -> `r)) -> ((`p -> `q) -> (`p -> `r)))");
    search.add("(((! `p) -> (! `q)) -> (`q -> `p))");
    search.add("(! (! X))");

    const target = new Rule("X");

    while (true) {
        let found = false;
        search.execute((candidate) => {
            if (candidate.key() === target.key()) {
                console.log("Found:", candidate.toString());
                found = true;
                return true;
            }
            return false;
        });
        if (found) break;
    }
    ```

=== "Python"

    ```python
    import apyds

    search = apyds.Search(1000, 10000)

    # Set up propositional logic
    search.add("(`P -> `Q) `P `Q")  # Modus ponens
    search.add("(`p -> (`q -> `p))")  # Axiom 1
    search.add("((`p -> (`q -> `r)) -> ((`p -> `q) -> (`p -> `r)))")  # Axiom 2
    search.add("(((! `p) -> (! `q)) -> (`q -> `p))")  # Axiom 3
    search.add("(! (! X))")  # Premise

    target = apyds.Rule("X")

    while True:
        found = False
        def check(candidate):
            global found
            if candidate == target:
                print(f"Found: {candidate}")
                found = True
                return True
            return False
        search.execute(check)
        if found:
            break
    ```

## Configuration Methods

### Set Limit Size

Controls the maximum size for each stored rule/fact:

=== "TypeScript"

    ```typescript
    search.set_limit_size(2000);
    ```

=== "Python"

    ```python
    search.set_limit_size(2000)
    ```

=== "C++"

    ```cpp
    search.set_limit_size(2000);
    ```

### Set Buffer Size

Controls the internal buffer size for operations:

=== "TypeScript"

    ```typescript
    search.set_buffer_size(20000);
    ```

=== "Python"

    ```python
    search.set_buffer_size(20000)
    ```

=== "C++"

    ```cpp
    search.set_buffer_size(20000);
    ```

### Reset

Clears all rules and facts:

=== "TypeScript"

    ```typescript
    search.reset();
    ```

=== "Python"

    ```python
    search.reset()
    ```

=== "C++"

    ```cpp
    search.reset();
    ```

## Performance Considerations

1. **Buffer Size**: Larger buffers allow more complex intermediate results but use more memory
2. **Limit Size**: Restricts maximum rule/fact complexity - too small may reject valid rules
3. **Iterative Execution**: Call `execute()` in a loop to continue inference until convergence
4. **Early Termination**: Return `true` from callback to stop as soon as target is found
5. **Deduplication**: The engine automatically deduplicates facts, avoiding redundant computation

## See Also

- [Terms](terms.md) - Building blocks for the search
- [Rules](rules.md) - How rules are structured and matched
