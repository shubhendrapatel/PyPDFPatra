"""
pypdfpatra.engine.layout.table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Implementation of the W3C Table Formatting Context.
"""

from __future__ import annotations

from pypdfpatra.defaults import PAGE_HEIGHT
from pypdfpatra.engine.font_metrics import measure_text, parse_font
from pypdfpatra.engine.tree import Box, TableBox, TableCellBox

from .common import PosCB


def layout_table_context(
    box: TableBox,
    cb_x: float,
    cb_y: float,
    cb_w: float,
    root_font_size: float = 12.0,
    current_page_name: str = "default",
    page_rules: list | None = None,
    pos_cb: PosCB | None = None,
) -> None:
    """
    Executes the Table Formatting Context (TFC) algorithm with support for
    colspan and rowspan.
    """
    from .block import _parse_length, _resolve_box_geometry, layout_block_context
    from .inline import shift_box

    style = getattr(box.node, "style", {}) if box.node else {}
    _, css_width, _, _ = _resolve_box_geometry(
        box, cb_w, style, root_font_size=root_font_size
    )

    box.x = cb_x
    box.y = cb_y

    spacing_val = str(style.get("border-spacing", "0px"))
    parts = spacing_val.split()
    h_spacing = (
        _parse_length(parts[0], cb_w, root_font_size=root_font_size) if parts else 0.0
    )
    v_spacing = h_spacing
    if len(parts) > 1:
        v_spacing = _parse_length(parts[1], cb_w, root_font_size=root_font_size)

    # 1. Collect all rows and cells
    rows = []
    thead_rows = []

    def _scan_for_rows(parent_box: Box):
        for child in parent_box.children:
            name = child.__class__.__name__
            if name == "TableRowBox":
                if (
                    parent_box.__class__.__name__ == "TableRowGroupBox"
                    and getattr(parent_box.node, "tag", "") == "thead"
                ):
                    thead_rows.append(child)
                rows.append(child)
            elif name == "TableRowGroupBox":
                _scan_for_rows(child)

    _scan_for_rows(box)
    box.thead_rows = thead_rows

    if not rows:
        box.w = css_width if css_width is not None else cb_w
        box.h = 0.0
        return

    # 2. Map cells to grid
    grid = {}  # (row_idx, col_idx) -> CellBox
    cell_metadata = {}  # id(cell) -> meta_dict
    num_cols = 0

    for r_idx, row in enumerate(rows):
        current_col = 0
        cells = [c for c in row.children if c.__class__.__name__ == "TableCellBox"]
        for cell in cells:
            # Skip columns already occupied by rowspans from previous rows
            while (r_idx, current_col) in grid:
                current_col += 1

            p = getattr(cell.node, "props", {})
            r_attr = p.get("rowspan", "1")
            c_attr = p.get("colspan", "1")

            try:
                rowspan = max(1, int(r_attr))
            except (ValueError, TypeError):
                rowspan = 1
            try:
                colspan = max(1, int(c_attr))
            except (ValueError, TypeError):
                colspan = 1

            cell_metadata[id(cell)] = {
                "rowspan": rowspan,
                "colspan": colspan,
                "start_row": r_idx,
                "start_col": current_col,
                "cell": cell,
            }

            for dr in range(rowspan):
                for dc in range(colspan):
                    grid[(r_idx + dr, current_col + dc)] = cell

            current_col += colspan
        num_cols = max(num_cols, current_col)

    if num_cols == 0:
        box.w = css_width if css_width is not None else cb_w
        box.h = 0.0
        return

    # 3. Calculate column widths (Shrink-to-fit)
    col_widths = [0.0] * num_cols

    def _get_text_nodes(n: Box) -> list:
        res = []
        if n.__class__.__name__ == "TextBox":
            res.append(n)
        for c in n.children:
            if isinstance(c, Box):
                res.extend(_get_text_nodes(c))
        return res

    def _compute_cell_intrinsic_width(cell: TableCellBox):
        n = getattr(cell, "node", None)
        s = getattr(n, "style", {}) if n else {}
        _, c_w, _, _ = _resolve_box_geometry(
            cell, cb_w, s, root_font_size=root_font_size
        )

        cell_max_w = 20.0
        for tbox in _get_text_nodes(cell):
            ts = getattr(tbox.node, "style", {}) if getattr(tbox, "node", None) else {}
            family, fp_style, size = parse_font(ts)
            w = measure_text(tbox.text_content.strip(), family, size, fp_style)
            if w > cell_max_w:
                cell_max_w = w

        padded_w = (
            cell_max_w
            + cell.padding_left
            + cell.padding_right
            + cell.border_left
            + cell.border_right
            + 15.0
        )
        if c_w is not None:
            padded_w = max(padded_w, c_w)
        return padded_w

    # First pass: colspan = 1
    for meta in cell_metadata.values():
        if meta["colspan"] == 1:
            w = _compute_cell_intrinsic_width(meta["cell"])
            col_widths[meta["start_col"]] = max(col_widths[meta["start_col"]], w)

    # Second pass: colspan > 1
    for meta in cell_metadata.values():
        if meta["colspan"] > 1:
            w = _compute_cell_intrinsic_width(meta["cell"])
            sc = meta["start_col"]
            ec = sc + meta["colspan"]
            current_sum = sum(col_widths[sc:ec]) + (meta["colspan"] - 1) * h_spacing
            if w > current_sum:
                extra = (w - current_sum) / meta["colspan"]
                for i in range(sc, ec):
                    col_widths[i] += extra

    total_table_w = sum(col_widths) + (num_cols + 1) * h_spacing

    if css_width is not None:
        if total_table_w < css_width:
            extra = (css_width - total_table_w) / num_cols
            col_widths = [cw + extra for cw in col_widths]
            total_table_w = css_width
    elif total_table_w < cb_w and cb_w > 0:
        extra = (cb_w - total_table_w) / num_cols
        col_widths = [cw + extra for cw in col_widths]
        total_table_w = cb_w
    elif total_table_w > cb_w and cb_w > 0:
        available_column_w = cb_w - (num_cols + 1) * h_spacing
        current_column_sum = sum(col_widths)
        if current_column_sum > 0:
            scale = available_column_w / current_column_sum
            col_widths = [cw * scale for cw in col_widths]
        total_table_w = cb_w

    box.w = total_table_w
    box.x = cb_x + box.margin_left + box.border_left + box.padding_left
    box.y = cb_y + box.margin_top + box.border_top + box.padding_top

    content_x = box.x
    current_y = box.y

    for child in box.children:
        if getattr(child.node, "tag", "") == "caption":
            layout_block_context(
                child,
                content_x,
                current_y,
                box.w,
                root_font_size=root_font_size,
                current_page_name=current_page_name,
                page_rules=page_rules,
                pos_cb=pos_cb,
            )
            current_y += (
                child.margin_top
                + child.border_top
                + child.padding_top
                + child.h
                + child.padding_bottom
                + child.border_bottom
                + child.margin_bottom
            )

    current_y += v_spacing

    # 4. Preliminary layout to determine row heights
    row_heights = [0.0] * len(rows)
    for r_idx, row in enumerate(rows):
        r_style = getattr(row.node, "style", {}) if row.node else {}
        _resolve_box_geometry(row, box.w, r_style)
        row_max_h = 0.0
        cells = [c for c in row.children if c.__class__.__name__ == "TableCellBox"]
        for cell in cells:
            m = cell_metadata[id(cell)]
            sc = m["start_col"]
            csp = m["colspan"]
            cell_w = sum(col_widths[sc : sc + csp]) + (csp - 1) * h_spacing

            # Reset cell to safe virtual position
            layout_block_context(
                cell,
                0,
                0,
                cell_w,
                root_font_size=root_font_size,
                current_page_name=current_page_name,
                page_rules=page_rules,
                pos_cb=PosCB(0, 0, cell_w, 0),
            )

            total_h = (
                cell.h
                + cell.padding_top
                + cell.padding_bottom
                + cell.border_top
                + cell.border_bottom
            )
            if m["rowspan"] == 1:
                row_max_h = max(row_max_h, total_h)
        row_heights[r_idx] = row_max_h

    # Adjust row heights for rowspan > 1
    for meta in cell_metadata.values():
        if meta["rowspan"] > 1:
            sr, er = meta["start_row"], meta["start_row"] + meta["rowspan"]
            cell = meta["cell"]
            total_h = (
                cell.h
                + cell.padding_top
                + cell.padding_bottom
                + cell.border_top
                + cell.border_bottom
            )
            current_h_span = sum(row_heights[sr:er]) + (meta["rowspan"] - 1) * v_spacing
            if total_h > current_h_span:
                # Distribute extra height to the last row of the span
                row_heights[er - 1] += total_h - current_h_span

    # 5. Final positioning
    thead_h = 0.0
    thead_resolved = False
    current_row_y = current_y

    # Pre-calculated horizontal offsets for columns
    col_x_offsets = [0.0] * num_cols
    curr_x = h_spacing
    for i in range(num_cols):
        col_x_offsets[i] = curr_x
        curr_x += col_widths[i] + h_spacing

    for r_idx, row in enumerate(rows):
        row.x = content_x
        row.y = 0.0
        row.w = box.w
        row.h = row_heights[r_idx]

        cells = [c for c in row.children if c.__class__.__name__ == "TableCellBox"]
        for cell in cells:
            m = cell_metadata[id(cell)]
            sc, csp, rsp = m["start_col"], m["colspan"], m["rowspan"]

            c_x = content_x + col_x_offsets[sc]
            c_w = sum(col_widths[sc : sc + csp]) + (csp - 1) * h_spacing
            c_h = sum(row_heights[r_idx : r_idx + rsp]) + (rsp - 1) * v_spacing

            # Re-layout with definitive width
            layout_block_context(
                cell,
                c_x,
                0.0,
                c_w,
                root_font_size=root_font_size,
                current_page_name=current_page_name,
                page_rules=page_rules,
                pos_cb=PosCB(c_x, 0, c_w, 0),
            )

            # Fix cell height to match spanned rows
            cell.h = (
                c_h
                - cell.padding_top
                - cell.padding_bottom
                - cell.border_top
                - cell.border_bottom
            )

        if row.__class__.__name__ == "TableRowBox" and any(
            row is thr for thr in (thead_rows or [])
        ):
            thead_h += row.h + v_spacing
        else:
            thead_resolved = True

        if thead_resolved and thead_rows:
            from ..page import get_resolved_margins

            page = int(current_row_y / PAGE_HEIGHT)
            mt, mb, _, _ = get_resolved_margins(page_rules, page, current_page_name)
            boundary = (page + 1) * PAGE_HEIGHT - mb
            if current_row_y + row.h + v_spacing > boundary:
                next_page = page + 1
                nmt, _, _, _ = get_resolved_margins(
                    page_rules, next_page, current_page_name
                )
                current_row_y = (next_page * PAGE_HEIGHT) + nmt + thead_h

        shift_box(row, 0, current_row_y)
        current_row_y += row.h + v_spacing

    box.h = current_row_y - box.y - box.margin_top - box.border_top - box.padding_top
