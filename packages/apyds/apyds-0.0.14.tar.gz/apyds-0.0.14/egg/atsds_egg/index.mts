/**
 * E-Graph implementation for atsds (TypeScript version)
 * E-Graph (Equality Graph) for representing equivalence classes of terms.
 */

import type { List, Term } from "atsds";

function isList(obj: unknown): obj is List {
    return (
        typeof obj === "object" &&
        obj !== null &&
        typeof (obj as Record<string, unknown>).length === "function" &&
        typeof (obj as Record<string, unknown>).getitem === "function"
    );
}

// Branded type for EClassId to ensure type safety, even though it's a number at runtime.
export type EClassId = number & { __brand: "EClassId" };

class DefaultMap<K, V> extends Map<K, V> {
    constructor(private readonly factory: () => V) {
        super();
    }

    get(key: K): V {
        if (!this.has(key)) {
            this.set(key, this.factory());
        }
        return super.get(key)!;
    }
}

class UnionFind<T> {
    /**
     * Union-find data structure for managing disjoint sets.
     */
    public parent: Map<T, T>;

    constructor() {
        this.parent = new Map<T, T>();
    }

    /**
     * Find the canonical representative of x's set with path compression.
     * @param x - The element to find.
     * @returns The canonical representative of x's set.
     */
    find(x: T): T {
        if (!this.parent.has(x)) {
            this.parent.set(x, x);
        }
        if (this.parent.get(x) !== x) {
            this.parent.set(x, this.find(this.parent.get(x)!));
        }
        return this.parent.get(x)!;
    }

    /**
     * Union two sets and return the canonical representative.
     * @param a - The first element.
     * @param b - The second element.
     * @returns The canonical representative of the merged set.
     */
    union(a: T, b: T): T {
        const ra = this.find(a);
        const rb = this.find(b);
        if (ra !== rb) {
            this.parent.set(rb, ra);
        }
        return ra;
    }
}

/**
 * ENode - Node in the E-Graph with an operator and children.
 */
class ENode {
    /**
     * @param op - The operator
     * @param children - The children E-class IDs
     */
    constructor(
        public op: string,
        public children: EClassId[],
    ) {}

    /**
     * Canonicalize children using the find function.
     * @param find - Function to find the canonical E-class ID.
     * @returns A new ENode with canonicalized children.
     */
    canonicalize(find: (id: EClassId) => EClassId): ENode {
        return new ENode(
            this.op,
            this.children.map((c) => find(c)),
        );
    }

    /**
     * Get a string key representation for this ENode for use in Maps/Objects.
     * @returns A unique string representation of this ENode.
     */
    key(): string {
        return `${this.op}(${this.children.join(",")})`;
    }
}

/**
 * EGraph - E-Graph for representing equivalence classes of terms.
 */
class EGraph {
    private next_id: number = 0;
    private hashcons: Map<string, [ENode, EClassId]> = new Map();
    private unionfind: UnionFind<EClassId> = new UnionFind();
    private classes: DefaultMap<EClassId, Set<ENode>> = new DefaultMap(() => new Set());
    private parents: DefaultMap<EClassId, Set<[ENode, EClassId]>> = new DefaultMap(() => new Set());
    private worklist: Set<EClassId> = new Set();

    /**
     * Generate a fresh E-class ID.
     * @returns A new E-class ID.
     */
    private freshId(): EClassId {
        const eid = this.next_id as EClassId;
        this.next_id += 1;
        return eid;
    }

    /**
     * Find the canonical representative of an E-class.
     * @param eclass - The E-class ID to find.
     * @returns The canonical E-class ID.
     */
    find(eclass: EClassId): EClassId {
        return this.unionfind.find(eclass);
    }

    /**
     * Add a term to the E-Graph and return its E-class ID.
     * @param term - An atsds Term to add to the E-Graph.
     * @returns The E-class ID for the added term.
     */
    add(term: Term): EClassId {
        const enode = this.termToEnode(term);
        return this.addEnode(enode);
    }

    /**
     * Convert an atsds Term to an ENode.
     * @param term - The Term to convert.
     * @returns The converted ENode.
     */
    private termToEnode(term: Term): ENode {
        const inner = term.term();

        if (isList(inner)) {
            const children: EClassId[] = [];
            for (let i = 0; i < inner.length(); i++) {
                const childTerm = inner.getitem(i);
                const childId = this.add(childTerm);
                children.push(childId);
            }
            return new ENode("()", children);
        } else {
            return new ENode(term.toString(), []);
        }
    }

    /**
     * Add an ENode to the E-Graph.
     * @param enode - The ENode to add.
     * @returns The E-class ID for the added ENode.
     */
    private addEnode(enode: ENode): EClassId {
        enode = enode.canonicalize(this.find.bind(this));

        const enodeKey = enode.key();
        const entry = this.hashcons.get(enodeKey);
        if (entry) {
            return this.find(entry[1]);
        }

        const eid = this.freshId();

        this.hashcons.set(enodeKey, [enode, eid]);
        this.unionfind.parent.set(eid, eid);
        this.classes.get(eid).add(enode);

        for (const c of enode.children) {
            this.parents.get(c).add([enode, eid]);
        }

        return eid;
    }

    /**
     * Merge two E-classes and defer congruence restoration.
     * @param a - The first E-class ID to merge.
     * @param b - The second E-class ID to merge.
     * @returns The canonical E-class ID of the merged class.
     */
    merge(a: EClassId, b: EClassId): EClassId {
        const ra = this.find(a);
        const rb = this.find(b);
        if (ra === rb) {
            return ra;
        }

        const r = this.unionfind.union(ra, rb);

        for (const node of this.classes.get(rb)) {
            this.classes.get(r).add(node);
        }
        this.classes.delete(rb);

        for (const item of this.parents.get(rb)) {
            this.parents.get(r).add(item);
        }
        this.parents.delete(rb);

        this.worklist.add(r);

        return r;
    }

    /**
     * Restore congruence by processing the worklist.
     */
    rebuild(): void {
        while (this.worklist.size > 0) {
            const todo = new Set(Array.from(this.worklist).map((e) => this.find(e)));
            this.worklist.clear();

            for (const eclass of todo) {
                this.repair(eclass);
            }
        }
    }

    /**
     * Restore congruence for a single E-class.
     */
    private repair(eclass: EClassId): void {
        const newParents = new Map<string, [ENode, EClassId]>();

        for (const [pnode, peclass] of this.parents.get(eclass)) {
            this.hashcons.delete(pnode.key());

            const canon = pnode.canonicalize(this.find.bind(this));
            const canonKey = canon.key();
            const canonicalPeclass = this.find(peclass);

            if (newParents.has(canonKey)) {
                this.merge(canonicalPeclass, newParents.get(canonKey)![1]);
            } else {
                newParents.set(canonKey, [canon, canonicalPeclass]);
                this.hashcons.set(canonKey, [canon, canonicalPeclass]);
            }
        }

        this.parents.get(eclass).clear();
        for (const [_, entry] of newParents) {
            this.parents.get(eclass).add(entry);
        }
    }
}

export { DefaultMap, UnionFind, ENode, EGraph };
