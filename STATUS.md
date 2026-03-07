# PyPDFPatra — Project Status

Legend: ✅ Done · 🔄 In Progress · ⬜ Not Started

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

### ⬜ Still Needs to be Created

| File | Purpose | Priority |
|---|---|---|
| `engine/shorthand.py` | Expand `margin`, `padding`, `border`, `font` shorthands to longhands | 🔴 High |
| `engine/css_parser.py` | Parse `<style>` blocks and external `.css` files via `tinycss2` | 🟡 Medium |
| `engine/font_resolver.py` | Resolve `font-family` → actual font file, load into `fpdf2` | 🟡 Medium |
| `engine/image.py` | Fetch and place `<img>` elements on the PDF canvas | 🟡 Medium |
| `engine/page.py` | Page size, `@page` CSS rules, page-break handling | 🟡 Medium |
| `engine/layout_table.py` | CSS Table formatting context (`display: table`) | 🟠 Low |

---

## CSS W3C Spec Compliance

### Box Model (CSS2.1 §8)

| Property | Status |
|---|---|
| `width`, `height` — `<length>`, `auto` | ✅ |
| `box-sizing: content-box / border-box` | ✅ |
| `margin-top/right/bottom/left` | ✅ |
| `padding-top/right/bottom/left` | ✅ |
| `margin: <shorthand>`, `padding: <shorthand>` | ⬜ |
| `border-width / border-style / border-color` | ⬜ |
| Margin collapsing (§8.3.1) | ✅ |

### Visual Formatting / Display (CSS2.1 §9)

| Property | Status |
|---|---|
| `display: block` | ✅ |
| `display: none` | ✅ |
| `display: inline` | 🔄 (identified, laid out as block) |
| `display: list-item` | 🔄 (identified, no bullet rendering) |
| `display: inline-block` | ⬜ |
| `position: static` (normal flow) | ✅ |
| `position: relative / absolute / fixed` | ⬜ |
| `float: left / right` | ⬜ |
| `overflow` | ⬜ |

### Typography (CSS2.1 §15–16)

| Property | Status |
|---|---|
| `font-size` — UA defaults (`2em`, `1.5em`) | ✅ |
| `color` | ⬜ |
| `font-family` | ⬜ |
| `font-weight: bold` | ⬜ |
| `font-style: italic` | ⬜ |
| `line-height` | ⬜ |
| `text-align` | ⬜ |
| Inline text line-wrapping (IFC) | ✅ |

### Backgrounds & Colors (CSS2.1 §14)

| Property | Status |
|---|---|
| `background-color` — hex (`#rrggbb`) | ✅ |
| `background-color` — named colors, `rgb()` | ⬜ |
| `background-image` | ⬜ |
| `opacity` | ⬜ |

### CSS Length Units

| Unit | Status |
|---|---|
| `px`, `%`, `auto`, `inherit` | ✅ |
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
| Painting / Z-order | CSS2.1 App. E | ⬜ |
| Stylesheet parsing (`<style>` / `.css`) | CSS2.1 §2 | ⬜ |
| Page model / `@page` rules | CSS Paged Media | ⬜ |
