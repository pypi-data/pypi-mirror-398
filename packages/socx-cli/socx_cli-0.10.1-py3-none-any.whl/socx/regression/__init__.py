"""Expose regression primitives for use throughout SoCX."""

__all__ = (
    "Test",
    "TestBase",
    "TestStatus",
    "TestResult",
    "TestCommand",
    "Regression",
)

from socx.regression.test import Test as Test
from socx.regression.test import TestBase as TestBase
from socx.regression.test import TestStatus as TestStatus
from socx.regression.test import TestResult as TestResult
from socx.regression.test import TestCommand as TestCommand
from socx.regression.regression import Regression as Regression
