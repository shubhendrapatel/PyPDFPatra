# PyPDFPatra: Supported CSS Properties & Selectors

This document outlines the subset of W3C CSS specifications currently supported by the PyPDFPatra rendering engine. Because PDF generation differs from interactive browser rendering, not all browser properties translate natively.

## Selectors (CSS 1 & CSS 2.1)
The mapping engine (powered by parsed ASTs from `tinycss2`) fully applies the cascading rules for the following basic selectors:
* **Universal (CSS 2.1)**: `*`
* **Type/Tag (CSS 1)**: `div`, `p`, `h1`, `span`, etc.
* **Class (CSS 1)**: `.classname`
* **ID (CSS 1)**: `#idname`
* **Combinators**: Descendant (` `), Child (`>`), Adjacent Sibling (`+`), General Sibling (`~`)
* **Attribute Selectors**: `[attr]`, `[attr="value"]`
* **Pseudo-classes**: `:first-child`, `:last-child`, `:first-of-type`, `:last-of-type`, `:nth-child()`, `:nth-of-type()`
* **Pseudo-elements**: `::before`, `::after` (with `content` support)

## The Cascade & Specificity (CSS 2.1 §6)
The engine strictly follows the W3C cascading order:
1. **`!important` Declarations**: Correctly prioritized.
2. **Specificity Calculation**: Weights are applied by (IDs, Classes/Attributes/Pseudo-classes, Tags/Pseudo-elements).
3. **Source Order**: Later rules override earlier ones of equal specificity.
4. **`!important` vs Inline**: Author `!important` rules correctly override normal inline `style=""` declarations.

## Display & Box Model (CSS 2.1)
The block formatting context and inline formatting context support W3C-standard flow layout.
* **`display`**: `block`, `inline`, `inline-block`, `none`, `list-item`, `table`, `table-row`, `table-cell`, `flex`.
* **`box-sizing`**: `content-box`, `border-box` (W3C standard box model sizing).
* **`visibility`**: `visible`, `hidden`.

## Positioning (CSS 2.1)
* **`position`**: `static`, `relative`, `absolute`, `fixed`.
* **`top`**, **`right`**, **`bottom`**, **`left`**: Support for absolute and relative offsets.
* **`z-index`**: Controls stacking order of overlapping elements.

### Paged Media (position: fixed)
In the PDF context, **`position: fixed`** follows the W3C paged media standard by repeating the element on **every page** of the document. This is the primary method for creating global headers and footers.

### Flexbox Support
Current implementation support flex containers with:
- **`display: flex`**
- **`flex-direction`**: `row`, `column`.
- **`justify-content`**: `flex-start`, `flex-end`, `center`, `space-between`.
- **`align-items`**: `stretch` (default), `flex-start`, `flex-end`, `center`.
- **Intrinsic Sizing**: Flex items with `width: auto` correctly size themselves to their content (text/images) before distribution.

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

### Table Cells & Spacing
* **`border-spacing`**: Supports pixel values for horizontal and vertical gutter between cells.
* **`colspan`**: HTML attribute support for merging columns.
* **`rowspan`**: HTML attribute support for merging rows.

## Typography & Text (CSS 1 & CSS 2.1)
* **`font-family`** (CSS 1): Support for standard PDF metrics (Courier, Helvetica, Times) and custom TrueType fonts via `@font-face` embedding.
* **`font-size`** (CSS 1): Specified in `em` or `px` (automatically scales line heights)
* **`font-weight`** (CSS 1): `bold`, `normal`
* **`font-style`** (CSS 1): `italic`, `normal`
* **`text-align`** (CSS 1): `left`, `center`, `right` (aligns text within its containing block)
* **`text-decoration`** (CSS 1): `underline`, `line-through` (also triggered automatically by standard `<u>`, `<s>`, `<del>` HTML tags)
* **`white-space`** (CSS 1): `pre` (Supported; preserves explicit spaces and newlines over standard wrapping)
* **`line-height`**: Specified in absolute points or relative unitless values (e.g., `1.6`).
* **`text-transform`**: `uppercase`, `lowercase`, `capitalize`.

## Colors & Backgrounds (CSS 1, CSS 2.1, CSS Color Module Level 4)
Colors can be specified using short hex (e.g., `#fff`), standard hex (e.g., `#ffffff`), or by directly typing any of the 148 standard W3C CSS4 named colors (e.g., `blue`, `papayawhip`, `cornflowerblue`).
* **`color`** (CSS 1)
* **`background-color`** (CSS 1)
* **`background-image`**: Support for local and remote image URLs.

## Lists (CSS 1 & 2.1)
* **`list-style-type`**: `disc`, `circle`, `square`, `decimal`, `decimal-leading-zero`.

## Special Values/Keywords (CSS 2.1 & CSS 3)
The W3C cascade inheritance model correctly propagates the following special keywords down the DOM tree.
* **`inherit`** (CSS 2.1): Specifically pulls the parent's computed property.
* **`currentColor`** (CSS 3 Color Module): Syncs styling properties (like borders) strictly to the rendered text color scalar.
* **`transparent`** (CSS 2.1): Renders 0,0,0 scalar internally but bypasses background fill.

