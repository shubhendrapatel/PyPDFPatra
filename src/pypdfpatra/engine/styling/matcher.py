"""
pypdfpatra.engine.styling.matcher
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This module handles the CSS 'Cascade'. It matches CSS selectors
(like .class or #id) to the Cython Nodes in the tree.
"""

from typing import List

import tinycss2

from pypdfpatra.defaults import SUPPORTED_PSEUDO_ELEMENTS
from pypdfpatra.engine.tree import Node

__all__ = ["apply_styles"]


def apply_styles(node: Node, rules: List[tinycss2.ast.Node]) -> None:
    """
    Recursively matches CSS rules to a Node and its children.
    """
    # Build ancestor list for descendant matching
    ancestors = []
    curr = node.parent
    while curr:
        ancestors.append(curr)
        curr = curr.parent

    # 1. Match Rules to this specific Node
    for rule in rules:
        if isinstance(rule, tinycss2.ast.QualifiedRule):
            # Parse selector into parts (handling basic combinators)
            selector_str = "".join(
                [
                    t.serialize()
                    if hasattr(t, "serialize")
                    else str(t.value)
                    if hasattr(t, "value")
                    else str(t)
                    for t in rule.prelude
                ]
            ).strip()

            # CSS Pseudo-elements (::...)
            pseudo_target = "style"
            for p_name in SUPPORTED_PSEUDO_ELEMENTS:
                p_str = f"::{p_name}"
                if p_str in selector_str:
                    pseudo_target = p_name
                    selector_str = selector_str.replace(p_str, "").strip()
                    break

            if _matches_selector(node, selector_str, ancestors):
                if pseudo_target == "style":
                    _inject_declarations(node, rule.content, node.style)
                else:
                    # Initialize pseudo-storage on demand
                    if pseudo_target not in node.pseudos:
                        node.pseudos[pseudo_target] = {}
                    _inject_declarations(
                        node, rule.content, node.pseudos[pseudo_target]
                    )

    # 1.5. Apply Inline Styles (e.g. <div style="...">)
    inline_style_str = node.props.get("style")
    if inline_style_str:
        inline_declarations = tinycss2.parse_declaration_list(
            inline_style_str, skip_comments=True, skip_whitespace=True
        )
        for decl in inline_declarations:
            if isinstance(decl, tinycss2.ast.Declaration):
                node.style[decl.name] = "".join(
                    [
                        t.serialize()
                        if hasattr(t, "serialize")
                        else str(t.value)
                        if hasattr(t, "value")
                        else str(t)
                        for t in decl.value
                    ]
                )

    # 2. Recursively apply to all children
    for child in node.children:
        apply_styles(child, rules)


def _matches_selector(node: Node, selector: str, ancestors: List[Node]) -> bool:
    """
    Supports: #id, .class, tag, descendant (a b), child (a > b),
              :first-of-type, :last-of-type
    """
    # Split by commas for multiple selectors (e.g. h1, h2)
    for part in [s.strip() for s in selector.split(",")]:
        if _matches_single_selector(node, part, ancestors):
            return True
    return False


def _matches_single_selector(node: Node, selector: str, ancestors: List[Node]) -> bool:
    """
    Handles a single selector string (no commas).
    """
    # Handle Child Combinator (a > b)
    if ">" in selector:
        parts = [p.strip() for p in selector.split(">")]
        target = parts[-1]
        parent_sel = " ".join(parts[:-1])
        if _matches_simple_selector(node, target):
            if ancestors and _matches_single_selector(
                ancestors[0], parent_sel, ancestors[1:]
            ):
                return True
        return False

    # Handle Descendant Combinator (a b)
    parts = selector.split()
    if len(parts) > 1:
        target = parts[-1]
        ancestor_sel = " ".join(parts[:-1])
        if _matches_simple_selector(node, target):
            # Check all ancestors
            for i, anc in enumerate(ancestors):
                if _matches_single_selector(anc, ancestor_sel, ancestors[i + 1 :]):
                    return True
        return False

    return _matches_simple_selector(node, selector)


def _matches_simple_selector(node: Node, selector: str) -> bool:
    """
    Matches #id, .class, tag, pseudo-classes, or attribute selectors on a single node.
    """
    if not selector:
        return False

    # 1. Attribute Selectors [attr=val]
    if selector.startswith("[") and selector.endswith("]"):
        inner = selector[1:-1]
        if "=" in inner:
            attr, val = inner.split("=", 1)
            val = val.strip("'\"")
            return node.props.get(attr) == val
        else:
            return inner in node.props

    # 2. Pseudo-classes (multiple can be chained: div:first-child:hover)
    if ":" in selector:
        if selector.startswith(":"):
            base = "*"
            pseudo_full = selector[1:]
        else:
            base, pseudo_full = selector.split(":", 1)

        if base != "*" and not _matches_simple_selector(node, base):
            return False

        # Multiple pseudos can be chained: :first-child:nth-of-type(2)
        for pseudo in [p.strip() for p in pseudo_full.split(":") if p]:
            args = ""
            if "(" in pseudo and pseudo.endswith(")"):
                pseudo, args = pseudo[:-1].split("(", 1)

            if pseudo == "first-of-type":
                if not node.parent:
                    return True
                siblings = [c for c in node.parent.children if c.tag == node.tag]
                if not (siblings and siblings[0] == node):
                    return False
            elif pseudo == "last-of-type":
                if not node.parent:
                    return True
                siblings = [c for c in node.parent.children if c.tag == node.tag]
                if not (siblings and siblings[-1] == node):
                    return False
            elif pseudo == "first-child":
                if not (node.parent and node.parent.children[0] == node):
                    return False
            elif pseudo == "last-child":
                if not (node.parent and node.parent.children[-1] == node):
                    return False
            elif pseudo == "nth-child":
                if not (
                    node.parent
                    and _matches_nth(node.parent.children.index(node) + 1, args)
                ):
                    return False
            elif pseudo == "nth-of-type":
                if not node.parent:
                    return True
                siblings = [c for c in node.parent.children if c.tag == node.tag]
                if not (
                    node in siblings and _matches_nth(siblings.index(node) + 1, args)
                ):
                    return False
            else:
                return False
        return True

    # 3. ID Matcher
    if selector.startswith("#"):
        return node.props.get("id") == selector[1:]

    # 4. Class Matcher
    if selector.startswith("."):
        target_class = selector[1:]
        node_classes = node.props.get("class", "").split()
        return target_class in node_classes

    # 5. Tag Matcher
    return selector == node.tag or selector == "*"


def _matches_nth(index: int, formula: str) -> bool:
    """
    Evaluates nth-child logic (Supports: 'odd', 'even', or a single integer).
    """
    formula = formula.strip().lower()
    if formula == "odd":
        return index % 2 != 0
    if formula == "even":
        return index % 2 == 0
    try:
        return index == int(formula)
    except ValueError:
        return False


def _inject_declarations(
    node: Node, content: List[tinycss2.ast.Node], target_style: dict
) -> None:
    """
    Parses CSS declarations and stores them in the provided style dictionary.
    """
    declarations = tinycss2.parse_declaration_list(content)
    for decl in declarations:
        if isinstance(decl, tinycss2.ast.Declaration):
            target_style[decl.name] = "".join(
                [
                    t.serialize()
                    if hasattr(t, "serialize")
                    else str(t.value)
                    if hasattr(t, "value")
                    else str(t)
                    for t in decl.value
                ]
            ).strip()
