# PyPDFPatra — Project Status

Legend: ✅ Done · 🔄 In Progress · ⬜ Not Started

---

### Phase 3: Visual Styling & Forms (✅ Done)
- **Border and Padding**: Render borders (solid, dashed, dotted, double) and padding correctly in `render.py`. (✅)
- **Forms**: Implement replaced element layout for `<input>`, `<textarea>`, `<button>`. (✅)

### Phase 4: Complex Layout Contexts (✅ Done)
- **Lists**: Generate `MarkerBox` for bullets and numbers (`<li>`). (✅)
- **Table Formatting**: Implement W3C Table Formatting Context (`display: table`, `table-row`, `table-cell`, `colspan`, `rowspan`). (✅)

### Phase 5: External Assets & Media (✅ Done)
- **Images**: Download and measure `<img>` elements for replaced layout and PDF rendering. (✅)
- **Fonts**: Map `font-family` to `.ttf`/`.otf` files and embed them into the PDF engine. (✅)

### Phase 6: Print Pagination & Page Breaks (✅ Done)
- **Pagination**: Implement W3C Paged Media logic for page boundaries. (✅)
- **Fragmentation**: Implement line-breaking and block-fragmentation across pages. (✅)
- **Table Fragmentation**: Improved non-destructive row shifting and repeating `<thead>` support. (✅)

### Phase 7: PDF Navigation (✅ Done)
- **Hyperlink Annotations**: Clickable links (External URLs and Internal #anchors). (✅)
- **PDF Outlines**: Table of Contents / Bookmarks for Headings. (✅)

### Phase 8: Advanced Selectors & Pseudo-Elements (✅ Done)
- **Complex Selectors**: Descendant ( `div p`), Child (`div > p`), Sibling (`+`, `~`), and Attribute selectors. (✅)
- **Pseudo-Elements**: `::before` and `::after` with `content` support. (✅)
- **Pseudo-Classes**: `:first-of-type`, `:last-of-type`, `:nth-child`, `:nth-of-type`. (✅)
- **Cascade & Specificity**: Full implementation of W3C specificity algorithm and `!important` support. (✅)

### Phase 9: Positioning & Stacking (✅ Done)
- **Relative Positioning**: Offset boxes without affecting flow. (✅)
- **Absolute Positioning**: Remove from flow and position relative to containers (including outer dimension logic). (✅)
- **Fixed Positioning**: Anchor boxes to page coordinates (e.g., footers). (✅ with explicit height requirement for paged media)
- **Z-Index**: Control overlapping paint order. (✅)
- **Note**: Fixed-position elements in paged media (headers/footers) must have explicit `height` CSS property for proper space reservation.

### Phase 10: Flexbox Formatting Context (✅ Done)
- **Flex Container**: `display: flex`. (✅ Support for row and column flow)
- **Flex Directions**: `row`, `column`. (✅ Robust axis management)
- **Distribution**: `justify-content` (flex-start, flex-end, center, space-between) and `align-items` (stretch, flex-start, flex-end, center). (✅)
- **Intrinsic Sizing**: Support for "fit-content" behavior on `width: auto` children. (✅)

### Phase 11: Professional Paged Media (✅ Done)
- **Margin Boxes**: Support for `@top-left`, `@bottom-right`, etc. (✅)
- **Page Counters**: Automatic page numbering (`content: counter(page)`). (✅)
- **Running Elements**: Repeating headers/footers via `position: running()`. (✅ Partial)
- **Named Strings**: `string-set` and `string()` for dynamic headers. (✅)
- **Cross-References**: `target-counter()` and `target-text()` for TOCs. (✅)

### Phase 12: Advanced Typography (✅ Done)
- **Text Transform**: `uppercase`, `lowercase`, `capitalize`. (✅)
- **Font Variants**: `small-caps` simulation. (✅)

### Phase 13: Professional Hyphenation & Spacing (✅ Done)
- **Hyphenation**: Automatic line breaking for long words using `pyphen`. (✅)
- **Letter Spacing**: `letter-spacing` (pts/em). (✅)

### Phase 14: CSS 2.1 Floats & Clearance (⬜ Next Up)
- **Floats**: `float: left / right`. Requires complex IFC integration for text flow wrapping.
- **Clearance**: `clear: left / right / both` support to break out of floating contexts.

### Phase 15: CSS3 Backgrounds & Visual Effects (⬜ Planned)
- **SVG Rendering**: Integration of an SVG engine (e.g., `svglib` or raw paths).
- **Borders**: `border-radius` (Rounded corners).
- **Transparency**: `opacity` support for text and boxes.
- **Backgrounds**: Linear gradients (`linear-gradient`) and `background-size: cover/contain`.

### Phase 16: CSS 2.1 Layout Polish (⬜ Planned)
- **Min/Max Dimensions**: `min-width`, `max-width`, `min-height`, `max-height`.
- **Vertical Alignment**: Full `vertical-align` support (top, middle, bottom, etc.) in IFC and Tables.
- **Overflow & Clipping**: `overflow: hidden / clip` support for box boundaries.
- **Text & Lists**: `text-indent`, `word-spacing`, and `list-style-position`.
- **Table Polish**: `caption-side: bottom` and `visibility: collapse`.

### Phase 17: Multi-Column Layout (⬜ Not Started)
- **CSS Multi-col**: `columns`, `column-gap`, `column-rule`.

### Phase 18: Modern CSS4 Selectors & Logic (⬜ Not Started)
- **Functional Pseudo-classes**: Support for `:is()`, `:where()`, and complex `:not()`.
- **Relational Pseudo-class**: Support for the `:has()` "parent" selector (requires selector engine refactor).
- **Advanced Colors**: Implementation of `color-mix()` and wide-gamut colors logic.

### Phase 19: CSS Grid Layout (⬜ Not Started)
- **Grid Container**: `display: grid`.
- **Grid Tracks**: `grid-template-columns`, `grid-template-rows`.
- **Grid Items**: `grid-column`, `grid-row` placement.
- **Grid Gaps**: `column-gap`, `row-gap`.

### Phase 20: Interactive PDF Forms (⬜ Not Started)
- **AcroForms**: Fillable text inputs, checkboxes, and radio buttons.
- **Form Actions**: Basic submit/reset behavior inside PDF.

### Phase 21: Next-Gen Logical CSS (⬜ Future)
- **Smart Theming**: `light-dark()` and `color-mix()` for automatic PDF styling.
- **Layout Logic**: `calc-size()` and `@layer` support for robust document architectures.
- **Conditional Styles**: Basic implementation of `if()` for template logic.
- **Container Queries**: Support for `@container` to allow components to resize gracefully within columns.

---

## Modules

### ✅ Created & Working

| File | Purpose |
|---|---|
| `src/pypdfpatra/api.py` | HTML → DOM `Node` tree (inline `style=` parsing, void elements) |
| `src/pypdfpatra/matcher.py` | Apply CSS selector rules to DOM nodes |
| `src/pypdfpatra/main.py` | Public `HTML(string=).write_pdf()` API, W3C pipeline orchestration |
| `src/pypdfpatra/render.py` | Walk Box Tree → `fpdf2` PDF drawing commands |
| `engine/tree.pxd` | Cython header — `Node` and `Box` hierarchy declarations |
| `engine/tree.pyx` | Cython `Node` and `Box` subclasses (`BlockBox`, `InlineBox`, `TextBox`) |
| `engine/style.py` | **CSSOM** — UA defaults, CSS inheritance, final style resolution |
| `engine/box_generator.py` | **Render Tree** — converts DOM `Node` tree → W3C `Box` subclasses via `display`. |
| `engine/layout_block.py` | **Block Formatting Context (BFC)** — vertical stacking, W3C width/height math, margin collapsing |
| `engine/layout_inline.py` | **Inline Formatting Context (IFC)** — horizontal text flow, line box generation, line-breaking. |
| `engine/__init__.py` | Exports the engine's public surface (`resolve_styles`, `generate_box_tree`, etc). |
| `engine/shorthand.py` | Expand `margin`, `padding`, `border`, `font` shorthands to longhands |
| `engine/css_parser.py` | Parse `<style>` blocks and external `.css` files via `tinycss2` |
| `engine/layout_table.py` | **Table Formatting Context** — dynamic column widths, cell alignment, border-spacing |
| `engine/image.py` | Fetch and place `<img>` elements on the PDF canvas |
| `src/pypdfpatra/defaults.py` | **Global Config** — A4 dimensions, standard margins, and content area constants |
| `src/pypdfpatra/logger.py` | Centralized logging for the library |

### ⬜ Still Needs to be Created

| File | Purpose | Priority |
|---|---|---|
| `engine/font_resolver.py` | Resolve `font-family` → actual font file, load into `fpdf2` | 🟡 Medium |
| `engine/page.py` | Page size, `@page` CSS rules, page-break handling | ✅ Done |

---

## CSS W3C Spec Compliance

### Box Model (CSS2.1 §8)

| Property | Status |
|---|---|
| `width`, `height` — `<length>`, `auto` | ✅ |
| `min-width`, `max-width`, `min-height`, `max-height` | 🔄 (Phase 16) |
| `box-sizing: content-box / border-box` | ✅ |
| `margin-top/right/bottom/left` | ✅ |
| `padding-top/right/bottom/left` | ✅ |
| `margin: <shorthand>`, `padding: <shorthand>` | ✅ |
| `border-width / border-style / border-color` | ✅ |
| Margin collapsing (§8.3.1) | ✅ |

### Visual Formatting / Display (CSS2.1 §9)

| Property | Status |
|---|---|
| `display: block` | ✅ |
| `display: none` | ✅ |
| `display: inline` | ✅ |
| `display: list-item` | ✅ |
| `display: inline-block` | ✅ |
| `display: table`, `table-row`, `table-cell` | ✅ |
| `position: static` (normal flow) | ✅ |
| `position: relative / absolute / fixed` | ✅ |
| `float: left / right` | 🔄 (Phase 14) |
| `display: flex` | ✅ |
| `display: grid` | ⬜ (Phase 19) |
| `overflow` | 🔄 (Phase 16) |

### Typography (CSS2.1 §15–16)

| Property | Status |
|---|---|
| `font-size` — UA defaults (`2em`, `1.5em`) | ✅ |
| `color` | ✅ |
| `font-family` | ✅ |
| `font-weight: bold` | ✅ |
| `font-style: italic` | ✅ |
| `text-decoration: underline / line-through` | ✅ |
| `vertical-align: top / middle / bottom / baseline` | 🔄 (Phase 16) |
| `line-height` | ✅ |
| `text-align: left/center/right/justify` | ✅ |
| `hyphens: auto` | partial (pyphen) |
| `text-transform: uppercase / lowercase / capitalize` | ✅ |
| `letter-spacing` | ✅ |
| `font-variant: small-caps` | ✅ |
| Inline text line-wrapping (IFC) | ✅ |

### Backgrounds & Colors (CSS2.1 §14)

| Property | Status |
|---|---|
| `background-color` — hex (`#rrggbb`) | ✅ |
| `background-color` — named colors, `rgb()` | ✅ |
| `background-image` | ✅ |
| `background-size: cover / contain` | 🔄 (Phase 15) |
| `opacity` | 🔄 (Phase 15) |
| `border-collapse: collapse` | ⬜ |

### CSS Length Units

| Unit | Status |
|---|---|
| `px`, `%`, `auto`, `inherit`, `currentColor` | ✅ |
| `em` | ✅ |
| `rem` | ✅ |
| `pt`, `cm`, `mm`, `in` | ✅ |

---

## Pipeline Stages

| Stage | Spec | Status |
|---|---|---|
| HTML Parsing → DOM | WHATWG HTML | ✅ |
| CSSOM — Cascade + Inheritance | CSS2.1 §6 | ✅ |
| User-Agent Default Styles | WebKit / HTML5 | ✅ |
| Render Tree (Box Tree) generation | CSS2.1 §9.1 | ✅ |
| Block Formatting Context (BFC) | CSS2.1 §9.4.1 | ✅ |
| Inline Formatting Context (IFC) | CSS2.1 §9.4.2 | ✅ |
| Painting / Z-order | CSS2.1 App. E | ✅ |
| Stylesheet parsing (`<style>` / `.css`) | CSS2.1 §2 | ✅ |
| Page model / `@page` rules | CSS Paged Media | ✅ Done |
| Margin boxes / Page numbering | CSS Paged Media | ✅ Done |
| Floats & Clearance | CSS2.1 §9.5 | 🔄 (Phase 14) |
| CSS3 Visuals (Borders/Gradients) | Various CSS3 Modules | 🔄 (Phase 15) |
| Layout Polish (Min/Max, Align) | CSS2.1 / Misc | 🔄 (Phase 16) |
| Multi-column Layout | CSS Multi-col | ⬜ (Phase 17) |
