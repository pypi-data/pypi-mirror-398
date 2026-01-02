"""
Strox
=====

Find strings that matches approximately the given pattern

Includes:
- `get_similarity_score`
- `get_closest_match`
- `get_close_matches`
- `Budget`
"""

from __future__ import annotations as _annotations

__all__ = [
    "get_similarity_score",
    "get_closest_match",
    "get_close_matches",
    "Budget",
]

import difflib as _difflib
from functools import partial as _partial
from collections.abc import Iterable as _Iterable
from importlib.metadata import version
from typing import NamedTuple as _NamedTuple


class Budget(_NamedTuple):
    substitution_cost: float = 1.0
    insertion_cost: float = 0.5
    deletion_cost: float = 0.5
    equality_bonus: float = 0.0
    start_bonus: float = 0.0
    end_bonus: float = 0.0


def get_similarity_score(  # NOTE: Higher score is more similar
    string1: str,
    string2: str,
    /,
    *,
    budget: Budget | None = None,
) -> float:
    if budget is None:
        budget = Budget()
    score = 0
    matcher = _difflib.SequenceMatcher(None, string1, string2)
    for char_a, char_b in zip(string1, string2):
        if char_a == char_b:
            score += budget.start_bonus
        else:
            break
    for char_a, char_b in zip(reversed(string1), reversed(string2)):
        if char_a == char_b:
            score += budget.end_bonus
        else:
            break
    for tag, start, end, _start2, _end2 in matcher.get_opcodes():
        work = end - start
        if tag == "equal":
            score += budget.equality_bonus * work
        elif tag == "replace":
            work = 2
            score -= budget.substitution_cost * work
        elif tag == "delete":
            score -= budget.deletion_cost * work
        elif tag == "insert":
            score -= budget.insertion_cost * work
    return score


def get_closest_match(
    string: str,
    options: _Iterable[str],
    /,
    *,
    budget: Budget | None = None,
) -> str:
    if budget is None:
        budget = Budget()
    if not options:
        raise ValueError(
            f"Expected parameter 'options' to be a populated sequence, got: {options}"
        )
    compare = _partial(get_similarity_score, string, budget=budget)
    best_match = max(options, key=compare)
    return best_match


def get_close_matches(
    string: str,
    options: _Iterable[str],
    /,
    *,
    max_results: int | None = None,
    budget: Budget | None = None,
) -> list[str]:
    if budget is None:
        budget = Budget()
    if not options:
        raise ValueError(
            f"Expected parameter 'options' has to be a populated sequence, got: {options}"
        )
    compare = _partial(get_similarity_score, string, budget=budget)
    matches = sorted(options, key=compare, reverse=True)
    if max_results is None:
        return matches
    return matches[:max_results]


def main() -> int:
    import argparse
    import sys

    class ParserArguments(argparse.Namespace):
        query: str
        options: list[str]

    parser = argparse.ArgumentParser(
        prog="strox",
        description="Command line interface for the `strox` package",
        add_help=False,
    )
    parser.add_argument(
        "-h",
        "--help",
        action="help",
        help="Show this help message and exit",
        default=argparse.SUPPRESS,
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s: v{version('strox')}",
        help="Show `%(prog)s` version number and exit",
    )
    parser.add_argument(
        "query",
        help="Query to match against",
    )
    parser.add_argument(
        "options",
        nargs="+",
        help="Options to select from",
    )

    args = ParserArguments()
    parser.parse_args(namespace=args)

    result = get_closest_match(
        args.query,
        args.options,
    )
    sys.stdout.write(result)

    return 0
