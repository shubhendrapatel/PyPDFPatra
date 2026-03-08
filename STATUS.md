# PyPDFPatra — Project Status

Legend: ✅ Done · 🔄 In Progress · ⬜ Not Started

---

## Roadmap

### Phase 1: W3C Pipeline Restructuring (✅ Done)
- Implement `engine/style.py` (CSSOM, inherited properties, user-agent defaults)
- Update Cython tree with specific `Box` classes (`BlockBox`, `InlineBox`, `TextBox`)
- Implement `engine/box_generator.py` (DOM to Box Tree via `display`)
- Implement `engine/layout_block.py` (BFC) and `engine/layout_inline.py` (IFC)

### Phase 2: Refinement & CSS Integration (✅ Done)
- Integrate `tinycss2` to parse `<style>` blocks and CSS.
- Implement `engine/shorthand.py` to expand CSS shorthands.
- Ensure selector matching works for tags, classes, and IDs.

### Phase 3: Visual Styling & Forms (🔄 In Progress)
- **Border and Padding**: Render borders (solid, dashed, dotted, double) and padding correctly in `render.py`. (✅)
- **Forms**: Implement replaced element layout for `<input>`, `<textarea>`, `<button>`. (⬜)

### Phase 4: Complex Layout Contexts (✅ Done)
- **Lists**: Generate `MarkerBox` for bullets and numbers (`<li>`). (✅)
- **Tables**: Implement W3C Table Formatting Context (`display: table`, `table-row`, `table-cell`). (✅)

### Phase 5: External Assets & Media (🔄 In Progress)
- **Images**: Download and measure `<img>` elements for replaced layout and PDF rendering. (✅)
- **Fonts**: Map `font-family` to `.ttf`/`.otf` files and embed them into the PDF engine. (⬜)

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
| `engine/font_metrics.py` | Accurate text measurement via FPDF metrics |

### ⬜ Still Needs to be Created

| File | Purpose | Priority |
|---|---|---|
| `engine/font_resolver.py` | Resolve `font-family` → actual font file, load into `fpdf2` | 🟡 Medium |
| `engine/image.py` | Fetch and place `<img>` elements on the PDF canvas | 🟡 Medium |
| `engine/page.py` | Page size, `@page` CSS rules, page-break handling | 🟡 Medium |

---

## CSS W3C Spec Compliance

### Box Model (CSS2.1 §8)

| Property | Status |
|---|---|
| `width`, `height` — `<length>`, `auto` | ✅ |
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
| `display: inline-block` | ⬜ |
| `display: table`, `table-row`, `table-cell` | ✅ |
| `position: static` (normal flow) | ✅ |
| `position: relative / absolute / fixed` | ⬜ |
| `float: left / right` | ⬜ |
| `overflow` | ⬜ |

### Typography (CSS2.1 §15–16)

| Property | Status |
|---|---|
| `font-size` — UA defaults (`2em`, `1.5em`) | ✅ |
| `color` | ✅ |
| `font-family` | ⬜ |
| `font-weight: bold` | ✅ |
| `font-style: italic` | ✅ |
| `text-decoration: underline / line-through` | ✅ |
| `vertical-align: sub / super` | ⬜ |
| `line-height` | ⬜ |
| `text-align: left/center/right` | ✅ |
| Inline text line-wrapping (IFC) | ✅ |

### Backgrounds & Colors (CSS2.1 §14)

| Property | Status |
|---|---|
| `background-color` — hex (`#rrggbb`) | ✅ |
| `background-color` — named colors, `rgb()` | ✅ |
| `background-image` | ⬜ |
| `opacity` | ⬜ |

### CSS Length Units

| Unit | Status |
|---|---|
| `px`, `%`, `auto`, `inherit`, `currentColor` | ✅ |
| `em`, `rem` | ⬜ |
| `pt`, `cm`, `mm`, `in` | ⬜ |

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
| Painting / Z-order | CSS2.1 App. E | 🔄 |
| Stylesheet parsing (`<style>` / `.css`) | CSS2.1 §2 | ✅ |
| Page model / `@page` rules | CSS Paged Media | ⬜ |
