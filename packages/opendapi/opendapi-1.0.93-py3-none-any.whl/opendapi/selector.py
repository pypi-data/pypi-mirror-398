"""
Selectors with the following right-anchored grammar:

[exclude|!]? [prefix|regex|strict]? [name|path]? [file]? value

- A bare `value` is equivalent to 'strict:name:value'
- `file:value` loads a file and uses each non-empty, non-comment line as a selector
"""

import re
from enum import Enum
from typing import (
    Callable,
    List,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)


class RuleType(Enum):
    """Rule type"""

    PREFIX = "prefix"
    REGEX = "regex"
    STRICT = "strict"


class Kind(Enum):
    """Kind"""

    NAME = "name"
    PATH = "path"


# Types
Selector = str
Name = str
PathStr = str
NameAndPath = Tuple[Name, PathStr]
FileLoader = Callable[[str], str]  # repo-relative path -> UTF-8 file contents
CandidateType = Union[Name, NameAndPath]  # str (name) or (name, path)

# Grammar components
Value = str
IsFile = bool
IsExclude = bool


class SelectorParts(NamedTuple):
    """Parsed selector tokens (post-parse; pre-defaulting or post-defaulting)."""

    is_exclude: IsExclude
    typ: Optional[RuleType]  # None until defaulted to 'strict'
    kind: Optional[Kind]  # None until defaulted to 'name'
    value: Value
    is_file: IsFile

    def __str__(self) -> str:
        # Reconstruct a selector string losslessly.
        excl = "!" if self.is_exclude else ""
        tokens: List[str] = []
        if self.typ:
            tokens.append(self.typ.value)
        if self.kind:
            tokens.append(self.kind.value)
        if self.is_file:
            tokens.append("file")
        tokens.append(self.value)
        return excl + ":".join(tokens)


# ---------------- Parsing ---------------- #


def _parse_selector(selector: Selector) -> SelectorParts:
    """
    Parse selector per grammar:

    [exclude|!]? [prefix|regex|strict]? [name|path]? [file]? value
    """
    s = selector.strip()
    is_exclude = False

    if s.startswith("!"):
        is_exclude = True
        s = s[1:].lstrip()
    elif s.startswith("exclude:"):
        is_exclude = True
        s = s[len("exclude:") :].lstrip()
    if not s and is_exclude:
        raise ValueError(f"Selector 'exclude:' must have a value: {selector!r}")

    tokens = s.split(":")
    if not tokens or tokens[-1] == "":
        raise ValueError(f"Invalid selector (empty value): {selector!r}")

    value = tokens[-1]

    # file?
    is_file = False
    idx = -2
    if len(tokens) >= 2 and tokens[idx] == "file":
        is_file = True
        idx -= 1

    # kind?
    kind: Optional[Kind] = None
    if len(tokens) >= abs(idx) and tokens[idx] in ("name", "path"):
        kind = Kind(tokens[idx])  # type: ignore[assignment]
        idx -= 1

    # type?
    typ: Optional[RuleType] = None
    if len(tokens) >= abs(idx) and tokens[idx] in ("prefix", "regex", "strict"):
        typ = RuleType(tokens[idx])  # type: ignore[assignment]
        idx -= 1

    # Any remaining non-empty tokens are unexpected (rare, but guard it)
    if len(tokens) + idx >= 0 and (leftover := [t for t in tokens[: idx + 1] if t]):
        raise ValueError(f"Unexpected tokens {leftover!r} in selector {selector!r}")

    return SelectorParts(is_exclude, typ, kind, value, is_file)


# ------------- File expansion (recursive) ------------- #


def _expand_selectors(
    selectors: Sequence[Selector],
    file_loader: Optional[FileLoader],
    *,
    max_depth: int = 5,
) -> List[SelectorParts]:
    """
    Expand any ...:file:<path> selectors by loading newline-separated entries.
    Propagates exclude and inherits type/kind when a child line omits them.
    Returns a flat list of SelectorParts with is_file=False (file fully resolved).
    """
    if max_depth < 0:
        raise ValueError("Exceeded maximum selector include depth")

    out: List[SelectorParts] = []

    for raw in selectors:
        parts = _parse_selector(raw)

        # Non-file selector → keep as-is for now
        if not parts.is_file:
            out.append(parts)
            continue

        if file_loader is None:
            raise ValueError(f"Selector requires file loader: {raw!r}")

        text = file_loader(parts.value)
        # Currently supports txt files only
        lines = [
            stripped
            for ln in text.splitlines()
            if (stripped := ln.strip()) and not stripped.startswith("#")
        ]

        nested: List[Selector] = []
        for line in lines:
            child = _parse_selector(line)
            # Exclude propagation with XOR: exclude+exclude => include
            is_excl = parts.is_exclude ^ child.is_exclude
            # Inherit type/kind only if child omitted them
            eff_typ = child.typ or parts.typ
            eff_kind = child.kind or parts.kind
            # Build a concrete child selector (no file at this stage)
            nested.append(
                str(
                    SelectorParts(
                        is_excl, eff_typ, eff_kind, child.value, child.is_file
                    )
                )
            )

        out.extend(_expand_selectors(nested, file_loader, max_depth=max_depth - 1))

    # Apply defaults and clear is_file (we've expanded all files)
    defaulted: List[SelectorParts] = [
        SelectorParts(
            is_exclude=p.is_exclude,
            typ=(p.typ or RuleType.STRICT),
            kind=(p.kind or Kind.NAME),
            value=p.value,
            is_file=False,
        )
        for p in out
    ]
    return defaulted


# ---------------- Matching ---------------- #


def _match_value(typ: RuleType, hay: str, needle: str) -> bool:
    if typ is RuleType.STRICT:
        return hay == needle
    if typ is RuleType.PREFIX:
        return hay.startswith(needle)
    if typ is RuleType.REGEX:
        return re.search(needle, hay) is not None
    raise ValueError(f"Unknown match type: {typ}")


def _match_candidate(cand: CandidateType, terms: List[SelectorParts]) -> bool:
    name, path = (cand, None) if isinstance(cand, str) else cand
    for t in terms:
        target = name if t.kind is Kind.NAME else path
        if t.kind is Kind.PATH and path is None:
            continue
        if target is None:
            continue
        if _match_value(t.typ, target, t.value):
            return True
    return False


# ---------------- Public API ---------------- #


def filter_candidates_by_selectors(
    candidates: Sequence[CandidateType],
    selectors: Sequence[Selector],
    *,
    file_loader: Optional[FileLoader] = None,
    include_all_if_unspecified: bool = True,
) -> List[CandidateType]:
    """
    Filter candidates using the unified selector grammar.
    - Each candidate is either a name (str) or (name, path).
    - If no include terms are provided:
        - include all if include_all_if_unspecified=True (default)
        - else include none
    """
    expanded = _expand_selectors(selectors, file_loader=file_loader)

    include_terms: List[SelectorParts] = []
    exclude_terms: List[SelectorParts] = []
    for p in expanded:
        (exclude_terms if p.is_exclude else include_terms).append(p)

    included_idx: Set[int] = set()
    if include_terms:
        for i, cand in enumerate(candidates):
            if _match_candidate(cand, include_terms):
                included_idx.add(i)
    elif include_all_if_unspecified:
        included_idx = set(range(len(candidates)))

    excluded_idx: Set[int] = set()
    if exclude_terms and included_idx:
        for i in list(included_idx):
            if _match_candidate(candidates[i], exclude_terms):
                excluded_idx.add(i)

    return [
        candidates[i]
        for i in range(len(candidates))
        if i in included_idx and i not in excluded_idx
    ]
