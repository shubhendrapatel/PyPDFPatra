"""
pypdfpatra.engine.styling.matcher
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This module handles the CSS 'Cascade'. It matches CSS selectors
(like .class or #id) to the Cython Nodes in the tree.
"""

from typing import List, Tuple

import tinycss2

from pypdfpatra.defaults import SUPPORTED_PSEUDO_ELEMENTS
from pypdfpatra.engine.tree import Node

__all__ = ["apply_styles"]


def apply_styles(node: Node, rules: List[tinycss2.ast.QualifiedRule]) -> None:
    """
    Recursively matches CSS rules to a Node and its children, applying them
    according to W3C Specificity and !important rules.
    """
    # Build ancestor list for descendant matching
    ancestors = []
    curr = node.parent
    while curr:
        ancestors.append(curr)
        curr = curr.parent

    # 1. Collect all matching declarations from Rules
    # List of (specificity_tuple, declaration_name, value, is_important)
    matched_declarations = []

    for rule in rules:
        if isinstance(rule, tinycss2.ast.QualifiedRule):
            # A rule can have multiple comma-separated selectors (e.g. h1, .title)
            # Each selector has its own specificity.
            selector_prelude = "".join(
                [
                    t.serialize()
                    if hasattr(t, "serialize")
                    else str(t.value)
                    if hasattr(t, "value")
                    else str(t)
                    for t in rule.prelude
                ]
            ).strip()

            for selector_str in [s.strip() for s in selector_prelude.split(",")]:
                # CSS Pseudo-elements (::...) affect specificity как теги
                clean_selector = selector_str
                pseudo_target = "style"
                for p_name in SUPPORTED_PSEUDO_ELEMENTS:
                    p_str = f"::{p_name}"
                    if p_str in clean_selector:
                        pseudo_target = p_name
                        clean_selector = clean_selector.replace(p_str, "").strip()
                        break

                if _matches_selector(node, clean_selector, ancestors):
                    spec = _calculate_specificity(selector_str)

                    # Parse declarations in this rule
                    decls = tinycss2.parse_declaration_list(rule.content)
                    for decl in decls:
                        if isinstance(decl, tinycss2.ast.Declaration):
                            val_str, important = _serialize_declaration_value(decl)
                            matched_declarations.append(
                                {
                                    "spec": spec,
                                    "name": decl.name,
                                    "value": val_str,
                                    "important": important,
                                    "target": pseudo_target,
                                }
                            )
    # 2. Apply Normal Author declarations first
    # Sort by specificity so higher specificity overwrites lower
    normal_authors = [d for d in matched_declarations if not d["important"]]
    normal_authors.sort(key=lambda d: d["spec"])

    for d in normal_authors:
        target_dict = (
            node.style if d["target"] == "style" else node.pseudos.get(d["target"])
        )
        if d["target"] != "style" and target_dict is None:
            node.pseudos[d["target"]] = {}
            target_dict = node.pseudos[d["target"]]
        target_dict[d["name"]] = d["value"]

    # 3. Apply Inline Styles (Normal)
    inline_important_props = []
    inline_style_str = node.props.get("style")
    if inline_style_str:
        inline_decls = tinycss2.parse_declaration_list(
            inline_style_str, skip_comments=True, skip_whitespace=True
        )
        for decl in inline_decls:
            if isinstance(decl, tinycss2.ast.Declaration):
                val_str, important = _serialize_declaration_value(decl)
                if not important:
                    node.style[decl.name] = val_str
                else:
                    inline_important_props.append((decl.name, val_str))

    # 4. Apply Author !important declarations (These override normal inline)
    important_authors = [d for d in matched_declarations if d["important"]]
    important_authors.sort(key=lambda d: d["spec"])
    for d in important_authors:
        target_dict = (
            node.style if d["target"] == "style" else node.pseudos.get(d["target"])
        )
        if target_dict is not None:
            target_dict[d["name"]] = d["value"]

    # 5. Apply Inline !important (Wins everything)
    for name, val in inline_important_props:
        node.style[name] = val

    # 6. Recursively apply to children
    for child in node.children:
        apply_styles(child, rules)


def _serialize_declaration_value(
    declaration: tinycss2.ast.Declaration,
) -> Tuple[str, bool]:
    """Helper to extract value string and !important flag."""
    val = "".join(
        [
            t.serialize()
            if hasattr(t, "serialize")
            else str(t.value)
            if hasattr(t, "value")
            else str(t)
            for t in declaration.value
        ]
    ).strip()
    return val, declaration.important


def _calculate_specificity(selector: str) -> Tuple[int, int, int]:
    """
    Calculates (ids, classes/pseudos/attrs, tags/pseudo-elements)
    Following W3C Spec.
    """
    ids = selector.count("#")
    classes = selector.count(".")
    attrs = selector.count("[")
    # Count normal clones (:) and subtract pseudo-elements (::)
    pseudos = selector.count(":") - (selector.count("::") * 2)

    # Type Selectors (Tags)
    # Split by combinators and then inspect the start of each segment
    segments = selector.replace(">", " ").replace("+", " ").replace("~", " ").split()
    tags = selector.count("::")  # Pseudo-elements count as tags

    for seg in segments:
        if seg == "*":
            continue
        # A tag exists if the segment starts with an identifier
        # We check if it doesn't start with # . [ :
        if not seg.startswith(("#", ".", "[", ":")):
            tags += 1

    return (ids, classes + attrs + pseudos, tags)


def _matches_selector(node: Node, selector: str, ancestors: List[Node]) -> bool:
    """
    Supports: #id, .class, tag, descendant (a b), child (a > b),
              adjacent sibling (a + b), general sibling (a ~ b),
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

    # Handle Adjacent Sibling Combinator (a + b)
    if "+" in selector:
        parts = [p.strip() for p in selector.split("+")]
        target = parts[-1]
        prec_sel = "+".join(parts[:-1])
        if _matches_simple_selector(node, target):
            if node.parent:
                idx = node.parent.children.index(node)
                if idx > 0:
                    prev_sib = node.parent.children[idx - 1]
                    if _matches_single_selector(prev_sib, prec_sel, ancestors):
                        return True
        return False

    # Handle General Sibling Combinator (a ~ b)
    if "~" in selector:
        parts = [p.strip() for p in selector.split("~")]
        target = parts[-1]
        prec_sel = "~".join(parts[:-1])
        if _matches_simple_selector(node, target):
            if node.parent:
                idx = node.parent.children.index(node)
                # Check all preceding siblings
                for sib in node.parent.children[:idx]:
                    if _matches_single_selector(sib, prec_sel, ancestors):
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
