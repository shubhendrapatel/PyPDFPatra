# PyPDFPatra: Supported CSS Properties & Selectors

This document outlines the subset of W3C CSS specifications currently supported by the PyPDFPatra rendering engine. Because PDF generation differs from interactive browser rendering, not all browser properties translate natively.

## Selectors (CSS 1 & CSS 2.1)
The mapping engine (powered by parsed ASTs from `tinycss2`) fully applies the cascading rules for the following basic selectors:
* **Universal (CSS 2.1)**: `*`
* **Type/Tag (CSS 1)**: `div`, `p`, `h1`, `span`, etc.
* **Class (CSS 1)**: `.classname`
* **ID (CSS 1)**: `#idname`

*Note: Pseudo-classes (like `:hover`), pseudo-elements (like `::before`), and complex combinators (like `div > p` or `div + p`) are currently under active development and not fully supported by the layout engine yet.*

## Display & Box Model (CSS 2.1)
The block formatting context and inline formatting context support W3C-standard flow layout.
* **`display`**: `block`, `inline`, `inline-block`, `none`, `list-item`, `table`, `table-row`, `table-cell`.
* **`box-sizing`**: `content-box`, `border-box` (W3C standard box model sizing).

## Dimensions (CSS 1 & CSS 2.1)
Values can be specified in pixels (`px`) or percentages (`%`). Em (`em`) scaling is supported relative to current font sizes.
* **`width`** (CSS 1)
* **`height`** (CSS 1)

## Margins & Paddings (CSS 1)
Standard W3C shorthand expansion is supported (e.g., `margin: 10px 20px;` correctly expands to top/bottom 10px, left/right 20px).
* **`margin`** (Shorthand)
* **`margin-top`**, **`margin-right`**, **`margin-bottom`**, **`margin-left`**
* **`padding`** (Shorthand)
* **`padding-top`**, **`padding-right`**, **`padding-bottom`**, **`padding-left`**

## Borders (CSS 1 & CSS 2.1)
Standard shorthand is supported (`border: 1px solid black;`).
* **`border`** (Shorthand) (CSS 1)
* **`border-width`**, **`border-style`**, **`border-color`** (CSS 1)
* Directional: **`border-top`**, **`border-right`**, **`border-bottom`**, **`border-left`** (CSS 1)

### Supported Border Styles (CSS 2.1 Specification)
* `solid`
* `dashed` (Vector-rendered)
* `dotted` (Vector-rendered)
* `double` (Rendered as two parallel lines)
* `none`
* `hidden`
* `inset` (Creates a simulated 3D recessed shadow effect)
* `outset` (Creates a simulated 3D raised button effect)

### Table Border Spacing
* **`border-spacing`**: Supports pixel values for horizontal and vertical gutter between cells.

## Typography & Text (CSS 1 & CSS 2.1)
* **`font-family`** (CSS 1): Support for standard PDF metrics (Courier, Helvetica, Times) and custom TrueType fonts via `@font-face` embedding.
* **`font-size`** (CSS 1): Specified in `em` or `px` (automatically scales line heights)
* **`font-weight`** (CSS 1): `bold`, `normal`
* **`font-style`** (CSS 1): `italic`, `normal`
* **`text-align`** (CSS 1): `left`, `center`, `right` (aligns text within its containing block)
* **`text-decoration`** (CSS 1): `underline`, `line-through` (also triggered automatically by standard `<u>`, `<s>`, `<del>` HTML tags)
* **`white-space`** (CSS 1): `pre` (Supported; preserves explicit spaces and newlines over standard wrapping)

## Colors & Backgrounds (CSS 1, CSS 2.1, CSS Color Module Level 4)
Colors can be specified using short hex (e.g., `#fff`), standard hex (e.g., `#ffffff`), or by directly typing any of the 148 standard W3C CSS4 named colors (e.g., `blue`, `papayawhip`, `cornflowerblue`).
* **`color`** (CSS 1)
* **`background-color`** (CSS 1)

## Lists (CSS 1 & 2.1)
* **`list-style-type`**: `disc`, `circle`, `square`, `decimal`, `decimal-leading-zero`.

## Special Values/Keywords (CSS 2.1 & CSS 3)
The W3C cascade inheritance model correctly propagates the following special keywords down the DOM tree.
* **`inherit`** (CSS 2.1): Specifically pulls the parent's computed property.
* **`currentColor`** (CSS 3 Color Module): Syncs styling properties (like borders) strictly to the rendered text color scalar.
* **`transparent`** (CSS 2.1): Renders 0,0,0 scalar internally but bypasses background fill.

