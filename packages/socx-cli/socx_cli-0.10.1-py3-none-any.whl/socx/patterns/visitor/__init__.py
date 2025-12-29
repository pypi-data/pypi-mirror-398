"""Expose visitor pattern building blocks."""

__all__ = (
    "Node",
    "Visitor",
    "Structure",
    "Traversal",
    "ByLevelTraversal",
    "TopDownTraversal",
    "BottomUpTraversal",
)


from socx.patterns.visitor.protocol import Node as Node
from socx.patterns.visitor.protocol import Visitor as Visitor
from socx.patterns.visitor.protocol import Structure as Structure
from socx.patterns.visitor.protocol import Traversal as Traversal

from socx.patterns.visitor.traversal import (
    ByLevelTraversal as ByLevelTraversal,
)
from socx.patterns.visitor.traversal import (
    TopDownTraversal as TopDownTraversal,
)
from socx.patterns.visitor.traversal import (
    BottomUpTraversal as BottomUpTraversal,
)
