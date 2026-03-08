# Architectural Decision Log

This document tracks important implementation decisions, design choices, and CSS/HTML specification interpretations for PyPDFPatra.

## CSS User-Agent Default Styles

### Why do Tables have no borders by default?
**Context**: During the implementation of the W3C Table Formatting Context (`layout_table.py`), tables rendered without any borders.
**Decision**: In standard W3C HTML specifications, `<table>`, `<th>`, and `<td>` elements **do not** have borders by default. Users must explicitly define table borders using CSS (e.g., `border: 1px solid black`) or inline styles.
**Implementation**: Our User-Agent stylesheet (`engine/style.py`) explicitly defaults them to `display: table` and `table-cell` without border rules to strictly comply with browsers.

### CSS Selectors Support (MVP)
**Context**: A CSS rule like `.test-table th, .test-table td` didn't apply to the table cells.
**Decision**: The MVP CSS Matcher (`matcher.py`) currently only supports very basic tags, class, and ID queries (`div`, `.class`, `#id`), evaluating them linearly. It does not yet implement complex parsing for descendant selectors (`.class child`) or comma-separated composite rules. Inline styles (`style="..."`) are the most robust override mechanism in the MVP.

## Architecture & Layout Engine

### Cython for the Render Tree (`tree.pxd`, `tree.pyx`)
**Context**: Rebuilding the layout engine for a PDF generator capable of rendering hundreds of pages.
**Decision**: We use Cython extension types (`cdef class`) for the AST Box elements (`BlockBox`, `TextBox`, `TableBox`, etc.). Constructing a DOM and Box tree in pure Python for a 500-page document requires millions of objects, leading to severe memory bloat and slow GC pauses. Cython C-structs provide high-speed property access and smaller memory footprints during layout calculations.

### Strict W3C CSS Box Model
**Context**: Handling margins, borders, paddings, and widths.
**Decision**: We explicitly mirror the W3C CSS2.1 / CSS3 Formatting Contexts (Block, Inline, Table). The `box_generator.py` maps elements strictly by their `display` CSS property (not HTML tag semantics) to route them into `layout_block`, `layout_inline`, or `layout_table`. This guarantees that users familiar with browser CSS can predict how their PDFs will generate.

### FPDF2 Graphics Backend
**Context**: Choosing a PDF generation backend dependency.
**Decision**: While engines like WeasyPrint use heavy native libraries (Cairo/Pango), we leverage `fpdf2` to keep PyPDFPatra lightweight and easy to install. However, FPDF2's coordinate system is strictly linear (incremental Y-cursor). We abstract this away: the Cython layout engines calculate absolute `X/Y/W/H` coordinates in a vacuum, and `render.py` translates those into FPDF drawing commands at the very end.

### Multi-page Splitting (Backgrounds & Borders)
**Context**: Elements like `<div>` traversing across page breaks.
**Decision**: We do *not* split the Cython layout tree into "page fragments" during the layout phase. The layout phase computes a single infinite vertical scrolling canvas. During `render.py`, as we draw borders and backgrounds, we mathematically slice the rendering instructions using `PAGE_HEIGHT`, skipping down to a new page programmatically if the absolute `Y` coordination crosses a multiple of the page height.

## Implementation Details

### List Item Bullets (`disc`, `square`)
**Context**: Rendering unordered list marks.
**Decision**: Instead of relying on Unicode bullets (`•`, `▪`), which often fail to render or show up as missing-character boxes if the embedded TrueType font lacks the specific glyph, we inject special `__disc__` and `__square__` payload strings into `MarkerBox` elements. During rendering, `render.py` intercepts these and uses vector graphics (`pdf.ellipse`, `pdf.rect`) to draw perfect, font-independent bullets.

### TrueType Fonts & Text Measurement
**Context**: Calculating the geometry of text blocks.
**Decision**: FPDF's built-in fonts (Helvetica) lack comprehensive Unicode support. We require explicit TTF font inclusion. `font_metrics.py` dynamically interfaces with FPDF's internal font dictionary cache to measure string widths before drawing them, feeding those floating-point measurements back up to the Inline Formatting Context (`layout_inline.py`) to trigger accurate line-wrapping.
