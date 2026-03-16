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
* **`transform`**: Visual-only 2D transformations.
    * `translate(x, y)` / `translateX(x)` / `translateY(y)`: **Fully Supported**. Effectively shifts the element without affecting document flow.
    * `scale(x, y)` / `rotate(angle)` / `skew(x, y)`: Currently **Placeholders** (Parsed and composed into a matrix but not yet rendered).
    * `matrix(a, b, c, d, e, f)`: Supported for translation components.
    * Support for all units: `px`, `pt`, `in`, `mm`, `cm`, `em`, `rem`.

### Paged Media (position: fixed)
In the PDF context, **`position: fixed`** follows the W3C paged media standard by repeating the element on **every page** of the document. This is the primary method for creating global headers and footers.

**⚠️ Important Requirement**: Fixed-position elements **MUST** have an explicit `height` CSS property (e.g., `height: 20px`). Without explicit height, the layout engine cannot reserve proper vertical space for the element on each page, potentially causing overlapping with content or inconsistent pagination.

```css
/* ✅ Correct */
.header {
    position: fixed;
    top: 0;
    height: 20px;
    width: 100%;
}

/* ❌ Wrong – will cause layout issues */
.header {
    position: fixed;
    top: 0;
    /* height: auto; or missing */
    width: 100%;
}
```

### Flexbox Support (CSS Flexible Box Layout Module Level 1)
The engine implements a comprehensive Flexbox Formatting Context (FFC):
- **`display: flex`**
- **`flex-direction`**: `row`, `column`, `row-reverse`, `column-reverse`.
- **`flex-wrap`**: `nowrap`, `wrap`, `wrap-reverse` (support for multi-line flex containers).
- **`justify-content`**: `flex-start`, `flex-end`, `center`, `space-between`.
- **`align-items`**: `stretch`, `flex-start`, `flex-end`, `center`.
- **`align-self`**: Per-item alignment override.
- **`align-content`**: Distribution of lines in multi-line containers.
- **`flex-grow`**, **`flex-shrink`**, **`flex-basis`**: Full support for flexible sizing and overflow handling.
- **`flex`**: Standard shorthand support.
- **`order`**: Support for custom item rendering order.
- **Intrinsic Sizing**: Flex items with `width: auto` correctly use "shrink-to-fit" (max-content) logic before flex calculations.

## Dimensions (CSS 1 & CSS 2.1)
Values can be specified in pixels (`px`), points (`pt`), inches (`in`), centimeters (`cm`), or millimeters (`mm`). Em (`em`) and Rem (`rem`) scaling is supported relative to current and root font sizes respectively.
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
* `ridge` (Creates a 3D ridged border)
* `groove` (Creates a 3D grooved border)

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
* **`line-height`**: Specified in absolute points, pixels, or relative unitless values (e.g., `1.6`).
* **`text-transform`**: `uppercase`, `lowercase`, `capitalize`.
* **`font-variant`**: `small-caps` (simulated).
* **`letter-spacing`**: Support for custom character spacing.
* **`hyphens`**: `auto` support via `pyphen` for automatic line-breaking.
* **`text-align`**: `left`, `center`, `right`, `justify`.

## Colors & Backgrounds (CSS 1, CSS 2.1, CSS Color Module Level 4)
Colors can be specified using short hex (e.g., `#fff`), standard hex (e.g., `#ffffff`), or by directly typing any of the 148 standard W3C CSS4 named colors (e.g., `blue`, `papayawhip`, `cornflowerblue`).
* **`color`** (CSS 1)
* **`background-color`** (CSS 1)
* **`background-image`**: Support for local and remote image URLs.

## Lists (CSS 1 & 2.1)
* **`list-style-type`**: `disc`, `circle`, `square`, `decimal`, `decimal-leading-zero`, `lower-roman`, `upper-roman`, `lower-alpha`, `upper-latin`.

## Special Values/Keywords (CSS 2.1 & CSS 3)
The W3C cascade inheritance model correctly propagates the following special keywords down the DOM tree.
* **`inherit`** (CSS 2.1): Specifically pulls the parent's computed property.
* **`currentColor`** (CSS 3 Color Module): Syncs styling properties (like borders) strictly to the rendered text color scalar.
* **`transparent`** (CSS 2.1): Renders 0,0,0 scalar internally but bypasses background fill.
## Paged Media (W3C Paged Media Module)
* **`@page` Rules**: Define custom page sizes (e.g., `A4`, `letter`) and margins.
* **Margin Boxes**: Support for standard W3C margin boxes:
    * `@top-left`, `@top-center`, `@top-right`
    * `@bottom-left`, `@bottom-center`, `@bottom-right`
* **Page Counters**: `counter(page)` and `counter(pages)` supported in `content`.
* **Named Strings (Phase 11)**: `string-set` and `string()` support for dynamic headers (e.g., repeating the nearest `<h2>` title).

## Page Break Controls (CSS Fragmentation Level 3)
* **`page-break-before: always`**: Forces elment to start on a new PDF page.
* **`page-break-after: always`**: Forces subsequent content to a new page.
* **`page-break-inside: avoid`**: Prevents a block (like a table row or image) from being split across page boundaries.

## Cross-References & Generated Content
* **`target-counter(#id, page)`**: Resolves the target's physical page number.
* **`attr(name)`**: Support for pulling attribute values (like `href`) into `content` pseudo-elements.
* **Function resolution**: Support for mixing strings, `attr()`, and `target-counter()` in the same `content` declaration.

## Interactive Navigation
* **Internal Links**: Support for `href="#id"` for document-level navigation.
* **PDF Bookmarks**: Automatic generation of PDF "Outlines" (bookmarks sidebar) from heading tags (`<h1>`-`<h6>`).
