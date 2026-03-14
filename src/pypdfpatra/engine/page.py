"""
pypdfpatra.engine.page
~~~~~~~~~~~~~~~~~~~~~
Handles @page rules and margin boxes for professional paged media.
"""

from typing import Dict, List

import tinycss2

from pypdfpatra.defaults import (
    DEFAULT_MARGIN_BOTTOM,
    DEFAULT_MARGIN_LEFT,
    DEFAULT_MARGIN_RIGHT,
    DEFAULT_MARGIN_TOP,
)
from pypdfpatra.engine.styling.shorthand import expand_shorthand_properties


class PageRule:
    def __init__(self, selector: str = ""):
        self.selector = selector  # "", ":first", ":left", ":right", or named page
        self.style: Dict[str, str] = {}
        self.margin_boxes: Dict[str, Dict[str, str]] = {}

    def __repr__(self):
        return f"<PageRule {self.selector}>"


def parse_page_rule(rule: tinycss2.ast.AtRule) -> PageRule:
    """Parses an @page rule into a PageRule object."""
    # Prelude contains the page selector (e.g., :first, or a name)
    prelude = "".join([t.serialize() for t in rule.prelude]).strip()
    page_rule = PageRule(prelude)

    # Content contains declarations and nested at-rules (margin boxes)
    content = tinycss2.parse_declaration_list(
        rule.content, skip_comments=True, skip_whitespace=True
    )

    for item in content:
        if isinstance(item, tinycss2.ast.Declaration):
            val = "".join(
                [
                    t.serialize()
                    if hasattr(t, "serialize")
                    else str(getattr(t, "value", t))
                    for t in item.value
                ]
            ).strip()
            page_rule.style[item.name] = val
        elif isinstance(item, tinycss2.ast.AtRule):
            # Check if it's a margin box rule (e.g., @top-left)
            if item.lower_at_keyword in (
                "top-left-corner",
                "top-left",
                "top-center",
                "top-right",
                "top-right-corner",
                "bottom-left-corner",
                "bottom-left",
                "bottom-center",
                "bottom-right",
                "bottom-right-corner",
                "left-top",
                "left-middle",
                "left-bottom",
                "right-top",
                "right-middle",
                "right-bottom",
            ):
                margin_box_name = item.lower_at_keyword
                margin_box_style = {}
                decls = tinycss2.parse_declaration_list(
                    item.content, skip_comments=True, skip_whitespace=True
                )
                for decl in decls:
                    if isinstance(decl, tinycss2.ast.Declaration):
                        val = "".join(
                            [
                                t.serialize()
                                if hasattr(t, "serialize")
                                else str(getattr(t, "value", t))
                                for t in decl.value
                            ]
                        ).strip()
                        margin_box_style[decl.name] = val
                page_rule.margin_boxes[margin_box_name] = expand_shorthand_properties(
                    margin_box_style
                )

    page_rule.style = expand_shorthand_properties(page_rule.style)
    return page_rule


def resolve_page_style(
    page_rules: List[PageRule], page_index: int, page_name: str = "default"
) -> PageRule:
    """
    Resolves the style for a specific page.
    page_index is 0-indexed.
    """
    curr_style = PageRule()

    # Sort order:
    # 1. Base @page (empty selector)
    # 2. Pseudo-classes (:first, :left, :right)
    # 3. Named pages (not yet supported fully but we can match selector)

    # For now, let's keep it simple:
    for rule in page_rules:
        match = False
        if rule.selector == "":
            match = True
        elif rule.selector == ":first" and page_index == 0:
            match = True
        elif rule.selector == ":left" and page_index % 2 != 0:
            # 0 is 1st (odd), 1 is 2nd (even/left)
            match = True
        elif rule.selector == ":right" and page_index % 2 == 0:
            match = True
        elif rule.selector == page_name:
            # Named page match
            match = True

        if match:
            # Merge styles
            curr_style.style.update(rule.style)
            # Merge margin boxes
            for mb_name, mb_style in rule.margin_boxes.items():
                if mb_name not in curr_style.margin_boxes:
                    curr_style.margin_boxes[mb_name] = {}
                curr_style.margin_boxes[mb_name].update(mb_style)

    return curr_style


def get_resolved_margins(page_rules, page_index, page_name="default"):
    """
    Returns a tuple (mt, mb, ml, mr) of resolved margins for a given page.
    """
    if not page_rules:
        return (
            DEFAULT_MARGIN_TOP,
            DEFAULT_MARGIN_BOTTOM,
            DEFAULT_MARGIN_LEFT,
            DEFAULT_MARGIN_RIGHT,
        )

    rule = resolve_page_style(page_rules, page_index, page_name)

    def _parse(k, d):
        val = rule.style.get(k, str(d))
        if not val:
            return float(d)
        val = str(val).strip().lower()
        try:
            if val.endswith("pt") or val.endswith("px"):
                return float(val[:-2])
            if val.endswith("in"):
                return float(val[:-2]) * 72.0
            if val.endswith("cm"):
                return float(val[:-2]) * 72.0 / 2.54
            if val.endswith("mm"):
                return float(val[:-2]) * 72.0 / 25.4
            return float(val)
        except (ValueError, TypeError):
            return float(d)

    return (
        _parse("margin-top", DEFAULT_MARGIN_TOP),
        _parse("margin-bottom", DEFAULT_MARGIN_BOTTOM),
        _parse("margin-left", DEFAULT_MARGIN_LEFT),
        _parse("margin-right", DEFAULT_MARGIN_RIGHT),
    )
