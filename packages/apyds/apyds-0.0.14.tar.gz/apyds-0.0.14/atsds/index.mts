/**
 * TypeScript wrapper for a deductive system implemented in WebAssembly.
 * Provides classes and functions for working with logical terms, rules, and inference.
 */

import create_ds from "./ds.mjs";
import type * as dst from "./ds.d.mts";

const ds: dst.EmbindModule = await create_ds();

let _buffer_size: number = 1024;

/**
 * Gets the current buffer size, or sets a new buffer size and returns the previous value.
 * The buffer size is used for internal operations like conversions and transformations.
 *
 * @param size - The new buffer size to set. If 0 (default), the current size is returned without modification.
 * @returns The previous buffer size value.
 *
 * @example
 * ```typescript
 * const currentSize = buffer_size(); // Get current size
 * const oldSize = buffer_size(2048); // Set new size, returns old size
 * ```
 */
export function buffer_size(size: number = 0): number {
    const old_size = _buffer_size;
    if (size !== 0) {
        _buffer_size = size;
    }
    return old_size;
}

/**
 * Common interface for all deductive system types.
 * @internal
 */
interface Common {
    clone(): Common;
    data_size(): number;
}

/**
 * Static methods interface for deductive system types.
 * @internal
 */
interface StaticCommon<T extends Common> {
    from_binary(buffer: dst.Buffer): T;
    to_binary(value: T): dst.Buffer;
    from_string(text: string, size: number): T;
    to_string(value: T, size: number): string;
}

/**
 * Valid initialization arguments for deductive system types.
 * @internal
 */
type InitialArgument<T extends Common> = _Common<T> | T | string | dst.Buffer | null;

/**
 * Base class for all deductive system wrapper types.
 * Handles initialization, serialization, and common operations.
 * @internal
 */
class _Common<T extends Common> {
    type: StaticCommon<T>;
    value: T;
    capacity: number;

    /**
     * Creates a new instance.
     *
     * @param type - The static type interface for this common type.
     * @param value - Initial value (can be another instance, base value, string, or buffer).
     * @param size - Optional buffer capacity for the internal storage.
     * @throws {Error} If initialization fails or invalid arguments are provided.
     */
    constructor(type: StaticCommon<T>, value: InitialArgument<T>, size: number = 0) {
        this.type = type;
        if (value instanceof _Common) {
            this.value = value.value;
            this.capacity = value.capacity;
            if (size !== 0) {
                throw new Error("Cannot set capacity when copying from another instance.");
            }
        } else if (value instanceof (this.type as unknown as new () => T)) {
            this.value = value;
            this.capacity = size;
        } else if (typeof value === "string") {
            this.capacity = size !== 0 ? size : buffer_size();
            this.value = this.type.from_string(value, this.capacity);
            if (this.value === null) {
                throw new Error("Initialization from a string failed.");
            }
        } else if (value instanceof ds.Buffer) {
            this.value = this.type.from_binary(value);
            this.capacity = this.size();
            if (size !== 0) {
                throw new Error("Cannot set capacity when initializing from bytes.");
            }
        } else {
            throw new Error("Unsupported type for initialization.");
        }
    }

    /**
     * Convert the value to a string representation.
     *
     * @returns The string representation.
     * @throws {Error} If conversion fails.
     */
    toString(): string {
        const result = this.type.to_string(this.value, buffer_size());
        if (result === "") {
            throw new Error("Conversion to string failed.");
        }
        return result;
    }

    /**
     * Get the binary representation of the value.
     *
     * @returns The binary data as a Buffer.
     */
    data(): dst.Buffer {
        return this.type.to_binary(this.value);
    }

    /**
     * Get the size of the data in bytes.
     *
     * @returns The data size.
     */
    size(): number {
        return this.value.data_size();
    }

    /**
     * Create a deep copy of this instance.
     *
     * @returns A new instance with cloned value.
     */
    copy(): this {
        const this_constructor = this.constructor as new (value: T, size: number) => this;
        return new this_constructor(this.value.clone() as T, this.size());
    }

    /**
     * Get a key representation for this value.
     * The key equality is consistent with object equality.
     *
     * @returns The string key.
     */
    key(): string {
        return this.toString();
    }
}

/**
 * Wrapper class for deductive system strings.
 * Supports initialization from strings, buffers, or other instances.
 *
 * @example
 * ```typescript
 * const str1 = new String_("hello");
 * const str2 = new String_(str1.data()); // From binary
 * console.log(str1.toString()); // "hello"
 * ```
 */
export class String_ extends _Common<dst.String> {
    /**
     * Creates a new string instance.
     *
     * @param value - Initial value (string, buffer, or another String_).
     * @param size - Optional buffer capacity for the internal storage.
     * @throws {Error} If initialization fails.
     */
    constructor(value: InitialArgument<dst.String>, size: number = 0) {
        super(ds.String, value, size);
    }
}

/**
 * Wrapper class for logical variables in the deductive system.
 * Variables are used in logical terms and can be unified.
 *
 * @example
 * ```typescript
 * const var1 = new Variable("`X");
 * console.log(var1.name().toString()); // "X"
 * ```
 */
export class Variable extends _Common<dst.Variable> {
    /**
     * Creates a new variable instance.
     *
     * @param value - Initial value (string, buffer, or another Variable).
     * @param size - Optional buffer capacity for the internal storage.
     * @throws {Error} If initialization fails.
     */
    constructor(value: InitialArgument<dst.Variable>, size: number = 0) {
        super(ds.Variable, value, size);
    }

    /**
     * Get the name of this variable.
     *
     * @returns The variable name as a String_.
     */
    name(): String_ {
        return new String_(this.value.name());
    }
}

/**
 * Wrapper class for items in the deductive system.
 * Items represent constants or functors in logical terms.
 *
 * @example
 * ```typescript
 * const item = new Item("atom");
 * console.log(item.name().toString()); // "atom"
 * ```
 */
export class Item extends _Common<dst.Item> {
    /**
     * Creates a new item instance.
     *
     * @param value - Initial value (string, buffer, or another Item).
     * @param size - Optional buffer capacity for the internal storage.
     * @throws {Error} If initialization fails.
     */
    constructor(value: InitialArgument<dst.Item>, size: number = 0) {
        super(ds.Item, value, size);
    }

    /**
     * Get the name of this item.
     *
     * @returns The item name as a String_.
     */
    name(): String_ {
        return new String_(this.value.name());
    }
}

/**
 * Wrapper class for lists in the deductive system.
 * Lists contain ordered sequences of terms.
 *
 * @example
 * ```typescript
 * const list = new List("(a b c)");
 * console.log(list.length()); // 3
 * console.log(list.getitem(0).toString()); // "a"
 * ```
 */
export class List extends _Common<dst.List> {
    /**
     * Creates a new list instance.
     *
     * @param value - Initial value (string, buffer, or another List).
     * @param size - Optional buffer capacity for the internal storage.
     * @throws {Error} If initialization fails.
     */
    constructor(value: InitialArgument<dst.List>, size: number = 0) {
        super(ds.List, value, size);
    }

    /**
     * Get the number of elements in the list.
     *
     * @returns The list length.
     */
    length(): number {
        return this.value.length();
    }

    /**
     * Get an element from the list by index.
     *
     * @param index - The zero-based index of the element.
     * @returns The term at the specified index.
     */
    getitem(index: number): Term {
        return new Term(this.value.getitem(index));
    }
}

/**
 * Wrapper class for logical terms in the deductive system.
 * A term can be a variable, item, or list.
 *
 * @example
 * ```typescript
 * const term = new Term("(f `x a)");
 * const innerTerm = term.term(); // Get the underlying term type
 * ```
 */
export class Term extends _Common<dst.Term> {
    /**
     * Creates a new term instance.
     *
     * @param value - Initial value (string, buffer, or another Term).
     * @param size - Optional buffer capacity for the internal storage.
     * @throws {Error} If initialization fails.
     */
    constructor(value: InitialArgument<dst.Term>, size: number = 0) {
        super(ds.Term, value, size);
    }

    /**
     * Extracts the underlying term and returns it as its concrete type (Variable, Item, or List).
     *
     * @returns The term as a Variable, Item, or List.
     * @throws {Error} If the term type is unexpected.
     */
    term(): Variable | Item | List {
        const term_type: dst.TermType = this.value.get_type();
        if (term_type === ds.TermType.Variable) {
            return new Variable(this.value.variable());
        } else if (term_type === ds.TermType.Item) {
            return new Item(this.value.item());
        } else if (term_type === ds.TermType.List) {
            return new List(this.value.list());
        } else {
            throw new Error("Unexpected term type.");
        }
    }

    /**
     * Ground this term using a dictionary to substitute variables with values.
     *
     * @param other - A term representing a dictionary (list of pairs). Each pair contains a variable and its substitution value.
     *                Example: "((`a b))" means substitute variable `a with value b.
     * @param scope - Optional scope string for variable scoping.
     * @returns The grounded term, or null if grounding fails.
     *
     * @example
     * ```typescript
     * const a = new Term("`a");
     * const b = new Term("((`a b))");
     * console.log(a.ground(b).toString()); // "b"
     *
     * // With scope
     * const c = new Term("`a");
     * const d = new Term("((x y `a `b) (y x `b `c))");
     * console.log(c.ground(d, "x").toString()); // "`c"
     * ```
     */
    ground(other: Term, scope: string = ""): Term | null {
        const capacity = buffer_size();
        const term = ds.Term.ground(this.value, other.value, scope, capacity);
        if (term === null) {
            return null;
        }
        return new Term(term, capacity);
    }

    /**
     * Match two terms and return the unification result as a dictionary.
     *
     * @param other - The term to match with this term.
     * @returns A term representing the unification dictionary (list of tuples), or null if matching fails.
     *
     * @example
     * ```typescript
     * const a = new Term("`a");
     * const b = new Term("b");
     * const result = a.match(b);
     * if (result !== null) {
     *     console.log(result.toString());  // "((1 2 `a b))"
     * }
     * ```
     */
    match(other: Term): Term | null {
        const capacity = buffer_size();
        const term = ds.Term.match(this.value, other.value, "1", "2", capacity);
        if (term === null) {
            return null;
        }
        return new Term(term, capacity);
    }

    /**
     * Rename all variables in this term by adding prefix and suffix.
     *
     * @param prefix_and_suffix - A term representing a list with two inner lists.
     *                            Each inner list contains 0 or 1 item representing the prefix and suffix.
     *                            Example: "((pre_) (_suf))" adds "pre_" as prefix and "_suf" as suffix.
     * @returns The renamed term, or null if renaming fails.
     *
     * @example
     * ```typescript
     * const a = new Term("`x");
     * const b = new Term("((pre_) (_suf))");
     * console.log(a.rename(b).toString()); // "`pre_x_suf"
     *
     * // With empty prefix (only suffix)
     * const c = new Term("`x");
     * const d = new Term("(() (_suf))");
     * console.log(c.rename(d).toString()); // "`x_suf"
     * ```
     */
    rename(prefix_and_suffix: Term): Term | null {
        const capacity = buffer_size();
        const term = ds.Term.rename(this.value, prefix_and_suffix.value, capacity);
        if (term === null) {
            return null;
        }
        return new Term(term, capacity);
    }
}

/**
 * Wrapper class for logical rules in the deductive system.
 * A rule consists of zero or more premises (above the line) and a conclusion (below the line).
 *
 * @example
 * ```typescript
 * const rule = new Rule("(father `X `Y)\n----------\n(parent `X `Y)\n");
 * console.log(rule.conclusion().toString()); // "(parent `X `Y)"
 * console.log(rule.length()); // 1 (number of premises)
 * ```
 */
export class Rule extends _Common<dst.Rule> {
    /**
     * Creates a new rule instance.
     *
     * @param value - Initial value (string, buffer, or another Rule).
     * @param size - Optional buffer capacity for the internal storage.
     * @throws {Error} If initialization fails.
     */
    constructor(value: InitialArgument<dst.Rule>, size: number = 0) {
        super(ds.Rule, value, size);
    }

    /**
     * Get the number of premises in the rule.
     *
     * @returns The number of premises.
     */
    length(): number {
        return this.value.length();
    }

    /**
     * Get a premise term by index.
     *
     * @param index - The zero-based index of the premise.
     * @returns The premise term at the specified index.
     */
    getitem(index: number): Term {
        return new Term(this.value.getitem(index));
    }

    /**
     * Get the conclusion of the rule.
     *
     * @returns The conclusion term.
     */
    conclusion(): Term {
        return new Term(this.value.conclusion());
    }

    /**
     * Ground this rule using a dictionary to substitute variables with values.
     *
     * @param other - A rule representing a dictionary (list of pairs). Each pair contains a variable and its substitution value.
     *                Example: new Rule("((`a b))") means substitute variable `a with value b.
     * @param scope - Optional scope string for variable scoping.
     * @returns The grounded rule, or null if grounding fails.
     *
     * @example
     * ```typescript
     * const a = new Rule("`a");
     * const b = new Rule("((`a b))");
     * console.log(a.ground(b).toString()); // "----\nb\n"
     *
     * // With scope
     * const c = new Rule("`a");
     * const d = new Rule("((x y `a `b) (y x `b `c))");
     * console.log(c.ground(d, "x").toString()); // "----\n`c\n"
     * ```
     */
    ground(other: Rule, scope: string = ""): Rule | null {
        const capacity = buffer_size();
        const rule = ds.Rule.ground(this.value, other.value, scope, capacity);
        if (rule === null) {
            return null;
        }
        return new Rule(rule, capacity);
    }

    /**
     * Match this rule with another rule using unification.
     * This unifies the first premise of this rule with the other rule.
     * The other rule must be a fact (a rule without premises).
     *
     * @param other - The rule to match against (must be a fact without premises).
     * @returns The matched rule, or null if matching fails.
     *
     * @example
     * ```typescript
     * const mp = new Rule("(`p -> `q)\n`p\n`q\n");
     * const pq = new Rule("((! (! `x)) -> `x)");
     * console.log(mp.match(pq).toString()); // "(! (! `x))\n----------\n`x\n"
     * ```
     */
    match(other: Rule): Rule | null {
        const capacity = buffer_size();
        const rule = ds.Rule.match(this.value, other.value, capacity);
        if (rule === null) {
            return null;
        }
        return new Rule(rule, capacity);
    }

    /**
     * Rename all variables in this rule by adding prefix and suffix.
     *
     * @param prefix_and_suffix - A rule with only a conclusion that is a list with two inner lists.
     *                            Each inner list contains 0 or 1 item representing the prefix and suffix.
     *                            Example: "((pre_) (_suf))" adds "pre_" as prefix and "_suf" as suffix.
     * @returns The renamed rule, or null if renaming fails.
     *
     * @example
     * ```typescript
     * const a = new Rule("`x");
     * const b = new Rule("((pre_) (_suf))");
     * console.log(a.rename(b).toString()); // "----\n`pre_x_suf\n"
     *
     * // With empty prefix (only suffix)
     * const c = new Rule("`x");
     * const d = new Rule("(() (_suf))");
     * console.log(c.rename(d).toString()); // "----\n`x_suf\n"
     * ```
     */
    rename(prefix_and_suffix: Rule): Rule | null {
        const capacity = buffer_size();
        const rule = ds.Rule.rename(this.value, prefix_and_suffix.value, capacity);
        if (rule === null) {
            return null;
        }
        return new Rule(rule, capacity);
    }
}

/**
 * Search engine for the deductive system.
 * Manages a knowledge base of rules and performs logical inference.
 *
 * @example
 * ```typescript
 * const search = new Search();
 * search.add("(parent john mary)");
 * search.add("(father `X `Y)\n----------\n(parent `X `Y)\n");
 * search.execute((rule) => {
 *   console.log(rule.toString());
 *   return false; // Return false to continue, true to stop
 * });
 * ```
 */
export class Search {
    _search: dst.Search;

    /**
     * Creates a new search engine instance.
     *
     * @param limit_size - Size of the buffer for storing the final objects (rules/facts) in the knowledge base (default: 1000).
     * @param buffer_size - Size of the buffer for internal operations like conversions and transformations (default: 10000).
     */
    constructor(limit_size: number = 1000, buffer_size: number = 10000) {
        this._search = new ds.Search(limit_size, buffer_size);
    }

    /**
     * Set the size of the buffer for storing final objects.
     *
     * @param limit_size - The new limit size for storing rules/facts.
     */
    set_limit_size(limit_size: number): void {
        this._search.set_limit_size(limit_size);
    }

    /**
     * Set the buffer size for internal operations.
     *
     * @param buffer_size - The new buffer size.
     */
    set_buffer_size(buffer_size: number): void {
        this._search.set_buffer_size(buffer_size);
    }

    /**
     * Reset the search engine, clearing all rules and facts.
     */
    reset(): void {
        this._search.reset();
    }

    /**
     * Add a rule or fact to the knowledge base.
     *
     * @param text - The rule or fact as a string.
     * @returns True if successfully added, false otherwise.
     */
    add(text: string): boolean {
        return this._search.add(text);
    }

    /**
     * Execute the search engine with a callback for each inferred rule.
     *
     * @param callback - Function called for each candidate rule. Return false to continue, true to stop.
     * @returns The number of rules processed.
     */
    execute(callback: (candidate: Rule) => boolean): number {
        return this._search.execute((candidate: dst.Rule): boolean => {
            return callback(new Rule(candidate).copy());
        });
    }
}
