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
        substitution_cost: float
        insertion_cost: float
        deletion_cost: float
        equality_bonus: float
        start_bonus: float
        end_bonus: float

    parser = argparse.ArgumentParser(
        prog="strox",
        description="Command line interface for the `strox` package",
        add_help=False,
    )
    parser.add_argument(
        "--substitution-cost",
        "-s",
        "--sub",
        type=float,
        default=Budget._field_defaults["substitution_cost"],
        help="Substitution cost",
        metavar="FLOAT",
    )
    parser.add_argument(
        "--insertion-cost",
        "-i",
        "--ins",
        type=float,
        default=Budget._field_defaults["insertion_cost"],
        help="Insertion cost",
        metavar="FLOAT",
    )
    parser.add_argument(
        "--deletion-cost",
        "-d",
        "--del",
        type=float,
        default=Budget._field_defaults["deletion_cost"],
        help="Deletion cost",
        metavar="FLOAT",
    )
    parser.add_argument(
        "--equality-bonus",
        "-e",
        "--eq",
        type=float,
        default=Budget._field_defaults["equality_bonus"],
        help="Equality bonus",
        metavar="FLOAT",
    )
    parser.add_argument(
        "--start-bonus",
        "--sb",
        type=float,
        default=Budget._field_defaults["start_bonus"],
        help="Start bonus",
        metavar="FLOAT",
    )
    parser.add_argument(
        "--end-bonus",
        "--eb",
        type=float,
        default=Budget._field_defaults["end_bonus"],
        help="End bonus",
        metavar="FLOAT",
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
        budget=Budget(
            substitution_cost=args.substitution_cost,
            insertion_cost=args.insertion_cost,
            deletion_cost=args.deletion_cost,
            equality_bonus=args.equality_bonus,
            start_bonus=args.start_bonus,
            end_bonus=args.end_bonus,
        ),
    )
    sys.stdout.write(result)

    return 0
