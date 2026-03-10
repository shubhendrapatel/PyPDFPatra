# Extending PyPDFPatra

This guide explains how to add new features, CSS properties, or layout boxes to the PyPDFPatra engine.

## Adding a New CSS Property

1.  **Parser Update:** If the property is a shorthand, add it to `src/pypdfpatra/engine/styling/shorthand.py`.
2.  **Style Resolution:** If the property should follow specific inheritance rules, update `INHERITED_PROPERTIES` in `src/pypdfpatra/engine/styling/resolve.py`.
3.  **Layout Logic:** Implement the property handling in the relevant formatting context:
    -   `src/pypdfpatra/engine/layout/block.py` for block boxes.
    -   `src/pypdfpatra/engine/layout/inline.py` for inline/line-wrapping.
4.  **Rendering:** Update `src/pypdfpatra/render.py` to draw the effects of the new property (e.g., shadows, gradients).

## Adding a New Box Type

1.  **Cython Model:** Define the new Box class in `src/pypdfpatra/engine/tree.pyx`. Ensure it inherits from `Box` or a relevant specialized subclass.
2.  **Box Generation:** Update the factory logic in `src/pypdfpatra/engine/layout/box_generator.py` to instantiate your new box based on `display` styles or HTML tags.
3.  **Layout Context:** Create or update a layout function in `src/pypdfpatra/engine/layout/` to handle the geometry calculations for the new box.
4.  **Renderer:** Update `draw_boxes` in `src/pypdfpatra/render.py` to handle the painting of the new box type.

## Testing New Features

1.  Add a sample HTML file in `example/` or a new test case in `tests/`.
2.  Run the coverage script to verify the visual output:
    ```bash
    python example/test_coverage.py
    ```
