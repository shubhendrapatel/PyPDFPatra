# Visual Accuracy & Layout Fixes

This plan addressed the rendering discrepancies between PyPDFPatra and Chromium.

## Completed Changes

### 1. HR Element Rendering (✅ Done)
- **Fix:** Updated [style.py](file:///d:/programming/repo/PyPDFPatra/src/pypdfpatra/engine/style.py) UA styles to use `border-top` for a crisp single line, later refined to match Chromium's `inset` behavior where requested.

### 2. Table Consistency (✅ Done)
- **Fix:** Implemented `border-collapse`, `border-spacing`, and correctly centered captions in [layout_table.py](file:///d:/programming/repo/PyPDFPatra/src/pypdfpatra/engine/layout_table.py).

### 3. Centering (Block & Inline) (✅ Done)
- **Fix:** 
    - Block: Implemented `margin: auto` logic in [layout_block.py](file:///d:/programming/repo/PyPDFPatra/src/pypdfpatra/engine/layout_block.py).
    - Inline: Passed `text-align` through IFC to correctly shift line boxes in [layout_inline.py](file:///d:/programming/repo/PyPDFPatra/src/pypdfpatra/engine/layout_inline.py).

### 4. Text Decorations (✅ Done)
- **Fix:** Implemented custom line-drawing for `underline` and `line-through` in [_draw_text](file:///d:/programming/repo/PyPDFPatra/src/pypdfpatra/render.py#367-452) ([render.py](file:///d:/programming/repo/PyPDFPatra/src/pypdfpatra/render.py)). Fixed double-underline by removing built-in FPDF underline.

### 5. Border Fidelity (✅ Done)
- **Fix:** Rewrote [_draw_borders](file:///d:/programming/repo/PyPDFPatra/src/pypdfpatra/render.py#242-365) to use line-based drawing with support for `dashed`, `dotted`, and `double` styles, including half-width edge offsets for CSS alignment.

## Next: Page Break Handling

### 1. Line-box Overflow Detection
- **Problem:** Text is drawn at absolute coordinates that overflow the `PAGE_HEIGHT` (842.0). 
- **Cause:** [layout_inline.py](file:///d:/programming/repo/PyPDFPatra/src/pypdfpatra/engine/layout_inline.py) continues stacking line boxes vertically without checking if they fit on the current page.
- **Fix:** 
    - [ ] Update [layout_inline_context](file:///d:/programming/repo/PyPDFPatra/src/pypdfpatra/engine/layout_inline.py#299-366) to track available space.
    - [ ] Trigger a page break (adjust `current_y`) when a line box would overflow the page boundary.

## Verification Plan
1. Run [example/test_coverage.py](file:///d:/programming/repo/PyPDFPatra/example/test_coverage.py).
2. Verify that `box-model-1` text is visible on Page 4 (currently cut off at bottom of Page 3).

