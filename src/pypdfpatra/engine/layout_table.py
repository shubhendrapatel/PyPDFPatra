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
    for row in rows:
        cells = [c for c in row.children if isinstance(c, TableCellBox)]
        num_cols = max(num_cols, len(cells))
        
    if num_cols == 0:
        box.h = 0.0
        return
        
    # 2. Distribute column widths evenly (MVP Table Layout Auto approximation)
    col_w = box.w / num_cols
    
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
            cell_x = row_content_x + (i * col_w)
            # Layout the block context within the cell
            layout_block_context(cell, cell_x, row.y, col_w)
            
            # cell.w is set by layout_block_context usually to col_w minus its own margins
            max_cell_h = max(max_cell_h, cell.h + cell.padding_top + cell.padding_bottom + cell.border_top + cell.border_bottom)
            
        # Synchronize all cells in this row to exactly max_cell_h
        for cell in cells:
            cell.h = max_cell_h - cell.padding_top - cell.padding_bottom - cell.border_top - cell.border_bottom
            
        row.h = max_cell_h
        current_y += row.h + row.border_top + row.border_bottom + row.margin_top + row.margin_bottom
        
    box.h = current_y - box.y - box.margin_top - box.border_top - box.padding_top
