"""Validation helpers for regression test collections."""

from collections.abc import Iterable

from socx.regression.test import Test


def _duplicates(tests: Iterable[Test]) -> Iterable[Test]:
    """Return tests that appear more than once in the iterable."""
    rv = list()
    seen = set()
    for x in tests:
        if x in seen:
            rv.append(x)
        else:
            seen.add(x)
    return rv


def _warn_duplicates(
    ntests: int, nunique: int, duplicates: Iterable[Test]
) -> None:
    """Raise a descriptive error highlighting duplicate regression tests."""
    error = f"""
Note that the total number of unique tests ({nunique}) is smaller than the
number supplied ({ntests}). The suspected duplicate values are {duplicates}.
"""
    raise ValueError(error)


def validate_test_list(tests: Iterable[Test]) -> None:
    """Ensure the provided test iterable does not contain duplicates."""
    dups = _duplicates(tests)
    unique = set(tests)
    ntests, nunique = len(tuple(tests)), len(tuple(unique))
    if ntests < nunique:
        _warn_duplicates(ntests, nunique, dups)
