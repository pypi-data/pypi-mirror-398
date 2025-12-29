# Installation

DS can be installed for TypeScript/JavaScript, Python, or used directly as a C++ library.

## TypeScript/JavaScript

The TypeScript/JavaScript package `atsds` wraps the C++ core via WebAssembly.

```bash
npm install atsds
```

The package includes:

- WebAssembly binaries (`.wasm`)
- TypeScript type definitions (`.d.mts`)
- ES module support

### Requirements

- Node.js 20+ or a modern browser with WebAssembly support

### Browser Usage

The package works in browsers that support WebAssembly:

```html
<script type="module">
  import { Term } from "https://unpkg.com/atsds/dist/index.mjs";
  
  const term = new Term("(hello world)");
  console.log(term.toString());
</script>
```

## Python

The Python package `apyds` wraps the C++ core via pybind11.

```bash
pip install apyds
```

### Requirements

- Python 3.11-3.14
- Pre-built wheels are available for common platforms (Linux, macOS, Windows)

### Virtual Environment (Recommended)

It's recommended to use a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install apyds
```

### Development Installation

To install from source with development dependencies:

```bash
git clone https://github.com/USTC-KnowledgeComputingLab/ds.git
cd ds
uv sync --extra dev
```

## C++

The C++ library is the core implementation. Both Python and TypeScript bindings are built on top of it.

### Prerequisites

- C++20 compatible compiler (GCC 10+, Clang 10+, MSVC 2019+)
- CMake 3.30+

### Using vcpkg

Clone the repository and use the overlay port:

```bash
git clone https://github.com/USTC-KnowledgeComputingLab/ds.git
vcpkg install ds --overlay-ports=./ds/ports
```

Add to your `vcpkg.json`:

```json
{
  "dependencies": ["ds"]
}
```

In your CMakeLists.txt:

```cmake
find_package(ds CONFIG REQUIRED)
target_link_libraries(your_target PRIVATE ds::ds)
```

### Building from Source

```bash
git clone https://github.com/USTC-KnowledgeComputingLab/ds.git
cd ds
cmake -B build
cmake --build build
```

### Using in Your Project

Include the headers from `include/ds/` in your C++ project:

```cpp
#include <ds/ds.hh>
#include <ds/search.hh>
```

Link against the `ds` static library produced by the build.

## Building All Components

To build all language bindings from source:

### TypeScript/JavaScript (requires Emscripten)

```bash
# Install Emscripten SDK first
# https://emscripten.org/docs/getting_started/downloads.html

npm install
npm run build
```

### Python

```bash
uv sync --extra dev
```

### C++

```bash
cmake -B build
cmake --build build
```

## Running Tests

After installation, you can verify everything works by running the tests:

### TypeScript/JavaScript Tests

```bash
npm test
```

### Python Tests

```bash
uv run pytest
```

### C++ Tests

```bash
cd build
ctest
```

## Verifying Installation

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
