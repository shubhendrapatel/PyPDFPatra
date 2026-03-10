# PyPDFPatra W3C Engine Refactor

## Phase 1: Structure Redesign
- [x] Implement [engine/style.py](file:///d:/programming/repo/PyPDFPatra/src/pypdfpatra/engine/style.py) (CSSOM, inherited properties, user-agent defaults)
- [x] Update [tree.pxd](file:///d:/programming/repo/PyPDFPatra/src/pypdfpatra/engine/tree.pxd) and [tree.pyx](file:///d:/programming/repo/PyPDFPatra/src/pypdfpatra/engine/tree.pyx) with specific `Box` classes (`BlockBox`, `InlineBox`, `LineBox`)
- [x] Implement [engine/box_generator.py](file:///d:/programming/repo/PyPDFPatra/src/pypdfpatra/engine/box_generator.py) (Convert DOM -> Box Tree via `display` properties)
- [x] Implement [engine/layout_block.py](file:///d:/programming/repo/PyPDFPatra/src/pypdfpatra/engine/layout_block.py) (W3C Block Formatting Context)
- [x] Implement [engine/layout_inline.py](file:///d:/programming/repo/PyPDFPatra/src/pypdfpatra/engine/layout_inline.py) (W3C Inline Formatting Context - basic line wrapping)
- [x] Update [main.py](file:///d:/programming/repo/PyPDFPatra/src/pypdfpatra/main.py) & [render.py](file:///d:/programming/repo/PyPDFPatra/src/pypdfpatra/render.py) to use the new Box Tree pipeline

## Phase 2: Refinement & CSS Integration
- [x] Integrate `tinycss2` to parse `<style>` blocks and external CSS files.
- [x] Implement [engine/shorthand.py](file:///d:/programming/repo/PyPDFPatra/src/pypdfpatra/engine/shorthand.py) to expand CSS shorthands (e.g., `margin: 10px 20px`).



## Phase 3: Visual Styling & Forms
- [x] Implement [border](file:///d:/programming/repo/PyPDFPatra/src/pypdfpatra/render.py#242-311) and `padding` rendering routines in [render.py](file:///d:/programming/repo/PyPDFPatra/src/pypdfpatra/render.py).
- [x] Implement Layout Generation ([box_generator.py](file:///d:/programming/repo/PyPDFPatra/src/pypdfpatra/engine/box_generator.py)) for Form elements (`<input>`, `<textarea>`, `<button>`) as replaced boxes with intrinsic sizing.

## Phase 4: Complex Layout Contexts
- [x] Implement `MarkerBox` generation and margin-area positioning for `<li>` list items.
- [x] Implement W3C Table Formatting Context ([layout_table.py](file:///d:/programming/repo/PyPDFPatra/src/pypdfpatra/engine/layout_table.py)) for dynamic fluid span grids.

## Phase 5: External Assets & Media
- [x] Implement Image fetching, size resolution, and rendering ([engine/image.py](file:///d:/programming/repo/PyPDFPatra/src/pypdfpatra/engine/image.py)).
- [x] Implement Custom Web Font fetching and embedding via `@font-face` resolution ([engine/font_metrics.py](file:///d:/programming/repo/PyPDFPatra/src/pypdfpatra/engine/font_metrics.py)).

## Phase 6: Print Pagination & Page Breaks (✅ Done)
- [x] Implement CSS Paged Media logic in layout engine to detect page boundaries (`PAGE_HEIGHT`).
- [x] Implement line-breaking and block-fragmentation to slice elements across multiple PDF pages.
- [x] Implement [defaults.py](file:///d:/programming/repo/PyPDFPatra/src/pypdfpatra/defaults.py) for global page/margin constants.

## Phase 7: Advanced PDF Features (🔄 In Progress)
- [ ] Implement PDF AcroForms for interactive fillable widgets.
- [ ] Implement PDF Outlines (Bookmarks) for navigation.
- [x] Implement Hyperlink Annotations.

## Phase 8: Refinement & Specialized Features (⬜ Not Started)
- [ ] Implement `overflow: hidden` via PDF clipping (Deferred — will decide on later date).
