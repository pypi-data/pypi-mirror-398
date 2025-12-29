# AUTO GENERATED FILE - DO NOT EDIT

from dash.development.base_component import Component, _explicitize_args


class DashSpreadGrid(Component):
    """A DashSpreadGrid component.
_

Keyword arguments:

- id (string; optional):
    _.

- active_columns (list; optional):
    _.

- active_rows (list; optional):
    _.

- borderWidth (number; default 1):
    _.

- clicked_cell (dict; optional):
    _.

- clicked_custom_cell (dict; optional):
    _.

- column_widths (list; optional):
    _.

- columns (list; default [{ "type": "DATA-BLOCK" }]):
    _.

- columns_order (list; optional):
    _.

- data (boolean | number | string | dict | list; optional):
    _.

- data_selector (string; default "data[row.selector][column.selector]"):
    _.

- edited_cells (list; optional):
    _.

- filtering (list; optional):
    _.

- filters (list; optional):
    _.

- focusedCell (dict; optional):
    _.

- formatting (list; optional):
    _.

- highlightedCells (list; optional):
    _.

- hovered_cell (dict; optional):
    _.

- pinned_bottom (number; default 0):
    _.

- pinned_left (number; default 0):
    _.

- pinned_right (number; default 0):
    _.

- pinned_top (number; default 0):
    _.

- row_heights (list; optional):
    _.

- rows (list; default [{ "type": "HEADER" }, { "type": "DATA-BLOCK" }]):
    _.

- rows_order (list; optional):
    _.

- selected_cells (list; optional):
    _.

- sort_by (list; optional):
    _.

- sorting (list; optional):
    _."""
    _children_props = []
    _base_nodes = ['children']
    _namespace = 'dash_spread_grid'
    _type = 'DashSpreadGrid'
    @_explicitize_args
    def __init__(self, id=Component.UNDEFINED, data=Component.UNDEFINED, columns=Component.UNDEFINED, rows=Component.UNDEFINED, formatting=Component.UNDEFINED, filtering=Component.UNDEFINED, sorting=Component.UNDEFINED, data_selector=Component.UNDEFINED, pinned_top=Component.UNDEFINED, pinned_bottom=Component.UNDEFINED, pinned_left=Component.UNDEFINED, pinned_right=Component.UNDEFINED, borderWidth=Component.UNDEFINED, focusedCell=Component.UNDEFINED, selected_cells=Component.UNDEFINED, highlightedCells=Component.UNDEFINED, edited_cells=Component.UNDEFINED, filters=Component.UNDEFINED, sort_by=Component.UNDEFINED, column_widths=Component.UNDEFINED, row_heights=Component.UNDEFINED, columns_order=Component.UNDEFINED, rows_order=Component.UNDEFINED, clicked_cell=Component.UNDEFINED, clicked_custom_cell=Component.UNDEFINED, active_columns=Component.UNDEFINED, active_rows=Component.UNDEFINED, hovered_cell=Component.UNDEFINED, **kwargs):
        self._prop_names = ['id', 'active_columns', 'active_rows', 'borderWidth', 'clicked_cell', 'clicked_custom_cell', 'column_widths', 'columns', 'columns_order', 'data', 'data_selector', 'edited_cells', 'filtering', 'filters', 'focusedCell', 'formatting', 'highlightedCells', 'hovered_cell', 'pinned_bottom', 'pinned_left', 'pinned_right', 'pinned_top', 'row_heights', 'rows', 'rows_order', 'selected_cells', 'sort_by', 'sorting']
        self._valid_wildcard_attributes =            []
        self.available_properties = ['id', 'active_columns', 'active_rows', 'borderWidth', 'clicked_cell', 'clicked_custom_cell', 'column_widths', 'columns', 'columns_order', 'data', 'data_selector', 'edited_cells', 'filtering', 'filters', 'focusedCell', 'formatting', 'highlightedCells', 'hovered_cell', 'pinned_bottom', 'pinned_left', 'pinned_right', 'pinned_top', 'row_heights', 'rows', 'rows_order', 'selected_cells', 'sort_by', 'sorting']
        self.available_wildcard_properties =            []
        _explicit_args = kwargs.pop('_explicit_args')
        _locals = locals()
        _locals.update(kwargs)  # For wildcard attrs and excess named props
        args = {k: _locals[k] for k in _explicit_args}

        super(DashSpreadGrid, self).__init__(**args)
