"""Expose reusable design-pattern utilities leveraged throughout SoCX."""

__all__ = (
    "Node",
    "Visitor",
    "PtrMixin",
    "UIDMixin",
    "Structure",
    "Traversal",
    "Singleton",
    "ByLevelTraversal",
    "TopDownTraversal",
    "BottomUpTraversal",
)


from socx.patterns.mixins import PtrMixin as PtrMixin
from socx.patterns.mixins import UIDMixin as UIDMixin

from socx.patterns.visitor import Node as Node
from socx.patterns.visitor import Visitor as Visitor
from socx.patterns.visitor import Structure as Structure
from socx.patterns.visitor import Traversal as Traversal
from socx.patterns.visitor import ByLevelTraversal as ByLevelTraversal
from socx.patterns.visitor import TopDownTraversal as TopDownTraversal
from socx.patterns.visitor import BottomUpTraversal as BottomUpTraversal

from socx.patterns.singleton import Singleton as Singleton
