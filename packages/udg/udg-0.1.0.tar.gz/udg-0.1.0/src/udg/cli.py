"""
CLI entry points for UDG solvers.
"""

import click

from udg import entropydg, nodaldg, semdg, upwinddg


@click.group()
def cli() -> None:
    """UDG - Upwind Discontinuous Galerkin Method solvers."""


@cli.command("sem-dg")
def sem_dg_command() -> None:
    """Run the DGSEM solver (Kopriva et al., 2009)."""
    semdg.run()


@cli.command("nodal-dg")
def nodal_dg_command() -> None:
    """Run the Nodal-DG solver (Hesthaven et al., 2008)."""
    nodaldg.run()


@cli.command("upwind-dg")
def upwind_dg_command() -> None:
    """Run the Upwind-DG solver."""
    upwinddg.run()


@cli.command("entropy-dg")
def entropy_dg_command() -> None:
    """Run the Entropy-DG solver (Gassner et al., 2011)."""
    entropydg.run()


if __name__ == "__main__":
    cli()
