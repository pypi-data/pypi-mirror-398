from __future__ import annotations

__all__ = ["EClassId", "UnionFind", "ENode", "EGraph"]

from dataclasses import dataclass
from typing import NewType, Callable
from collections import defaultdict
import apyds

EClassId = NewType("EClassId", int)


class UnionFind:
    """Union-find data structure for managing disjoint sets."""

    def __init__(self) -> None:
        self.parent: dict[EClassId, EClassId] = {}

    def find(self, x: EClassId) -> EClassId:
        """Find the canonical representative of x's set with path compression."""
        if x not in self.parent:
            self.parent[x] = x
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, a: EClassId, b: EClassId) -> EClassId:
        """Union two sets and return the canonical representative."""
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra
        return ra


@dataclass(frozen=True)
class ENode:
    """Node in the E-Graph with an operator and children."""

    op: str
    children: tuple[EClassId, ...]

    def canonicalize(self, find: Callable[[EClassId], EClassId]) -> ENode:
        """Canonicalize children using the find function."""
        return ENode(self.op, tuple(find(c) for c in self.children))


class EGraph:
    """E-Graph for representing equivalence classes of terms."""

    def __init__(self) -> None:
        self.uf = UnionFind()
        self.next_id = 0
        self.classes: dict[EClassId, set[ENode]] = {}
        self.parents: dict[EClassId, set[tuple[ENode, EClassId]]] = defaultdict(set)
        self.hashcons: dict[ENode, EClassId] = {}
        self.worklist: set[EClassId] = set()

    def _fresh_id(self) -> EClassId:
        """Generate a fresh E-class ID."""
        eid = EClassId(self.next_id)
        self.next_id += 1
        return eid

    def find(self, eclass: EClassId) -> EClassId:
        """Find the canonical representative of an E-class."""
        return self.uf.find(eclass)

    def add(self, term: apyds.Term) -> EClassId:
        """Add a term to the E-Graph and return its E-class ID.

        Args:
            term: An apyds.Term to add to the E-Graph.

        Returns:
            The E-class ID for the added term.
        """
        enode = self._term_to_enode(term)
        return self._add_enode(enode)

    def _term_to_enode(self, term: apyds.Term) -> ENode:
        """Convert an apyds.Term to an ENode."""
        inner = term.term

        if isinstance(inner, apyds.List):
            children = []
            for i in range(len(inner)):
                child_term = inner[i]
                child_id = self.add(child_term)
                children.append(child_id)
            return ENode("()", tuple(children))
        else:
            return ENode(str(inner), ())

    def _add_enode(self, enode: ENode) -> EClassId:
        """Add an ENode to the E-Graph."""
        enode = enode.canonicalize(self.find)

        if enode in self.hashcons:
            return self.find(self.hashcons[enode])

        eid = self._fresh_id()

        self.uf.parent[eid] = eid
        self.classes[eid] = {enode}
        self.hashcons[enode] = eid

        for c in enode.children:
            self.parents[c].add((enode, eid))

        return eid

    def merge(self, a: EClassId, b: EClassId) -> EClassId:
        """Merge two E-classes and schedule rebuilding."""
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return ra

        r = self.uf.union(ra, rb)

        self.classes[r] |= self.classes[rb]
        del self.classes[rb]

        self.parents[r] |= self.parents[rb]
        del self.parents[rb]

        self.worklist.add(r)

        return r

    def rebuild(self) -> None:
        """Restore congruence by processing the worklist."""
        while self.worklist:
            todo: set[EClassId] = {self.find(e) for e in self.worklist}
            self.worklist.clear()

            for eclass in todo:
                self.repair(eclass)

    def repair(self, eclass: EClassId) -> None:
        """Repair congruence for an E-class by updating parent nodes."""
        new_parents: dict[ENode, EClassId] = {}

        for pnode, peclass in list(self.parents[eclass]):
            self.hashcons.pop(pnode, None)

            canon = pnode.canonicalize(self.find)
            peclass = self.find(peclass)

            if canon in new_parents:
                self.merge(peclass, new_parents[canon])
            else:
                new_parents[canon] = peclass
                self.hashcons[canon] = peclass

        self.parents[eclass] = {(p, c) for p, c in new_parents.items()}
