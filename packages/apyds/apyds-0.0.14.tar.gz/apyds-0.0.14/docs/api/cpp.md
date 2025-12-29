# C++ API Reference

This page documents the C++ API for the DS library. The documentation is generated from the C++ source code.

All classes and functions are in the `ds` namespace.

## Headers

```cpp
#include <ds/ds.hh>        // All basic types
#include <ds/search.hh>    // Search engine
#include <ds/utility.hh>   // Helper functions
```

---

## string_t

String handling class. Defined in `<ds/string.hh>`.

### Methods

#### data_size()

Get the size of the string data in bytes.

```cpp
length_t data_size();
```

#### head()

Get a pointer to the first byte.

```cpp
std::byte* head();
```

#### tail()

Get a pointer past the last byte.

```cpp
std::byte* tail();
```

#### print()

Output the string to a buffer.

```cpp
char* print(char* buffer, char* check_tail = nullptr);
```

#### scan()

Read a string from a buffer.

```cpp
const char* scan(const char* buffer, std::byte* check_tail = nullptr);
```

---

## variable_t

Logical variable class. Defined in `<ds/variable.hh>`.

Variables represent placeholders that can be unified with other terms.

### Methods

#### name()

Get the name of the variable (without backtick prefix).

```cpp
string_t* name();
```

#### data_size()

Get the size of the variable data in bytes.

```cpp
length_t data_size();
```

#### head() / tail()

Get pointers to the data boundaries.

```cpp
std::byte* head();
std::byte* tail();
```

#### print() / scan()

Input/output operations.

```cpp
char* print(char* buffer, char* check_tail = nullptr);
const char* scan(const char* buffer, std::byte* check_tail = nullptr);
```

---

## item_t

Item (constant/functor) class. Defined in `<ds/item.hh>`.

Items represent atomic values or function symbols.

### Methods

#### name()

Get the name of the item.

```cpp
string_t* name();
```

#### data_size()

Get the size of the item data in bytes.

```cpp
length_t data_size();
```

#### head() / tail()

Get pointers to the data boundaries.

```cpp
std::byte* head();
std::byte* tail();
```

#### print() / scan()

Input/output operations.

```cpp
char* print(char* buffer, char* check_tail = nullptr);
const char* scan(const char* buffer, std::byte* check_tail = nullptr);
```

---

## list_t

List class. Defined in `<ds/list.hh>`.

Lists contain ordered sequences of terms.

### Methods

#### length()

Get the number of elements in the list.

```cpp
length_t length();
```

#### getitem()

Get an element by index.

```cpp
term_t* getitem(length_t index);
```

#### data_size()

Get the size of the list data in bytes.

```cpp
length_t data_size();
```

#### head() / tail()

Get pointers to the data boundaries.

```cpp
std::byte* head();
std::byte* tail();
```

#### print() / scan()

Input/output operations.

```cpp
char* print(char* buffer, char* check_tail = nullptr);
const char* scan(const char* buffer, std::byte* check_tail = nullptr);
```

---

## term_t

General term class. Defined in `<ds/term.hh>`.

A term can be a variable, item, or list.

### Enum: term_type_t

```cpp
enum class term_type_t : min_uint_t {
    null = 0,
    variable = 1,
    item = 2,
    list = 3
};
```

### Methods

#### get_type()

Get the type of this term.

```cpp
term_type_t get_type();
```

#### is_null()

Check if the term is null.

```cpp
bool is_null();
```

#### variable() / item() / list()

Get the underlying value as the specific type. Returns nullptr if the term is not of that type.

```cpp
variable_t* variable();
item_t* item();
list_t* list();
```

#### set_type() / set_null() / set_variable() / set_item() / set_list()

Set the term type.

```cpp
term_t* set_type(term_type_t type, std::byte* check_tail = nullptr);
term_t* set_null(std::byte* check_tail = nullptr);
term_t* set_variable(std::byte* check_tail = nullptr);
term_t* set_item(std::byte* check_tail = nullptr);
term_t* set_list(std::byte* check_tail = nullptr);
```

#### data_size()

Get the size of the term data in bytes.

```cpp
length_t data_size();
```

#### head() / tail()

Get pointers to the data boundaries.

```cpp
std::byte* head();
std::byte* tail();
```

#### print() / scan()

Input/output operations.

```cpp
char* print(char* buffer, char* check_tail = nullptr);
const char* scan(const char* buffer, std::byte* check_tail = nullptr);
```

#### ground()

Ground this term using a dictionary to substitute variables.

```cpp
term_t* ground(term_t* term, term_t* dictionary, const char* scope, 
               std::byte* check_tail = nullptr);
```

#### match()

Match two terms and produce a unification dictionary.

```cpp
term_t* match(term_t* term_1, term_t* term_2, 
              const char* scope_1, const char* scope_2, 
              std::byte* check_tail = nullptr);
```

#### rename()

Rename variables by adding prefix and suffix.

```cpp
term_t* rename(term_t* term, term_t* prefix_and_suffix, 
               std::byte* check_tail = nullptr);
```

---

## rule_t

Logical rule class. Defined in `<ds/rule.hh>`.

A rule consists of premises and a conclusion.

### Methods

#### conclusion()

Get the conclusion of the rule.

```cpp
term_t* conclusion();
```

#### only_conclusion()

Get the conclusion only if there are no premises. Returns nullptr otherwise.

```cpp
term_t* only_conclusion();
```

#### premises()

Get a premise by index.

```cpp
term_t* premises(length_t index);
```

#### premises_count()

Get the number of premises.

```cpp
length_t premises_count();
```

#### valid()

Check if the rule is valid.

```cpp
bool valid();
```

#### data_size()

Get the size of the rule data in bytes.

```cpp
length_t data_size();
```

#### head() / tail()

Get pointers to the data boundaries.

```cpp
std::byte* head();
std::byte* tail();
```

#### print() / scan()

Input/output operations.

```cpp
char* print(char* buffer, char* check_tail = nullptr);
const char* scan(const char* buffer, std::byte* check_tail = nullptr);
```

#### ground()

Ground this rule using a dictionary.

```cpp
rule_t* ground(rule_t* rule, term_t* dictionary, const char* scope, 
               std::byte* check_tail = nullptr);
rule_t* ground(rule_t* rule, rule_t* dictionary, const char* scope, 
               std::byte* check_tail = nullptr);
```

#### match()

Match this rule with a fact.

```cpp
rule_t* match(rule_t* rule_1, rule_t* rule_2, 
              std::byte* check_tail = nullptr);
```

#### rename()

Rename variables in this rule.

```cpp
rule_t* rename(rule_t* rule, rule_t* prefix_and_suffix, 
               std::byte* check_tail = nullptr);
```

---

## search_t

Search engine class. Defined in `<ds/search.hh>`.

Manages a knowledge base and performs logical inference.

### Constructor

```cpp
search_t(length_t limit_size, length_t buffer_size);
```

**Parameters:**

- `limit_size`: Maximum size for each stored rule/fact
- `buffer_size`: Size of the internal buffer for operations

### Methods

#### set_limit_size()

Set the maximum rule/fact size.

```cpp
void set_limit_size(length_t limit_size);
```

#### set_buffer_size()

Set the internal buffer size.

```cpp
void set_buffer_size(length_t buffer_size);
```

#### reset()

Clear all rules and facts.

```cpp
void reset();
```

#### add()

Add a rule or fact from text.

```cpp
bool add(std::string_view text);
```

#### execute()

Execute one round of inference.

```cpp
length_t execute(const std::function<bool(rule_t*)>& callback);
```

**Parameters:**

- `callback`: Function called for each new inference. Return false to continue, true to stop.

**Returns:** The number of new inferences generated.

---

## Utility Functions

Helper functions in `<ds/utility.hh>`.

### text_to_term()

Parse text into a term object.

```cpp
std::unique_ptr<term_t> text_to_term(const char* text, length_t length);
```

**Parameters:**

- `text`: The text representation of the term
- `length`: Maximum size for the resulting binary term

**Returns:** A unique_ptr to the created term, or nullptr if length exceeded.

### term_to_text()

Convert a term object to text.

```cpp
std::unique_ptr<char> term_to_text(term_t* term, length_t length);
```

**Parameters:**

- `term`: The binary term to convert
- `length`: Maximum size for the resulting text

**Returns:** A unique_ptr to the text, or nullptr if length exceeded.

### text_to_rule()

Parse text into a rule object.

```cpp
std::unique_ptr<rule_t> text_to_rule(const char* text, length_t length);
```

**Parameters:**

- `text`: The text representation of the rule
- `length`: Maximum size for the resulting binary rule

**Returns:** A unique_ptr to the created rule, or nullptr if length exceeded.

### rule_to_text()

Convert a rule object to text.

```cpp
std::unique_ptr<char> rule_to_text(rule_t* rule, length_t length);
```

**Parameters:**

- `rule`: The binary rule to convert
- `length`: Maximum size for the resulting text

**Returns:** A unique_ptr to the text, or nullptr if length exceeded.

---

## Complete Example

Here's a complete example demonstrating the C++ API:

```cpp
#include <ds/ds.hh>
#include <ds/search.hh>
#include <ds/utility.hh>
#include <cstring>
#include <iostream>

int main() {
    const int buffer_size = 1000;
    
    // Create terms using utility functions
    auto term = ds::text_to_term("(f `x `y)", buffer_size);
    
    std::cout << "Term: " << ds::term_to_text(term.get(), buffer_size).get() << std::endl;
    
    // Work with rules
    auto fact = ds::text_to_rule("(parent john mary)", buffer_size);
    auto rule = ds::text_to_rule("(father `X `Y)\n----------\n(parent `X `Y)\n", buffer_size);
    
    std::cout << "\nFact:\n" << ds::rule_to_text(fact.get(), buffer_size).get();
    std::cout << "Rule premises: " << rule->premises_count() << std::endl;
    std::cout << "Rule conclusion: " << ds::term_to_text(rule->conclusion(), buffer_size).get() << std::endl;
    
    // Search engine
    ds::search_t search(1000, 10000);
    
    // Add rules and facts
    search.add("p q");  // p implies q
    search.add("q r");  // q implies r
    search.add("p");    // fact: p
    
    std::cout << "\nRunning inference:" << std::endl;
    
    // Execute search
    auto target = ds::text_to_rule("r", buffer_size);
    bool found = false;
    
    while (!found) {
        auto count = search.execute([&](ds::rule_t* candidate) {
            std::cout << "  Derived: " << ds::rule_to_text(candidate, buffer_size).get();
            
            // Check if this is our target
            if (candidate->data_size() == target->data_size() &&
                memcmp(candidate->head(), target->head(), candidate->data_size()) == 0) {
                found = true;
                return true;  // Stop
            }
            return false;  // Continue
        });
        
        if (count == 0) {
            std::cout << "  (no more inferences)" << std::endl;
            break;
        }
    }
    
    if (found) {
        std::cout << "Target found!" << std::endl;
    }
    
    return 0;
}
```
