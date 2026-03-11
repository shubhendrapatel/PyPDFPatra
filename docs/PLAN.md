# Mission: "Perfect Invoice" Layout

This plan outlines the steps required to achieve 1:1 visual parity with WeasyPrint for the `invoice.html` sample.

## 🛠️ Step 1: Advanced Selector Engine (Phase 8)
*   **Goal:** Allow the CSS matcher to handle the specialized selectors in `invoice.css`.
*   [ ] **Descendant Selectors:** Support `aside address` and `dt dd`.
*   [ ] **Pseudo-Classes:** Implement `:first-of-type` and `:last-of-type` for table column alignment.
*   [ ] **Pseudo-Elements:** Implement `::before` and `::after` with `content` support (needed for the colon `:` after labels).

## 🛠️ Step 2: Positioning & Stacking (Phase 9)
*   **Goal:** Enable absolute layout for the header info and the fixed footer.
*   [ ] **Absolute Positioning:** Remove elements from "Normal Flow" and place them using `top`, `bottom`, `right`, `left`.
*   [ ] **Anchor Logic:** Support positioning relative to the page boundary (needed for `bottom: 0` footer).

## 🛠️ Step 3: Flexbox Formatting Context (Phase 10)
*   **Goal:** Enable side-by-side addresses in the header.
*   [ ] **Flex Container:** Implement horizontal distribution for `display: flex`.
*   [ ] **Flex Alignment:** Support `justify-content` and `flex: 1`.

## 🛠️ Step 4: Paged Media Margin Boxes (Phase 11)
*   **Goal:** Correct footer placement for "Thank you!" and contact info.
*   [ ] **Margin Boxes:** Implement `@bottom-left` and `@bottom-right` in the page loop within `render.py`.

## 🛠️ Step 5: Visual Polish
*   [ ] **Text Transform:** Implement `text-transform: uppercase` in the renderer.
*   [ ] **White Space:** Support `white-space: pre-line` for address blocks.

## Verification
- Compare `example/invoice.pdf` against the WeasyPrint reference image.
