from __future__ import annotations

from typing import Any, Hashable, Tuple, Dict


def make_key(args: Tuple[Any, ...], kwargs: Dict[str, Any], typed: bool) -> Hashable:
    """
    Deterministic, hashable key.
    :param kwargs: order doesn't matter
    :param typed:True distinguishes 1 from 1.0, etc.
    """

    if kwargs:
        items = tuple(sorted(kwargs.items()))
    else:
        items = ()
    if not typed:
        return args, items

    args_t = tuple((type(v), v) for v in args)
    items_t = tuple((k, type(v), v) for (k, v) in items)
    return args_t, items_t