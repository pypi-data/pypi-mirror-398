"""
Integration tests for DG solver main() functions.

These tests verify that each solver produces the expected error
for a fixed polynomial order (p) and number of elements (ne).
The expected errors are computed from reference runs.
"""

import pytest

from udg import entropydg, nodaldg, semdg, upwinddg

# Fixed test parameters
P = 2  # polynomial order
NE = 8  # number of elements

# Expected errors (computed from reference runs with p=2, ne=8)
# These are regression values - if the algorithm changes, update these
EXPECTED_ERRORS = {
    "semdg": 0.0060251910474230464,
    "nodaldg": 0.0017987486331684567,
    "upwinddg": 0.025562225115547704,
    "entropydg": 0.006025191047422863,
}

# Tolerance for floating-point comparison
RTOL = 1e-10


class TestSolverIntegration:
    """Integration tests for solver main() functions."""

    def test_semdg_error(self):
        """Test DGSEM solver produces expected error."""
        error = semdg.main(P, NE)
        assert error == pytest.approx(EXPECTED_ERRORS["semdg"], rel=RTOL)

    def test_nodaldg_error(self):
        """Test Nodal-DG solver produces expected error."""
        error = nodaldg.main(P, NE)
        assert error == pytest.approx(EXPECTED_ERRORS["nodaldg"], rel=RTOL)

    def test_upwinddg_error(self):
        """Test Upwind-DG solver produces expected error."""
        error = upwinddg.main(P, NE)
        assert error == pytest.approx(EXPECTED_ERRORS["upwinddg"], rel=RTOL)

    def test_entropydg_error(self):
        """Test Entropy-DG solver produces expected error."""
        error = entropydg.main(P, NE)
        assert error == pytest.approx(EXPECTED_ERRORS["entropydg"], rel=RTOL)


class TestSolverConvergence:
    """Test that solvers exhibit expected convergence behavior."""

    @pytest.mark.parametrize(
        "solver_main", [semdg.main, nodaldg.main, upwinddg.main, entropydg.main]
    )
    def test_error_decreases_with_refinement(self, solver_main):
        """Verify error decreases when mesh is refined (h-refinement)."""
        error_coarse = solver_main(P, 4)
        error_fine = solver_main(P, 8)
        assert error_fine < error_coarse, "Error should decrease with mesh refinement"

    @pytest.mark.parametrize(
        "solver_main", [semdg.main, nodaldg.main, upwinddg.main, entropydg.main]
    )
    def test_error_decreases_with_higher_order(self, solver_main):
        """Verify error decreases with higher polynomial order (p-refinement)."""
        error_low_order = solver_main(1, NE)
        error_high_order = solver_main(3, NE)
        assert error_high_order < error_low_order, (
            "Error should decrease with higher polynomial order"
        )
