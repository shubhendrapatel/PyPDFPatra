# PyPDFPatra: CSS Property Pipeline & Transform Integration Guide

## Overview

This document describes the complete CSS property handling pipeline in PyPDFPatra, from parsing to rendering, with specific focus on where and how the `transform` property would be integrated.

---

## 1. CSS Property Parsing Pipeline

### 1.1 Entry Points

**Location**: `src/pypdfpatra/`

**Main Flow**:
```
HTML Input (api.py)
    ↓
Build Node Tree (HTMLParser → Node DOM)
    ↓
Parse Stylesheets (engine/styling/css_parser.py)
    ↓
Resolve Styles (engine/styling/resolve.py)
    ↓
Generate Box Tree (engine/layout/box_generator.py)
    ↓
Layout Phase (engine/layout/block.py, inline.py)
    ↓
Rendering (render.py)
```

### 1.2 Node & Style Dictionary Structure

**File**: `src/pypdfpatra/engine/tree.pyx`

```cython
cdef class Node:
    """DOM element with computed CSS styles"""
    tag: str           # e.g., 'div', 'p', 'span'
    props: dict        # HTML attributes
    children: list     # Child Node objects
    style: dict        # CSS properties (computed CSSOM)
    boxes: list        # Box geometry objects (created during layout)
    pseudos: dict      # Pseudo-element styles (::before, ::after)
    parent: Node       # Parent reference
```

The `style` dictionary example:
```python
{
    'display': 'block',
    'color': '#333333',
    'font-size': '16px',
    'margin-top': '10px',
    'position': 'absolute',
    'top': '50px',
    'left': '20px',
    # 'transform': 'translate(10px, 5px)'  <- Would be added here
}
```

### 1.3 CSS Stylesheet Parsing

**File**: `src/pypdfpatra/engine/styling/css_parser.py`

- **Parser**: Uses `tinycss2` library
- **Process**:
  - Finds `<style>` blocks and `<link rel="stylesheet">` tags
  - Parses CSS into AST rules
  - Extracts property declarations
  - Stores in `Node.style` dict

**Key Functions**:
```python
def parse_stylesheets(node: Node, base_url: str) -> None
def _find_css_sources(node: Node, css_sources: list, base_url: str) -> None
def _register_font_face(rule: tinycss2.ast.AtRule, base_url: str) -> None
```

### 1.4 Style Resolution & Cascading

**File**: `src/pypdfpatra/engine/styling/resolve.py`

**Cascade Order** (lowest to highest priority):
1. **User-Agent Defaults** (from `user_agent.py`)
   - e.g., `div → display: block`
2. **CSS Inheritance** (for inherited properties)
   - Properties in `INHERITED_PROPERTIES` frozenset
   - Inherited from parent's computed style
3. **Inline Styles** (from `style` attribute)
   - Highest priority
4. **Shorthand Expansion** (after cascade)
   - `margin: 10px 20px` → `margin-top`, `margin-right`, etc.

**Key Function**:
```python
def resolve_styles(node: Node, parent_style: dict = None) -> None:
    """
    Recursively computes final CSS for node and children.
    Modifies node.style in-place with full cascade resolved.
    """
```

**Inherited Properties** (where applicable):
```python
INHERITED_PROPERTIES = frozenset({
    'font-family', 'font-size', 'color', 'text-align',
    'line-height', 'visibility', 'white-space', ...
})
```

### 1.5 Shorthand Expansion

**File**: `src/pypdfpatra/engine/styling/shorthand.py`

Expands shorthand properties into their component parts:

**Examples**:
```python
# TRBL (Top, Right, Bottom, Left) shorthands
'margin: 10px 20px 30px 40px' →
    'margin-top: 10px'
    'margin-right: 20px'
    'margin-bottom: 30px'
    'margin-left: 40px'

# Border shorthand
'border: 1px solid black' →
    'border-width: 1px'
    'border-style: solid'
    'border-color: black'
    # Then expands each to TRBL
```

**Key Function**:
```python
def expand_shorthand_properties(style_dict: dict) -> dict:
    """Explodes shorthands into individual W3C components."""
```

---

## 2. Box Model & Layout Integration

### 2.1 Box Class Structure

**File**: `src/pypdfpatra/engine/tree.pyx`

```cython
cdef class Box:
    """Computed geometry for one element after layout"""
    
    # Position and size (content box)
    x: float
    y: float
    w: float
    h: float
    
    # CSS Spacing (Box Model)
    margin_top, margin_right, margin_bottom, margin_left: float
    padding_top, padding_right, padding_bottom, padding_left: float
    border_top, border_right, border_bottom, border_left: float
    
    # Positioning Properties (Phase 9)
    position: str      # 'static', 'relative', 'absolute', 'fixed'
    top: float         # stored as float('nan') if unset
    bottom: float
    left: float
    right: float
    z_index: int
    
    # Layout context
    page_name: str     # for named pages
    float_mode: str    # 'none', 'left', 'right'
    clear_mode: str    # 'none', 'left', 'right', 'both'
    
    # Reference back to source
    node: Node         # Original DOM node
    children: list     # Child Box objects
```

**Subclasses**:
- `BlockBox` - Block-level elements
- `InlineBox` - Inline elements
- `TextBox` - Text content
- `LineBox` - Line formatting context
- `TableBox`, `TableRowBox`, `TableCellBox` - Tables
- `ImageBox` - Images
- `InlineBlockBox` - Inline-block elements

### 2.2 Box Generation from Nodes

**File**: `src/pypdfpatra/engine/layout/box_generator.py`

**Process**:
1. Traverse Node tree
2. Create Box from Node based on `display` property
3. Parse and store positioning properties (top, left, right, bottom, position)
4. Process pseudo-elements (::before, ::after)
5. Recursively process children

**Key Function**:
```python
def generate_box_tree(node: Node, base_url: str) -> Box:
    """
    Creates a Box tree from Node tree.
    Parses CSS properties and populates Box attributes.
    """
    # Display type determines Box subclass:
    display = style.get('display', 'inline').strip().lower()
    if display == 'block': box = BlockBox(node)
    elif display == 'inline': box = InlineBox(node)
    elif display == 'table': box = TableBox(node)
    # ...
    
    # Populate positioning fields (Phase 9)
    pos = style.get('position', 'static').strip().lower()
    box.position = pos
    box.z_index = int(style.get('z-index', '0'))
    box.float_mode = style.get('float', 'none').lower()
    box.clear_mode = style.get('clear', 'none').lower()
```

---

## 3. Property Value Parsing

### 3.1 Length Parsing Function

**File**: `src/pypdfpatra/engine/layout/block.py`

```python
def _parse_length(
    value: str,
    parent_value: float,
    default_auto: float | None = 0.0,
    font_size: float = 12.0,
    root_font_size: float = 12.0,
) -> float | None:
    """Parse CSS length string (e.g. '10px', '50%', '10pt') to float"""
    
    if value == 'auto':
        return default_auto
    
    # Supported units:
    # px, pt, in, cm, mm, em, rem, %
    
    if value.endswith('px'):
        return float(value[:-2])
    elif value.endswith('pt'):
        return float(value[:-2])
    elif value.endswith('%'):
        return float(value[:-1]) / 100.0 * parent_value
    elif value.endswith('em'):
        return float(value[:-2]) * font_size
    # ... more units
```

### 3.2 Positioning Properties Parsing

**File**: `src/pypdfpatra/engine/layout/block.py` - `_resolve_box_geometry()`

```python
def _resolve_box_geometry(box, aw, style, pos_cb=None, root_font_size=12.0):
    """Resolve box model measurements"""
    
    # For positioning properties, unset values are stored as float('nan')
    box.top = _parse_length(
        style.get('top', 'nan'),
        aw,
        default_auto=float('nan'),  # ← Key: NaN for unset
        root_font_size=root_font_size
    )
    box.bottom = _parse_length(
        style.get('bottom', 'nan'),
        aw,
        default_auto=float('nan'),
        root_font_size=root_font_size
    )
    box.left = _parse_length(...)
    box.right = _parse_length(...)
```

**Why `float('nan')`?**
- Allow conditional logic: `if not math.isnan(box.left):`
- Don't confuse with `0` (valid position value)
- Simplifies absolute positioning calculations

---

## 4. Layout Phase: Positioning Application

### 4.1 Layout Phases Overview

**File**: `src/pypdfpatra/engine/layout/block.py`

```
Phase 9a: Box Geometry Calculation
    ↓ (margin, padding, border, width, height)
Phase 9b: Relative Positioning
    ↓ (visual shift via shift_box())
Phase 9c: Absolute/Fixed Positioning
    ↓ (_layout_positioned_children())
Block Layout
    ↓
Inline Layout
    ↓
Rendering
```

### 4.2a Relative Positioning

**Location**: `block.py: layout_block_context()` lines ~945-965

```python
# Phase 9: Relative Positioning Offset (Visual shift only)
if box.position == 'relative':
    from .inline import shift_box
    
    dx = 0.0
    dy = 0.0
    if not math.isnan(box.left):
        dx = box.left
    elif not math.isnan(box.right):
        dx = -box.right
    
    if not math.isnan(box.top):
        dy = box.top
    elif not math.isnan(box.bottom):
        dy = -box.bottom
    
    if dx != 0 or dy != 0:
        shift_box(box, dx, dy)
```

**Function**: `shift_box()` in [inline.py](inline.py#L162)

```python
def shift_box(b: Box, dx: float, dy: float) -> None:
    """Recursively shifts a box and its children"""
    b.x += dx
    b.y += dy
    for c in getattr(b, 'children', []):
        shift_box(c, dx, dy)
```

**Key Insight**: Relative positioning is a **visual-only offset** applied after normal layout. It doesn't affect document flow.

### 4.2b Absolute/Fixed Positioning

**Location**: `block.py: _layout_positioned_children()` lines ~1090+

```python
def _layout_positioned_children(
    box: Box,
    pos_cb: PosCB,  # Positioning Context Block (containing block)
    ...
):
    """Lays out absolute/fixed boxes relative to containing block"""
    
    for child_box in box.children:
        if child_box.position not in ('absolute', 'fixed'):
            continue
        
        # If position is fixed, use viewport; else use containing block
        if child_box.position == 'fixed':
            ref_x = 0.0
            ref_y = int(box.y / PAGE_HEIGHT) * PAGE_HEIGHT
            ref_w = PAGE_WIDTH
            ref_h = PAGE_HEIGHT
        else:
            ref_x, ref_y, ref_w, ref_h = pos_cb.x, pos_cb.y, pos_cb.w, pos_cb.h
        
        # Calculate initial position using top/left/bottom/right
        init_x = ref_x + box.left if not math.isnan(box.left) else ref_x
        init_y = ref_y + box.top if not math.isnan(box.top) else ref_y
        
        # Then recursively layout the absolutely-positioned box
        layout_block_context(
            child_box,
            init_x, init_y, child_box.w,
            pos_cb=new_pos_cb,
            ...
        )
```

---

## 5. Rendering Phase: Drawing Boxes

### 5.1 Render Infrastructure

**File**: `src/pypdfpatra/render.py`

**Main Structures**:
```python
def _draw_background(pdf, style, border_box_x, border_box_y, ...):
    """Paints background color across pages"""

def _draw_borders(pdf, style, border_top, border_bottom, ...):
    """Paints borders (solid, dashed, dotted, double, etc.)"""

def _draw_inline_backgrounds(pdf, box, style, ...):
    """Paints inline element backgrounds"""

def _draw_text(pdf, box, style, border_box_x, border_box_y, ...):
    """Paints text content"""
```

### 5.2 Box Rendering Coordinates

Rendering uses **Box.x** and **Box.y** coordinates directly (content box origin).

The box model is respected:
```
Margin Box (outermost)
├── border_box_x = x + margin_left
├── Border Box
│   ├── padding_box_x = x + margin_left + border_left
│   ├── Padding Box
│   │   ├── content_box_x = x + margin_left + border_left + padding_left
│   │   └── Content
```

### 5.3 Transformation During Rendering

**Currently**: No transformation is applied during rendering.

**Where to Apply Transform**:
- After calculating box position
- Before drawing to PDF
- Apply to all child coordinates recursively (like `shift_box`)

---

## 6. Integration Points for `transform` Property

### 6.1 Property Definition

**File to Modify**: `src/pypdfpatra/engine/tree.pyx`

**Add to Box class**:
```cython
cdef class Box:
    # ... existing attributes ...
    
    # Transformations (Phase 9)
    transform: str          # CSS transform property value
    transform_origin_x: float   # In px, defaults to 50% (center)
    transform_origin_y: float
```

### 6.2 Property Parsing

**File**: `src/pypdfpatra/engine/layout/box_generator.py`

**Where** (around line ~147):
```python
# Add after position parsing (Phase 9)
box.transform = style.get('transform', 'none').strip().lower()

# Later: parse transform-origin if needed
# origin = style.get('transform-origin', '50% 50%')
# Parse to (origin_x, origin_y)
```

### 6.2 Property Parsing (IMPLEMENTED)

**Files**:
- `src/pypdfpatra/engine/styling/transform_parser.py` - Parse CSS transform strings
- `src/pypdfpatra/engine/styling/transform_matrix.py` - Convert to PDF matrices

**Parsing Flow**:
```
CSS String: "translate(10px, 20px) rotate(45deg) scale(1.5)"
    ↓
transform_parser.parse_transform_string()
    ↓
Parsed: [
  {'type': 'translate', 'args': [10.0, 20.0], 'units': ('px', 'px')},
  {'type': 'rotate', 'args': [0.7854...]},      # 45° in radians
  {'type': 'scale', 'args': [1.5, 1.5]}
]
    ↓
transform_matrix.compose_transforms()
    ↓
PDF Matrix: [a, b, c, d, e, f] (single composed matrix)
```

### 6.3 Box Storage (IMPLEMENTED)

**File**: `src/pypdfpatra/engine/tree.pyx`

```cython
cdef class Box:
    # ... existing attributes ...
    cdef public list transform_matrix  # [a, b, c, d, e, f] or None
```

### 6.4 Integration in Box Generator (IMPLEMENTED)

**File**: `src/pypdfpatra/engine/layout/box_generator.py`

```python
from pypdfpatra.engine.styling.transform_parser import (
    parse_transform_string,
    normalize_length_to_pixels,
)
from pypdfpatra.engine.styling.transform_matrix import (
    compose_transforms,
    normalize_matrix,
)

# In generate_box_tree() after position parsing:
transform_str = style.get("transform", "none").strip().lower()
if transform_str and transform_str != "none":
    try:
        transforms = parse_transform_string(transform_str)
        if transforms:
            # Normalize length values to pixels
            for t in transforms:
                if "units" in t:
                    normalized_args = []
                    for i, arg in enumerate(t["args"]):
                        if i < len(t["units"]):
                            unit = t["units"][i]
                            normalized_args.append(
                                normalize_length_to_pixels(arg, unit)
                            )
                        else:
                            normalized_args.append(arg)
                    t["args"] = normalized_args
                    del t["units"]
            
            # Compose into single matrix
            matrix = compose_transforms(transforms)
            matrix = normalize_matrix(matrix)
            box.transform_matrix = matrix
    except Exception as e:
        import warnings
        warnings.warn(f"Failed to parse transform: {e}", UserWarning)
        box.transform_matrix = None
```

### 6.5 Rendering-Time Application (IMPLEMENTED)

**File**: `src/pypdfpatra/render.py`

```python
def _apply_transform(pdf: fpdf.FPDF, transform_matrix: list) -> bool:
    """
    Apply a CSS transformation matrix to the PDF graphics state.
    
    Args:
        pdf: FPDF instance
        transform_matrix: [a, b, c, d, e, f] or None
    
    Returns:
        True if a transform was applied (caller must call restore)
    """
    if transform_matrix is None:
        return False
    
    a, b, c, d, e, f = transform_matrix
    pdf.transform(a, b, c, d, e, f)
    return True


# In draw_boxes() function:
# Before drawing each box content:
transform_matrix = getattr(box, "transform_matrix", None)
transform_applied = False

if transform_matrix is not None:
    pdf.push_transformation_matrix()
    try:
        transform_applied = _apply_transform(pdf, transform_matrix)
    except Exception as e:
        warning.warn(f"Failed to apply transform: {e}")
        pdf.pop_transformation_matrix()
        transform_applied = False

# ... draw background, borders, text, children ...

# After all drawing is complete:
if transform_applied:
    pdf.pop_transformation_matrix()
```

---

## 6.6 Key Design Decision: Layout vs Rendering

**Important**: Unlike `position: relative`, the `transform` property:
- ✅ Does **NOT** affect document layout
- ✅ Does **NOT** affect positioning of siblings/children  
- ✅ Is a **visual-only** transformation
- ✅ Applied **during rendering only**, not during layout
- ✅ Applied via PDF's transformation matrix

This is why:
- Layout phase doesn't change
- Box coordinates remain unchanged
- Transforms applied at render-time via `pdf.transform()`

---

## 7. Summary: What Was Implemented

### Files Created (2):

1. **`transform_parser.py`** (~350 LOC)
   - `parse_transform_string()` - Parse CSS transform property
   - `parse_translate()`, `parse_scale()`, `parse_rotate()`, `parse_skew()`, `parse_matrix()`
   - Unit conversion and parsing helpers

2. **`transform_matrix.py`** (~250 LOC)
   - `translate_matrix()`, `scale_matrix()`, `rotate_matrix()`, `skew_matrix()`, `matrix_matrix()`
   - `multiply_matrices()` - Compose transforms into single matrix
   - `compose_transforms()` - Apply all transforms in order
   - `normalize_matrix()` - Round to avoid floating-point issues

### Files Modified (3):

1. **`tree.pyx`**
   - Added `transform_matrix` attribute to Box class

2. **`box_generator.py`**
   - Added imports for transform parser and matrix modules
   - Added transform parsing and composition in `generate_box_tree()`

3. **`render.py`**
   - Added `_apply_transform()` helper function
   - Modified `draw_boxes()` to apply/restore transformation matrix around box drawing

### Total Lines of Code: ~600 LOC

### No Changes to:
- Layout algorithm ✓
- Box positioning logic ✓
- Cascading/inheritance ✓
- CSS parsing system ✓

---

---

## 8. Rendering Pipeline Diagram

```
Box Layout Tree
    ↓
collect_fixed_boxes()
    ↓ (Filter position: fixed)
Anchor Registration
    ↓ (Register <a id="...">)
--- START RENDERING ---
    ↓
For each page:
  │
  ├─ For each Box (depth-first):
  │   ├─ Get style from Node.style
  │   ├─ Calculate absolute coordinates
  │   ├─ Draw background _draw_background()
  │   ├─ Draw borders _draw_borders()
  │   ├─ Draw text _draw_text()
  │   ├─ Draw children recursively
  │   └─ [NEW] Apply transform matrix ← HERE
  │
  └─ Iterate next page
```

---

## 9. User-Agent Defaults

**File**: `src/pypdfpatra/engine/styling/user_agent.py`

For future reference, default styles for elements:

```python
USER_AGENT_STYLES = {
    'html': {'display': 'block', 'font-size': '16px'},
    'body': {'display': 'block', 'margin': '8px'},
    'div': {'display': 'block'},
    'p': {'display': 'block', 'margin-top': '1em', 'margin-bottom': '1em'},
    # ... more
}

# For transform, no defaults needed (initial value is 'none')
```

---

## 10. Testing Strategy

### Unit Tests:
1. **Property Parsing**: `test_parse_transform('translate(10px, 5px)')`
2. **Matrix Calculation**: `test_transform_matrix_identity()`
3. **Rendering**: `test_render_transformed_element()`

### Integration Tests:
1. HTML with `style="transform: translate(10px, 5px)"`
2. Cascading through CSS rules
3. Inheritance (shouldn't inherit)
4. Multiple transforms: `translate(10px) rotate(45deg) scale(1.2)`

### Visualization Tests:
1. Compare rendered PDF with browser screenshot

---

## References

- **W3C CSS Transforms Module**: https://www.w3.org/TR/css-transforms-1/
- **PDF Specification - Transformations**: ISO 32000-1:2008, Section 8.3.2
- **PyPDFPatra Architecture**: See `docs/ARCHITECTURE.md`

