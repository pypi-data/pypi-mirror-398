"""Utilities for rendering regression results within the Textual TUI."""

from __future__ import annotations

from pathlib import Path
from typing import override, Any
from dataclasses import fields
from dataclasses import asdict

from socx import Test
from socx import Visitor
from socx import TestBase
from socx import Regression
from textual.widgets import DataTable

from socx_tui.regression.bindings.vim.mode import VimMode


class Table(DataTable[TestBase], can_focus=True, inherit_bindings=True):
    """Interactive table widget that displays regression test results."""

    BINDINGS = DataTable.BINDINGS + VimMode.Normal.value

    def __init__(
        self,
        *args: Any,
        model: Regression | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._model = model or Regression("", [])
        self.cursor_type = "row"
        self.zebra_stripes = True

    @property
    def model(self) -> TestBase:
        """Return the regression model currently bound to the table."""
        return self._model

    @model.setter
    def model(self, model: TestBase) -> None:
        """Update the underlying regression model reference."""
        self._model = model

    def accept(self, visitor: Visitor[Table | Regression | TestBase]) -> None:
        """Allow a visitor to traverse the bound regression model."""
        if self.model is not None:
            visitor.visit(self.model)

    def load_from_file(self, file: str | Path) -> None:
        """Populate the table from a serialized regression results file."""
        if isinstance(file, str):
            file = Path(file).resolve()
        model = Regression.from_lines(file.stem, file.read_text().splitlines())
        self.model = model


class TableVisitor(Visitor[Table | TestBase]):
    """Visitor that renders regression data into a ``Table`` widget."""

    _table: Table

    def __init__(self, table: Table) -> None:
        self._table = table

    @override
    def visit(self, n: Table | TestBase) -> None:
        """Dispatch the visit based on the regression node type."""
        if isinstance(n, Regression):
            self.visit_regression(n)
        elif isinstance(n, Test):
            self.visit_test(n)
        elif isinstance(n, Table):
            self._table.set_loading(True)
            self._table = n
            self.visit(self._table.model)
            self._table.set_loading(False)

    def visit_regression(self, n: Regression) -> None:
        """Add regression-level information such as column headers."""
        if n.tests:
            columns = tuple(field.name for field in fields(n.tests[0]))
            self._table.add_columns(*columns)
        for test in n.tests:
            self.visit(test)

    def visit_test(self, n: Test) -> None:
        """Append a single test case row to the table."""
        columns = fields(n)
        mapping = asdict(n)
        values = [mapping[column.name] for column in columns]
        for i in range(len(values)):
            value = values[i]
            if isinstance(value, dict) and "line" in value:
                values[i] = value["line"]
        self._table.add_row(*values)
