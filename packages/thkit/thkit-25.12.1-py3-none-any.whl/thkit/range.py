from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from collections.abc import Generator


#####ANCHOR composite range parser
def range_inclusive(start: float, end: float, step: float, tol: float = 1e-6) -> list[float]:
    """Generate evenly spaced points including the endpoint (within tolerance)."""
    assert step > 0, "step must be positive"
    assert end >= start, "end must be >= start"

    n_steps = int(np.floor((end - start) / step)) + 1
    p = start + step * np.arange(n_steps)
    ### Add endpoint if missing
    if abs(p[-1] - end) > tol:
        p = np.concatenate([p, [end]])
    return p.tolist()


def composite_range(list_inputs: list[float | str], tol=1e-6) -> list[float]:
    """A custom parser to allow define composite ranges. This is needed for defining input parameters in YAML files.

    Args:
        list_inputs (list[int | float | str]): Accepts numbers or strings with special form 'start:end[:step]' (inclusive).
        tol (float): Tolerance for including the endpoint.

    Examples: ["-3.1:-1", 0.1, 2, "3.1:5.2", "6.0:10.1:0.5"]
    """
    arr = []
    for item in list_inputs:
        if isinstance(item, (int, float)):
            arr.append(item)
        elif isinstance(item, str):
            assert ":" in item, "'Range string' must in form 'start:end[:step]'"
            parts = item.split(":")
            if len(parts) == 3:
                start, end, step = map(float, parts)
            elif len(parts) == 2:
                start, end = map(float, parts)
                step = 1
            else:
                raise ValueError(f"Invalid range string: {item}, must in form 'start:end[:step]'")
            arr.extend(range_inclusive(start, end, step, tol))
    return arr


def composite_index(list_inputs: list[float | str]) -> list[int]:
    """Allow define composite index ranges.

    Args:
        list_inputs (list[int | str]): Accepts ints or strings with special form 'start:end[:step]' (inclusive).

    Examples: [1, 2, "3:5", "7:10:2"] -> [1, 2, 3, 4, 5, 7, 9, 10]
    """
    idx = composite_range(list_inputs, tol=0.9)
    idx = [int(i) for i in idx]
    return idx


def composite_strain_points(list_inputs: list[int | float | str], tol=1e-6) -> list[float]:
    """Generate composite spacing points from multiple ranges with tolerance-based uniqueness.

    Notes:
        - `np.round(np.array(all_points) / tol).astype(int)` is a trick to avoid floating point issues
          when comparing points with a certain tolerance.
    """
    all_points = composite_range(list_inputs, tol)
    ### Bucketize by tolerance instead of decimals
    scaled_p = np.round(np.array(all_points) / tol).astype(int)
    unique_p = np.unique(scaled_p) * tol
    unique_p = unique_p[unique_p != 0.0]  # Exclude zero if present

    ### Round to tolerance precision (avoids 0.89999999)
    decimals = max(0, int(-np.log10(tol)))
    unique_p = np.round(unique_p, decimals)
    return unique_p.tolist()


#####ANCHOR List
def chunk_list(input_list: list, chunk_size: int) -> Generator:
    """Yield successive n-sized chunks from `input_list`.

    Args:
        input_list (list): Input list to be chunked.
        chunk_size (int): Chunk size (number of elements per chunk).
    """
    for i in range(0, len(input_list), chunk_size):
        yield input_list[i : i + chunk_size]
