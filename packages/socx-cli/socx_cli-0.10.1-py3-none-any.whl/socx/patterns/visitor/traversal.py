"""Traversal strategies compatible with the visitor protocol."""

from __future__ import annotations

from socx.patterns.visitor.protocol import Visitor
from socx.patterns.visitor.protocol import Structure
from socx.patterns.visitor.protocol import Traversal


class TopDownTraversal[NODE](Traversal[NODE]):
    """Pre-order traversal that visits parents before descendants."""

    @classmethod
    def accept(cls, n: NODE, v: Visitor[NODE], p: Structure[NODE]) -> None:
        """Visit ``n`` before recursively traversing its children."""
        v.visit(n)

        for c in p.children(n):
            cls.accept(c, v, p)


class BottomUpTraversal[NODE](Traversal[NODE]):
    """Post-order traversal that visits descendants before parents."""

    @classmethod
    def accept(cls, n: NODE, v: Visitor[NODE], p: Structure[NODE]) -> None:
        """Traverse child subtrees prior to visiting ``n``."""
        for c in p.children(n):
            cls.accept(c, v, p)

        v.visit(n)


class ByLevelTraversal[NODE](Traversal[NODE]):
    """Breadth-first traversal that visits nodes one level at a time."""

    @classmethod
    def accept(cls, n: NODE, v: Visitor[NODE], p: Structure[NODE]) -> None:
        """Walk the structure level-by-level starting from ``n``."""
        q: list[NODE] = [n]

        while q:
            t: list[NODE] = []

            for n_ in q:
                v.visit(n_)
                t.extend(p.children(n_))

            q = t
