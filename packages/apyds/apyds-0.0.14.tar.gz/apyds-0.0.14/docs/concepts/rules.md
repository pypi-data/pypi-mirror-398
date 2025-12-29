# Rules

Rules are the core mechanism for representing logical inference in DS. This page explains how rules work and how to use them.

## Rule Structure

A rule consists of:

- **Premises**: Zero or more conditions (above the line)
- **Conclusion**: The result when all premises are satisfied (below the line)

### Text Representation

Rules are written with premises and conclusion separated by dashes (at least four dashes):

```
premise1
premise2
----------
conclusion
```

A **fact** is a rule with no premises:

```
(parent john mary)
```

Or explicitly:

```
----------
(parent john mary)
```

!!! info "Rule Format Details"
    - Premises are separated by newlines
    - The separator line must contain at least 4 dashes (`----`) between premises and conclusion
    - Whitespace around premises and conclusion is trimmed
    - A rule without an premises is a fact

### Compact Rule Format

For rules with multiple premises, you can use space-separated terms on a single line:

```
(`P -> `Q) `P `Q
```

This is equivalent to:

```
(`P -> `Q)
`P
----------
`Q
```

The last term is the conclusion, and all preceding terms are premises.

### Examples

**Modus Ponens** (if P implies Q and P is true, then Q is true):

```
(`P -> `Q)
`P
----------
`Q
```

**Family Relationship** (if X is the father of Y, then X is a parent of Y):

```
(father `X `Y)
----------
(parent `X `Y)
```

## Creating Rules

=== "TypeScript"

    ```typescript
    import { Rule } from "atsds";

    // Create a fact
    const fact = new Rule("(parent john mary)");

    // Create a rule with premises
    const rule = new Rule("(father `X `Y)\n----------\n(parent `X `Y)\n");

    // Access rule components
    console.log(`Number of premises: ${rule.length()}`);  // 1
    console.log(`First premise: ${rule.getitem(0).toString()}`);  // (father `X `Y)
    console.log(`Conclusion: ${rule.conclusion().toString()}`);  // (parent `X `Y)
    ```

=== "Python"

    ```python
    import apyds

    # Create a fact
    fact = apyds.Rule("(parent john mary)")

    # Create a rule with premises
    # Using explicit separator
    rule = apyds.Rule("(father `X `Y)\n----------\n(parent `X `Y)\n")

    # Access rule components
    print(f"Number of premises: {len(rule)}")  # 1
    print(f"First premise: {rule[0]}")  # (father `X `Y)
    print(f"Conclusion: {rule.conclusion}")  # (parent `X `Y)
    ```

=== "C++"

    ```cpp
    #include <ds/ds.hh>
    #include <ds/utility.hh>
    #include <iostream>

    int main() {
        // Create a fact
        auto fact = ds::text_to_rule("(parent john mary)", 1000);

        // Create a rule with premises
        auto rule = ds::text_to_rule("(father `X `Y)\n----------\n(parent `X `Y)\n", 1000);

        // Access rule components
        std::cout << "Number of premises: " << rule->premises_count() << std::endl;
        std::cout << "Conclusion: " << ds::term_to_text(rule->conclusion(), 1000).get() << std::endl;

        return 0;
    }
    ```

## Rule Operations

### Grounding

Grounding substitutes variables in a rule with values from a dictionary.

=== "TypeScript"

    ```typescript
    import { Rule } from "atsds";

    // Create a rule with variables
    const rule = new Rule("`a");

    // Create a dictionary
    const dictionary = new Rule("((`a b))");

    // Ground the rule
    const result = rule.ground(dictionary);
    if (result !== null) {
        console.log(result.toString());  // ----\nb\n
    }
    ```

=== "Python"

    ```python
    import apyds

    # Create a rule with variables
    rule = apyds.Rule("`a")

    # Create a dictionary
    dictionary = apyds.Rule("((`a b))")

    # Ground the rule
    result = rule.ground(dictionary)
    print(result)  # ----\nb\n
    ```

=== "C++"

    ```cpp
    #include <ds/ds.hh>
    #include <ds/utility.hh>
    #include <iostream>

    int main() {
        // Create a rule with variables
        auto rule = ds::text_to_rule("`a", 1000);

        // Create a dictionary
        auto dictionary = ds::text_to_rule("((`a b))", 1000);

        // Ground the rule
        std::byte buffer[1000];
        auto result = reinterpret_cast<ds::rule_t*>(buffer);
        result->ground(rule.get(), dictionary.get(), nullptr, buffer + 1000);

        std::cout << ds::rule_to_text(result, 1000).get() << std::endl;  // ----\nb\n

        return 0;
    }
    ```

### Matching

Matching unifies the first premise of a rule with a fact, producing a new rule with one fewer premise.

=== "TypeScript"

    ```typescript
    import { Rule } from "atsds";

    // Modus ponens rule
    const mp = new Rule("(`p -> `q)\n`p\n`q\n");

    // Double negation elimination axiom
    const axiom = new Rule("((! (! `x)) -> `x)");

    // Match
    const result = mp.match(axiom);
    if (result !== null) {
        console.log(result.toString());
        // (! (! `x))
        // ----------
        // `x
    }
    ```

=== "Python"

    ```python
    import apyds

    # Modus ponens rule: if (P -> Q) and P then Q
    mp = apyds.Rule("(`p -> `q)\n`p\n`q\n")

    # A fact: double negation elimination axiom
    axiom = apyds.Rule("((! (! `x)) -> `x)")

    # Match: apply axiom to modus ponens
    result = mp @ axiom  # Uses @ operator
    print(result)
    # Output:
    # (! (! `x))
    # ----------
    # `x
    ```

=== "C++"

    ```cpp
    #include <ds/ds.hh>
    #include <ds/utility.hh>
    #include <iostream>

    int main() {
        // Modus ponens rule
        auto mp = ds::text_to_rule("(`p -> `q)\n`p\n`q\n", 1000);

        // Double negation elimination axiom
        auto axiom = ds::text_to_rule("((! (! `x)) -> `x)", 1000);

        // Match
        std::byte buffer[1000];
        auto result = reinterpret_cast<ds::rule_t*>(buffer);
        result->match(mp.get(), axiom.get(), buffer + 1000);

        std::cout << ds::rule_to_text(result, 1000).get() << std::endl;

        return 0;
    }
    ```

### Renaming

Renaming adds prefixes and/or suffixes to all variables in a rule.

=== "TypeScript"

    ```typescript
    import { Rule } from "atsds";

    // Create a rule
    const rule = new Rule("`x");

    // Rename with prefix and suffix
    const spec = new Rule("((pre_) (_suf))");
    const result = rule.rename(spec);
    if (result !== null) {
        console.log(result.toString());  // ----\n`pre_x_suf\n
    }
    ```

=== "Python"

    ```python
    import apyds

    # Create a rule
    rule = apyds.Rule("`x")

    # Rename with prefix and suffix
    spec = apyds.Rule("((pre_) (_suf))")
    result = rule.rename(spec)
    print(result)  # ----\n`pre_x_suf\n
    ```

=== "C++"

    ```cpp
    #include <ds/ds.hh>
    #include <ds/utility.hh>
    #include <iostream>

    int main() {
        // Create a rule
        auto rule = ds::text_to_rule("`x", 1000);

        // Rename with prefix and suffix
        auto spec = ds::text_to_rule("((pre_) (_suf))", 1000);

        // Rename the rule
        std::byte buffer[1000];
        auto result = reinterpret_cast<ds::rule_t*>(buffer);
        result->rename(rule.get(), spec.get(), buffer + 1000);

        std::cout << ds::rule_to_text(result, 1000).get() << std::endl;  // ----\n`pre_x_suf\n

        return 0;
    }
    ```

## Rule Comparison

Rules can be compared for equality. Two rules are equal if they have the same binary representation.

=== "TypeScript"

    ```typescript
    import { Rule } from "atsds";

    const rule1 = new Rule("(a b c)");
    const rule2 = new Rule("(a b c)");
    const rule3 = new Rule("(a b d)");

    console.log(rule1.key() === rule2.key());  // true
    console.log(rule1.key() === rule3.key());  // false
    ```

=== "Python"

    ```python
    import apyds

    rule1 = apyds.Rule("(a b c)")
    rule2 = apyds.Rule("(a b c)")
    rule3 = apyds.Rule("(a b d)")

    print(rule1 == rule2)  # True
    print(rule1 == rule3)  # False
    ```

=== "C++"

    ```cpp
    #include <ds/ds.hh>
    #include <ds/utility.hh>
    #include <cstring>
    #include <iostream>

    int main() {
        auto rule1 = ds::text_to_rule("(a b c)", 1000);
        auto rule2 = ds::text_to_rule("(a b c)", 1000);
        auto rule3 = ds::text_to_rule("(a b d)", 1000);

        bool eq12 = rule1->data_size() == rule2->data_size() &&
                    memcmp(rule1->head(), rule2->head(), rule1->data_size()) == 0;
        bool eq13 = rule1->data_size() == rule3->data_size() &&
                    memcmp(rule1->head(), rule3->head(), rule1->data_size()) == 0;

        std::cout << std::boolalpha;
        std::cout << eq12 << std::endl;  // true
        std::cout << eq13 << std::endl;  // false

        return 0;
    }
    ```

## See Also

- [Terms](terms.md) - Building blocks for rules
- [Search Engine](search.md) - Performing inference with rules
