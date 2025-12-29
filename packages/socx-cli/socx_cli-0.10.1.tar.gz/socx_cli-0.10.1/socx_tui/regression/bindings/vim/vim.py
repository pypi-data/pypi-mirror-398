"""Archived Vim binding prototype kept for future development."""

# from __future__ import annotations
#
# from typing import Any
# from typing import ClassVar
# from contextlib import suppress
#
# from textual.binding import BindingType
# from textual.coordinate import Coordinate
# from textual.widget import Widget
#
# from socx_tui.regression.bindings.vim.mode import Mode
#
#
# class Mixin(Widget):
#     BINDINGS: ClassVar[list[BindingType]] = []
#
#     def __init__(self, *args, **kwargs) -> None:
#         super().__init__(*args, **kwargs)
#
#
# class Vim(Mixin):
#     """Vim modes keybindings mixin class."""
#
#     BINDINGS: ClassVar[list[BindingType]] = Mode.Normal.value,
#
#     def __init__(self, *args: Any, **kwargs: Any) -> None:
#         super().__init__(*args, **kwargs)
#         self._mode: Mode = Mode.Normal
#         self._bindings: list[BindingType] = Mode.Normal.value
#
#     @property
#     def mode(self) -> Mode:
#         return self._mode
#
#     @mode.setter
#     def mode(self, mode: Mode) -> None:
#         self._mode = mode
#
#     @property
#     def bindings(self) -> list[BindingType]:
#         return self._bindings
#
#     @bindings.setter
#     def bindings(self, bindings: list[BindingType]) -> None:
#         self._bindings = bindings
#
#     # @property
#     # def rows(self): ...
#     #
#     # @rows.setter
#     # def rows(self, value): ...
#     #
#     # @property
#     # def row_count(self): ...
#     #
#     # @row_count.setter
#     # def row_count(self, value): ...
#     #
#     # @property
#     # def columns(self): ...
#     #
#     # @columns.setter
#     # def columns(self, value): ...
#     #
#     # @property
#     # def cursor_type(self): ...
#     #
#     # @cursor_type.setter
#     # def cursor_type(self, value): ...
#     #
#     # @property
#     # def cursor_coordinate(self): ...
#     #
#     # @cursor_coordinate.setter
#     # def cursor_coordinate(self, value): ...
#     #
#     # @property
#     # def show_cursor(self): ...
#     #
#     # @show_cursor.setter
#     # def show_cursor(self, value): ...
#     #
#     # @property
#     # def max_scroll_x(self): ...
#     #
#     # @max_scroll_x.setter
#     # def max_scroll_x(self, value): ...
#     #
#     # @property
#     # def max_scroll_y(self): ...
#     #
#     # @max_scroll_y.setter
#     # def max_scroll_y(self, value): ...
#     #
#     # def move_cursor(self, *args, **kwargs) -> None: ...
#     #
#     # def scroll_up(self, *args: Any, **kwargs: Any) -> None: ...
#     #
#     # def scroll_down(self, *args: Any, **kwargs: Any) -> None: ...
#     #
#     # def scroll_left(self, *args: Any, **kwargs: Any) -> None: ...
#     #
#     # def scroll_right(self, *args: Any, **kwargs: Any) -> None: ...
#     #
#     # def scroll_home(self, *args: Any, **kwargs: Any) -> None: ...
#     #
#     # def scroll_end(self, *args: Any, **kwargs: Any) -> None: ...
#     #
#     def scroll_x_home(self, *args: Any, **kwargs: Any) -> None:
#         try:
#             self.move_cursor(column=0)
#         except Exception:
#             with suppress(Exception):
#                 self.scroll_x = 0
#             with suppress(Exception):
#                 self.scroll_home(y_axis=False)
#
#     def scroll_x_end(self, *args: Any, **kwargs: Any) -> None:
#         try:
#             self.move_cursor(column=len(self.columns) - 1)
#         except Exception:
#             with suppress(Exception):
#                 self.scroll_x = self.max_scroll_x
#             with suppress(Exception):
#                 self.scroll_end(y_axis=False)
#
#     def scroll_y_home(self, *args: Any, **kwargs: Any) -> None:
#         try:
#             self._set_hover_cursor(False)
#             cursor_type = self.cursor_type
#             if self.show_cursor and (
#                 cursor_type == "cell" or cursor_type == "row"
#             ):
#                 _, column_index = self.cursor_coordinate
#                 self.cursor_coordinate = Coordinate(0, column_index)
#         except Exception:
#             with suppress(Exception):
#                 self.scroll_y = 0
#             with suppress(Exception):
#                 self.scroll_home(x_axis=False)
#
#     def scroll_y_end(self, *args: Any, **kwargs: Any) -> None:
#         try:
#             self._set_hover_cursor(False)
#             cursor_type = self.cursor_type
#             if self.show_cursor and (
#                 cursor_type == "cell" or cursor_type == "row"
#             ):
#                 _, column_index = self.cursor_coordinate
#                 self.cursor_coordinate = Coordinate(
#                     self.row_count - 1, column_index
#                 )
#         except Exception:
#             with suppress(Exception):
#                 self.scroll_y = self.max_scroll_x
#             with suppress(Exception):
#                 self.scroll_end(x_axis=False)
#
#     def action_scroll_y_home(self, *args: Any, **kwargs: Any) -> None:
#         self.scroll_y_home()
#
#     def action_scroll_y_end(self, *args: Any, **kwargs: Any) -> None:
#         self.scroll_y_end()
#
#     def action_scroll_x_home(self, *args: Any, **kwargs: Any) -> None:
#         self.scroll_x_home()
#
#     def action_scroll_x_end(self, *args: Any, **kwargs: Any) -> None:
#         self.scroll_x_end()
#
#     def _set_hover_cursor(self, *args: Any, **kwargs: Any) -> None:
#         pass
