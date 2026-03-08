"""
pypdfpatra.engine.layout_table
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Implementation of the W3C Table Formatting Context.

Handles grid calculation, fluid column widths ("table-layout: auto"), and row height synchronization.
"""

from __future__ import annotations
from pypdfpatra.engine.tree import Box, TableBox, TableRowGroupBox, TableRowBox, TableCellBox
from pypdfpatra.engine.layout_block import layout_block_context
from pypdfpatra.engine.layout_block import _resolve_box_geometry

def layout_table_context(box: TableBox, cb_x: float, cb_y: float, cb_w: float) -> None:
    """
    Executes the Table Formatting Context (TFC) algorithm.
    1. Grid construction (rows and columns).
    2. Column width distribution (table-layout: auto).
    3. Cell block layout generation.
    4. Row height synchronization.
    """
    style = getattr(box.node, "style", {}) if box.node else {}
    box_sizing, css_width = _resolve_box_geometry(box, cb_w, style)

    # Assume exactly cb_w for the table width in MVP fluid auto layout
    table_w = css_width if css_width > 0 else cb_w
    box.x = cb_x
    box.y = cb_y
    box.w = table_w
    
    content_x = box.x + box.margin_left + box.border_left + box.padding_left
    current_y = box.y + box.margin_top + box.border_top + box.padding_top
    
    # Lay out the table caption if present
    for child in box.children:
        if getattr(child.node, "tag", "") == "caption":
            # Treat as block context
            layout_block_context(child, content_x, current_y, box.w)
            current_y += (
                child.margin_top
                + child.border_top
                + child.padding_top
                + child.h
                + child.padding_bottom
                + child.border_bottom
                + child.margin_bottom
            )
            
    # 1. Collect all rows and cells
    rows = []
    
    # Helper to scan for rows (skipping over thead/tbody/tfoot for now)
    def _scan_for_rows(parent_box: Box):
        for child in parent_box.children:
            if isinstance(child, TableRowBox):
                rows.append(child)
            elif isinstance(child, TableRowGroupBox):
                _scan_for_rows(child)
                
    _scan_for_rows(box)
    
    if not rows:
        box.h = 0.0
        return
        
    # Find max columns
    num_cols = 0
    row_cells = []
    for row in rows:
        cells = [c for c in row.children if isinstance(c, TableCellBox)]
        num_cols = max(num_cols, len(cells))
        row_cells.append(cells)
        
    if num_cols == 0:
        box.h = 0.0
        return
        
    # 2. Distribute column widths dynamically (Shrink-to-fit)
    col_widths = [0.0] * num_cols
    
    from pypdfpatra.engine.font_metrics import measure_text, parse_font
    from pypdfpatra.engine.tree import TextBox

    def _get_text_nodes(n: Box) -> list:
        res = []
        if isinstance(n, TextBox):
            res.append(n)
        for c in n.children:
            if isinstance(c, Box):
                res.extend(_get_text_nodes(c))
        return res

    for cells in row_cells:
        for i, cell in enumerate(cells):
            cell_style = getattr(cell.node, "style", {}) if getattr(cell, "node", None) else {}
            _, css_w = _resolve_box_geometry(cell, cb_w, cell_style)
            
            cell_max_w = 20.0 # Min width
            for tbox in _get_text_nodes(cell):
                t_style = getattr(tbox.node, "style", {}) if getattr(tbox, "node", None) else {}
                family, fpdf_style, size = parse_font(t_style)
                w = measure_text(tbox.text_content.strip(), family, size, fpdf_style)
                if w > cell_max_w:
                    cell_max_w = w
            
            cell_padded_w = cell_max_w + cell.padding_left + cell.padding_right + cell.border_left + cell.border_right + 15.0 # Margin of safety
            
            if css_w > 0:
                cell_padded_w = max(cell_padded_w, css_w)
                
            if cell_padded_w > col_widths[i]:
                col_widths[i] = cell_padded_w
                
    total_table_w = sum(col_widths)
    
    # Scale width if exceeding bounds or explicitly forced
    if css_width > 0:
        if total_table_w < css_width:
            extra = (css_width - total_table_w) / num_cols
            col_widths = [cw + extra for cw in col_widths]
            total_table_w = css_width
    elif total_table_w > cb_w and cb_w > 0:
        scale = cb_w / total_table_w
        col_widths = [cw * scale for cw in col_widths]
        total_table_w = cb_w
        
    box.w = total_table_w
    
    # 3. Layout cells and synchronize row heights
    for row in rows:
        # Resolve row geometry (mostly margins/borders, usually 0 for TR)
        row_style = getattr(row.node, "style", {}) if row.node else {}
        _, row_css_w = _resolve_box_geometry(row, box.w, row_style)
        
        row.x = content_x
        row.y = current_y
        row.w = box.w
        
        row_content_x = row.x + row.border_left + row.padding_left
        
        cells = [c for c in row.children if isinstance(c, TableCellBox)]
        max_cell_h = 0.0
        
        for i, cell in enumerate(cells):
            # Layout the cell as a block container!
            # It gets its designated column width constraint
            cell_x = row_content_x + sum(col_widths[:i])
            # Layout the block context within the cell
            layout_block_context(cell, cell_x, row.y, col_widths[i])
            
            # cell.w is set by layout_block_context usually to col_w minus its own margins
            max_cell_h = max(max_cell_h, cell.h + cell.padding_top + cell.padding_bottom + cell.border_top + cell.border_bottom)
            
        # Synchronize all cells in this row to exactly max_cell_h
        for cell in cells:
            cell.h = max_cell_h - cell.padding_top - cell.padding_bottom - cell.border_top - cell.border_bottom
            
        row.h = max_cell_h
        current_y += row.h + row.border_top + row.border_bottom + row.margin_top + row.margin_bottom
        
    box.h = current_y - box.y - box.margin_top - box.border_top - box.padding_top
