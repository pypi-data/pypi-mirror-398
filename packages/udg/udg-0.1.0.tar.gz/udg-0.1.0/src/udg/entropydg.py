"""
Entropy-DG method
"""

from typing import Any, SupportsInt

import numpy as np
from numpy.typing import NDArray

from udg.common import mul, rk4a, rk4b, rk4c, run_solver
from udg.quadratures import jac_nodal_basis_at, nodal_basis_at, zwglj


def main(_p: SupportsInt, _ne: SupportsInt) -> float:
    # number of coefficients inside each element
    p, ne = int(_p), int(_ne)
    K = p + 1

    # number of quadrature points inside each element
    Nq = K

    # define 1D mesh (We just need a sorted point distribution)
    xmesh = np.linspace(0, 1, ne + 1)

    # length of the domain
    _xlo, _xhi = np.min(xmesh), np.max(xmesh)

    # number of elements
    E = len(xmesh) - 1

    # left/right face maps
    mapL, mapR = np.arange(E + 1) * Nq - 1, np.arange(E + 1) * Nq
    mapL[0], mapR[-1] = 0, E * Nq - 1

    # size of each element
    h = np.diff(xmesh).reshape(-1, 1)
    assert np.min(h) > 1e-8, "Too small element size"

    # jacobian of the mapping from D^{st}=[-1,1] to D
    jac, invjac = h / 2, 2 / h

    # the quadrature (points, weights) on standard interval
    z, w = zwglj(Nq, 0.0, 0.0)

    # define the orthonormal basis
    B = nodal_basis_at(K, z, z)

    # define the mass matrix (see Karniadakis, page 122)
    # since the basis is orthonormal, this should be identity
    M = np.einsum("mq,q,lq->ml", B, w, B)
    invM = np.linalg.inv(M)

    # define the {K-1} order derivative matrix
    Dr = jac_nodal_basis_at(K, z, z)[0]

    # define the correction functions at the left and right boundaries
    gLD, gRD = invM[0, :], invM[-1, :]

    # advection velocity
    advx = 1

    # initial time, time step, final time
    ti, dt, tf = 0.0, 5e-4, 1
    nsteps = int(np.ceil((tf - ti) / dt))
    dt = (tf - ti) / nsteps

    # Compute the initial solution (ucoeff and usol are same)
    xsol = np.array([0.5 * (xmesh[j] + xmesh[j + 1]) + jac[j] * z for j in range(E)])
    usol = np.sin(2 * np.pi * (xsol - 0))

    # Actual algorithm
    time = ti

    uprev = np.zeros_like(usol)

    def entropy_flux(ul: NDArray[Any], ur: NDArray[Any]) -> NDArray[np.floating[Any]]:
        return np.asarray(0.5 * (ul + ur))

    for _step in range(nsteps):
        for istp in range(5):
            _tlocal = time + rk4c[istp] * dt
            # Step:1 extract the solution at interfaces
            uL = usol.reshape(-1, 1)[mapL]
            uR = usol.reshape(-1, 1)[mapR]

            # Insert the boundary condition information at left boundary
            uL[0], uR[-1] = uR[-1], uL[0]

            # Compute the upwind flux at interfaces
            fL, fR = advx * uL, advx * uR
            fupw = 0.5 * (fL + fR) + 0.5 * np.abs(advx) * (uL - uR)

            # Step:2 evaluate the derivative
            fx = np.zeros_like(usol)
            for j in range(Nq):
                fx[:, j] += (
                    2
                    * advx
                    * mul(
                        entropy_flux(usol[:, j].reshape(-1, 1), usol),
                        Dr[:, j].reshape(-1, 1),
                    )
                ).ravel()

            # Step:3 Compute the jumps
            jR = fupw - fL
            jL = fupw - fR

            # Compute the continuous flux for each element
            # See the strong form eq 2.6 in (Hasthaven 2008)
            for e in range(E):
                fx[e, :] += jR[e + 1] * gRD - jL[e] * gLD
            fx *= -invjac

            uprev = rk4a[istp] * uprev + dt * fx
            usol += rk4b[istp] * uprev

        # increment time
        time += dt

    # exact solution
    usol_e = np.sin(2 * np.pi * (xsol - tf))
    error = np.dot(mul(np.fabs(usol - usol_e), w), jac)
    return float(error[0])


def run() -> None:
    run_solver(main, "entropydg_adv.pdf")
