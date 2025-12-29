import { List, Rule, Term } from "atsds";
import { EGraph, type EClassId } from "atsds-egg";

function buildTermToRule(data: Term): Rule {
    return new Rule(`----\n${data.toString()}\n`);
}

function extractLhsRhsFromRule(data: Rule): [Term, Term] | null {
    if (data.length() !== 0) {
        return null;
    }
    const term = data.conclusion();
    const inner = term.term();
    if (!(inner instanceof List)) {
        return null;
    }
    if (!(inner.length() === 4 && inner.getitem(0).toString() === "binary" && inner.getitem(1).toString() === "==")) {
        return null;
    }
    return [inner.getitem(2), inner.getitem(3)];
}

function buildLhsRhsToTerm(lhs: Term, rhs: Term): Term {
    return new Term(`(binary == ${lhs.toString()} ${rhs.toString()})`);
}

class InternalEGraph {
    private core: EGraph;
    private mapping: Map<string, EClassId>;

    constructor() {
        this.core = new EGraph();
        this.mapping = new Map();
    }

    private getOrAdd(data: Term): EClassId {
        const key = data.toString();
        if (!this.mapping.has(key)) {
            this.mapping.set(key, this.core.add(data));
        }
        return this.mapping.get(key)!;
    }

    find(data: Term): EClassId {
        return this.core.find(this.getOrAdd(data));
    }

    setEquality(lhs: Term, rhs: Term): void {
        const lhsId = this.getOrAdd(lhs);
        const rhsId = this.getOrAdd(rhs);
        this.core.merge(lhsId, rhsId);
    }

    getEquality(lhs: Term, rhs: Term): boolean {
        const lhsId = this.getOrAdd(lhs);
        const rhsId = this.getOrAdd(rhs);
        return this.core.find(lhsId) === this.core.find(rhsId);
    }

    rebuild(): void {
        this.core.rebuild();
    }
}

export class Search {
    private egraph: InternalEGraph;
    private terms: Set<string>;
    private facts: Set<string>;
    private newlyAddedTerms: Set<string>;
    private newlyAddedFacts: Set<string>;
    private factMatchingCache: Map<string, Set<string>>;

    constructor() {
        this.egraph = new InternalEGraph();
        this.terms = new Set();
        this.facts = new Set();
        this.newlyAddedTerms = new Set();
        this.newlyAddedFacts = new Set();
        this.factMatchingCache = new Map();
    }

    rebuild(): void {
        this.egraph.rebuild();

        const newlyAddedTermsList = Array.from(this.newlyAddedTerms).map((s) => new Term(s));
        for (const factStr of this.facts) {
            const fact = new Term(factStr);
            if (!this.factMatchingCache.has(factStr)) {
                this.factMatchingCache.set(factStr, new Set());
            }
            const candidates = this.collectMatchingCandidates(fact, newlyAddedTermsList);
            for (const c of candidates) {
                this.factMatchingCache.get(factStr)!.add(c.toString());
            }
        }

        const termsList = Array.from(this.terms).map((s) => new Term(s));
        for (const factStr of this.newlyAddedFacts) {
            const fact = new Term(factStr);
            if (!this.factMatchingCache.has(factStr)) {
                this.factMatchingCache.set(factStr, new Set());
            }
            const candidates = this.collectMatchingCandidates(fact, termsList);
            for (const c of candidates) {
                this.factMatchingCache.get(factStr)!.add(c.toString());
            }
        }

        this.newlyAddedTerms.clear();
        this.newlyAddedFacts.clear();
    }

    add(data: Rule): void {
        this.addExpr(data);
        this.addFact(data);
    }

    private addExpr(data: Rule): void {
        const lhsRhs = extractLhsRhsFromRule(data);
        if (!lhsRhs) return;
        const [lhs, rhs] = lhsRhs;
        this.terms.add(lhs.toString());
        this.newlyAddedTerms.add(lhs.toString());
        this.terms.add(rhs.toString());
        this.newlyAddedTerms.add(rhs.toString());
        this.egraph.setEquality(lhs, rhs);
    }

    private addFact(data: Rule): void {
        if (data.length() !== 0) return;
        const term = data.conclusion();
        this.terms.add(term.toString());
        this.newlyAddedTerms.add(term.toString());
        this.facts.add(term.toString());
        this.newlyAddedFacts.add(term.toString());
    }

    *execute(data: Rule): Generator<Rule> {
        yield* this.executeExpr(data);
        yield* this.executeFact(data);
    }

    private *executeExpr(data: Rule): Generator<Rule> {
        const lhsRhs = extractLhsRhsFromRule(data);
        if (!lhsRhs) return;
        const [lhs, rhs] = lhsRhs;

        if (this.egraph.getEquality(lhs, rhs)) {
            yield data;
        }

        const termsList = Array.from(this.terms).map((s) => new Term(s));
        const lhsPool = this.collectMatchingCandidates(lhs, termsList);
        const rhsPool = this.collectMatchingCandidates(rhs, termsList);

        if (lhsPool.length === 0 || rhsPool.length === 0) return;

        const lhsGroups = this.groupByEquivalenceClass(lhsPool);
        const rhsGroups = this.groupByEquivalenceClass(rhsPool);

        for (const lhsGroup of lhsGroups) {
            for (const rhsGroup of rhsGroups) {
                if (lhsGroup.size > 0 && rhsGroup.size > 0) {
                    const firstLhs = new Term(lhsGroup.values().next().value!);
                    const firstRhs = new Term(rhsGroup.values().next().value!);
                    if (this.egraph.getEquality(firstLhs, firstRhs)) {
                        for (const xStr of lhsGroup) {
                            for (const yStr of rhsGroup) {
                                const x = new Term(xStr);
                                const y = new Term(yStr);
                                const target = buildLhsRhsToTerm(x, y);
                                const query = data.conclusion();
                                const unification = target.match(query);
                                if (unification) {
                                    const result = target.ground(unification, "1");
                                    if (result) {
                                        yield buildTermToRule(result);
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    private *executeFact(data: Rule): Generator<Rule> {
        if (data.length() !== 0) return;
        const idea = data.conclusion();

        for (const factStr of this.facts) {
            if (this.egraph.getEquality(idea, new Term(factStr))) {
                yield data;
            }
        }

        const termsList = Array.from(this.terms).map((s) => new Term(s));
        const ideaPool = this.collectMatchingCandidates(idea, termsList);
        if (ideaPool.length === 0) return;

        const ideaGroups = this.groupByEquivalenceClass(ideaPool);

        for (const factStr of this.facts) {
            const factPoolStr = this.factMatchingCache.get(factStr);
            if (!factPoolStr || factPoolStr.size === 0) continue;

            const factPool = Array.from(factPoolStr).map((s) => new Term(s));
            const factGroups = this.groupByEquivalenceClass(factPool);

            for (const ideaGroup of ideaGroups) {
                for (const factGroup of factGroups) {
                    if (ideaGroup.size > 0 && factGroup.size > 0) {
                        const firstIdea = new Term(ideaGroup.values().next().value!);
                        const firstFact = new Term(factGroup.values().next().value!);
                        if (this.egraph.getEquality(firstIdea, firstFact)) {
                            for (const xStr of ideaGroup) {
                                for (const yStr of factGroup) {
                                    const x = new Term(xStr);
                                    const y = new Term(yStr);
                                    const target = buildLhsRhsToTerm(x, y);
                                    const query = buildLhsRhsToTerm(idea, new Term(factStr));
                                    const unification = target.match(query);
                                    if (unification) {
                                        const result = target.ground(unification, "1");
                                        if (result) {
                                            const inner = result.term();
                                            if (inner instanceof List) {
                                                yield buildTermToRule(inner.getitem(2));
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    private collectMatchingCandidates(pattern: Term, candidates: Term[]): Term[] {
        return candidates.filter((c) => pattern.match(c) !== null);
    }

    private groupByEquivalenceClass(terms: Term[]): Set<string>[] {
        if (terms.length === 0) return [];
        const eidToTerms = new Map<string, Set<string>>();
        for (const term of terms) {
            const eid = this.egraph.find(term).toString();
            if (!eidToTerms.has(eid)) {
                eidToTerms.set(eid, new Set());
            }
            eidToTerms.get(eid)!.add(term.toString());
        }
        return Array.from(eidToTerms.values());
    }
}
