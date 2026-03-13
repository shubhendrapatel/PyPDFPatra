# Architectural Decision Log

This document tracks important implementation decisions, design choices, and CSS/HTML specification interpretations for PyPDFPatra.

## CSS User-Agent Default Styles

### Why do Tables have no borders by default?
**Context**: During the implementation of the W3C Table Formatting Context (`layout_table.py`), tables rendered without any borders.
**Decision**: In standard W3C HTML specifications, `<table>`, `<th>`, and `<td>` elements **do not** have borders by default. Users must explicitly define table borders using CSS (e.g., `border: 1px solid black`) or inline styles.
**Implementation**: Our User-Agent stylesheet (`engine/style.py`) explicitly defaults them to `display: table` and `table-cell` without border rules to strictly comply with browsers.

### CSS Selectors & Cascading
**Context**: Moving from basic tag/class selectors to a full CSS engine.
**Decision**: We implemented a W3C-compliant CSS selector and cascading engine.
- **Selectors**: Support for Descendant, Child, Adjacent Sibling, and General Sibling combinators, as well as Attribute selectors and nth-child/nth-of-type pseudo-classes.
- **Cascading & Specificity**: We implemented the W3C specificity algorithm (IDs, Classes/Pseudo-classes, Tags) and support for `!important` declarations.
- **Cascade Resolution**: Author `!important` rules correctly override inline `style=` normal rules, and inline `!important` takes absolute precedence. This ensures that the engine behaves identically to modern browser layout engines.

## Architecture & Layout Engine

### Cython for the Render Tree (`tree.pxd`, `tree.pyx`)
**Context**: Rebuilding the layout engine for a PDF generator capable of rendering hundreds of pages.
**Decision**: We use Cython extension types (`cdef class`) for the AST Box elements (`BlockBox`, `TextBox`, `TableBox`, etc.). Constructing a DOM and Box tree in pure Python for a 500-page document requires millions of objects, leading to severe memory bloat and slow GC pauses. Cython C-structs provide high-speed property access and smaller memory footprints during layout calculations.

### Strict W3C CSS Box Model
**Context**: Handling margins, borders, paddings, and widths.
**Decision**: We explicitly mirror the W3C CSS2.1 / CSS3 Formatting Contexts (Block, Inline, Table). The `box_generator.py` maps elements strictly by their `display` CSS property (not HTML tag semantics) to route them into `layout_block`, `layout_inline`, or `layout_table`. This guarantees that users familiar with browser CSS can predict how their PDFs will generate.
**Height Calculation**: We modified `_parse_length` to distinguish between `auto` (returns `None`) and `0px` (returns `0.0`). This ensures that boxes with explicit zero height are respected and not treated as content-hugging containers.

### FPDF2 Graphics Backend
**Context**: Choosing a PDF generation backend dependency.
**Decision**: While engines like WeasyPrint use heavy native libraries (Cairo/Pango), we leverage `fpdf2` to keep PyPDFPatra lightweight and easy to install. However, FPDF2's coordinate system is strictly linear (incremental Y-cursor). We abstract this away: the Cython layout engines calculate absolute `X/Y/W/H` coordinates in a vacuum, and `render.py` translates those into FPDF drawing commands at the very end.

### Multi-page Splitting (Backgrounds & Borders)
**Context**: Elements like `<div>` traversing across page breaks.
**Decision**: We do *not* split the Cython layout tree into "page fragments" during the layout phase. The layout phase computes a single infinite vertical scrolling canvas. During `render.py`, as we draw borders and backgrounds, we mathematically slice the rendering instructions using `PAGE_HEIGHT`, skipping down to a new page programmatically if the absolute `Y` coordination crosses a multiple of the page height.

### FPDF Graphics State Management (Invisible Text Bug)
**Context**: When content (like a paragraph or background) spans multiple pages, switching back and forth between pages in FPDF caused subsequent text to become invisible or lose its color.
**Decision**: FPDF 2 internally caches the "current" font and color. Our manual page-switching mechanism (`pdf.page = X`) does not always trigger a cache invalidate. 
**Implementation**: We modified `_ensure_page` to explicitly reset `pdf.font_family`, `pdf.text_color`, and other state trackers to `None`. This forces FPDF to re-emit the necessary PDF operators (like `Tf` for fonts and `rg` for colors) on every new page fragment, ensuring visual consistency.

### Non-Destructive Table Fragmentation
**Context**: When a table row is pushed to a new page to accommodate a repeating header, the content of the first row on the new page was originally being cleared and re-laid out, leading to data loss.
**Decision**: We implemented a recursive `shift_box` utility. Instead of destroying and re-creating the render tree fragments, we calculate the vertical displacement (`dy`) required to clear the header and page margin, and recursively apply that shift to the existing row and all its nested children (LineBoxes, TextBoxes). This preserves the integrity of the layout while moving it to the correct coordinate space.

## Implementation Details

### List Item Bullets (`disc`, `square`)
**Context**: Rendering unordered list marks.
**Decision**: Instead of relying on Unicode bullets (`•`, `▪`), which often fail to render or show up as missing-character boxes if the embedded TrueType font lacks the specific glyph, we inject special `__disc__` and `__square__` payload strings into `MarkerBox` elements. During rendering, `render.py` intercepts these and uses vector graphics (`pdf.ellipse`, `pdf.rect`) to draw perfect, font-independent bullets.

### TrueType Fonts & Text Measurement
**Context**: Calculating the geometry of text blocks.
**Decision**: FPDF's built-in fonts (Helvetica) lack comprehensive Unicode support. We require explicit TTF font inclusion. `font_metrics.py` dynamically interfaces with FPDF's internal font dictionary cache to measure string widths before drawing them, feeding those floating-point measurements back up to the Inline Formatting Context (`layout_inline.py`) to trigger accurate line-wrapping.

## Deferred Features

### Fragmentation vs. Shifting (CSS2.1 §13.3)
**Context**: Large blocks near page boundaries.
**Decision**: We distinguish between "atomic" and "fragmentable" content.
- **Implemented Behavior**:
    1.  **Atomic Content**: Elements like `<img>`, `<table>` (smaller than a full page), or boxes with `page-break-inside: avoid` shift to the next page entirely if the remaining space is less than their predicted height.
    2.  **Fragmentable Content**: standard `BlockBox` containers and `IFC` (paragraphs) fragment across page boundaries line-by-line.
    3.  **Border Integrity**: Vertical borders and backgrounds are now mathematically "sliced" at page margins (`DEFAULT_MARGIN_TOP/BOTTOM`) during rendering to prevent bleeding into headers/footers.
    4.  **Table Fragmentation**: Large tables that exceed a full page are allowed to fragment. Individual rows `<tr>` are treated as atomic units (they should stay together on one page) but the table itself continues.

### Table Header Repetition (`<thead>`)
**Decision**: To improve readability of fragmented tables, `<thead>` blocks will be repeated at the top of every new page the table occupies.
**Architectural Note**: This is handled in `layout_table.py` by monitoring the vertical cursor. When a row is pushed to a new page, the header height is added as a prefix to the new page fragment.

### Position: Fixed Repetition (Paged Media Standard)
**Context**: In paged media (PDF), `position: fixed` elements should appear on every page according to W3C CSS2.1 §9.3.1.
**Decision**: We implement automatic repetition for fixed elements.
**Implementation**: Fixed boxes are collected into a separate layer during rendering. After the main BFC/IFC flow is drawn, the renderer iterates through all generated pages and "stamps" the fixed boxes at their relative page coordinates. This allows for simple global headers and footers.

### Basic Flexbox Support (Incomplete)
**Context**: Modern invoice samples (like WeasyPrint's) use `display: flex` for simple horizontal alignment.
**Decision**: We implemented a "Basic Flex Row" shortcut in `block.py` to support side-by-side block children.
**Caveat**: This is *not* a full W3C Flexbox Formatting Context (Phase 10). It does not support `flex-grow`, `justify-content`, or complex wrapping. It simply divides the container width equally among children and lays them out horizontally.

### HTML5 Semantic Tag Support
**Decision**: To ensure modern HTML documents render correctly as blocks, our User-Agent stylesheet (`user_agent.py`) includes default `display: block` rules for `aside`, `footer`, `section`, `header`, `article`, `main`, and `address`.

### Overflow Clipping (`overflow: hidden`)
**Context**: In `coverage.html`, `white-space: pre` blocks can bleed outside their containers if the content is too long. Standard W3C behavior for overflow is visible.
**Decision**: We have decided **not** to implement `overflow: hidden` at this stage. While `fpdf2` supports block-based clipping via `pdf.rect_clip()`, the interaction between clipping and our multi-page slicing logic requires careful design to avoid cutting off legitimate content at page boundaries.
