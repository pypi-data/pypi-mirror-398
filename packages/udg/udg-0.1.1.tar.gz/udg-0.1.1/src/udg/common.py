import itertools as it
from functools import reduce
from typing import Any, Protocol, SupportsInt

import matplotlib.pyplot as plt
import numpy as np
from mpltools import annotation
from numpy.typing import NDArray

rk4a = [
    0.0,
    -567301805773.0 / 1357537059087.0,
    -2404267990393.0 / 2016746695238.0,
    -3550918686646.0 / 2091501179385.0,
    -1275806237668.0 / 842570457699.0,
]

rk4b = [
    1432997174477.0 / 9575080441755.0,
    5161836677717.0 / 13612068292357.0,
    1720146321549.0 / 2090206949498.0,
    3134564353537.0 / 4481467310338.0,
    2277821191437.0 / 14882151754819.0,
]

rk4c = [
    0.0,
    1432997174477.0 / 9575080441755.0,
    2526269341429.0 / 6820363962896.0,
    2006345519317.0 / 3224310063776.0,
    2802321613138.0 / 2924317926251.0,
]

pa = {"fill": False, "edgecolor": "black"}
ta = {"fontsize": 10}


def mul(*args: NDArray[Any]) -> NDArray[Any]:
    return reduce(np.matmul, args)


def init() -> None:
    np.set_printoptions(suppress=True)


class SolverMain(Protocol):
    """Protocol for solver main functions."""

    def __call__(self, p: SupportsInt, ne: SupportsInt) -> float: ...


def run_solver(
    main_fn: SolverMain,
    output_file: str,
    p_start: int = 1,
    p_end: int = 4,
    n_power_start: int = 2,
    n_power_end: int = 7,
) -> None:
    """Run a convergence study for a DG solver and plot the results.

    Args:
        main_fn: The solver's main function that takes (p, ne) and returns error.
        output_file: Filename for the output PDF plot.
        p_start: Starting polynomial order (inclusive).
        p_end: Ending polynomial order (exclusive).
        n_power_start: Starting power of 2 for number of elements (inclusive).
        n_power_end: Ending power of 2 for number of elements (exclusive).
    """
    P = np.arange(p_start, p_end, 1)
    N = 2 ** np.arange(n_power_start, n_power_end)
    E = np.zeros((len(P), len(N)))

    for (i, p), (j, n) in it.product(enumerate(P), enumerate(N)):
        E[i, j] = main_fn(p, n)

    _fig = plt.figure()
    ax = plt.gca()
    colors = ["b", "g", "r", "c", "m", "y", "k", "w"]

    for j, p in enumerate(P):
        plt.loglog(1.0 / N, E[j, :], label=f"p={p}", color=colors[p])
        slope, _intercept = np.polyfit(np.log(1.0 / N[-3:]), np.log(E[j, -3:]), 1)
        annotation.slope_marker(
            (1.0 / N[-1], E[j, -1]),
            (f"{slope:.2f}", 1),
            ax=ax,
            poly_kwargs=pa,
            text_kwargs=ta,
        )

    plt.tight_layout()
    plt.autoscale()
    plt.legend(loc="lower right")
    plt.savefig(output_file)
