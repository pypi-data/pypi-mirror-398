# DS - A Deductive System

A deductive system for logical inference, implemented in C++. The library provides bindings for Python (via pybind11) and TypeScript/JavaScript (via Emscripten/WebAssembly).

## Features

- **Multi-Language Support**: Use the same deductive system in C++, Python, or TypeScript/JavaScript
- **Logical Terms**: Work with variables, items (constants/functors), and lists
- **Rule-Based Inference**: Define rules and facts, perform logical deduction
- **Unification and Matching**: Unify terms and match rules
- **Search Engine**: Built-in search mechanism for iterative inference
- **WebAssembly**: Run inference in the browser or Node.js environments
- **Type-Safe**: Strong typing support in TypeScript and Python

## Supported Languages

=== "TypeScript"

    ```typescript
    import { Term } from "atsds";
    
    const term = new Term("(hello world)");
    console.log(term.toString());
    // Output: (hello world)
    ```

=== "Python"

    ```python
    import apyds
    print(f"Version: {apyds.__version__}")
    
    term = apyds.Term("(hello world)")
    print(term)  # (hello world)
    ```

=== "C++"

    ```cpp
    #include <ds/ds.hh>
    #include <ds/utility.hh>
    #include <iostream>
    
    int main() {
        auto term = ds::text_to_term("(hello world)", 1000);
        std::cout << ds::term_to_text(term.get(), 1000).get() << std::endl;
        return 0;
    }
    ```

## Quick Links

- **[Installation](getting-started/installation.md)** - Install DS for your preferred language
- **[Quick Start](getting-started/quickstart.md)** - Get up and running in minutes
- **[Core Concepts](concepts/terms.md)** - Learn about terms, rules, and inference
- **[API Reference](api/python.md)** - Complete API documentation
- **[Examples](examples/basic.md)** - Working code examples

## License

This project is licensed under the GNU General Public License v3.0 or later.
