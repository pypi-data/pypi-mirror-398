"""
CLI entry point for kubesealpy.

This module provides command-line interface for sealing and unsealing
Kubernetes secrets.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import NoReturn

try:
    import typer
    from rich.console import Console

    _HAS_TYPER = True
except ImportError:
    _HAS_TYPER = False


def _fallback_app() -> NoReturn:
    """Fallback when typer is not installed."""
    print("CLI requires typer. Install with: pip install kubesealpy[cli]")
    sys.exit(1)


if _HAS_TYPER:
    import typer
    from rich.console import Console

    app = typer.Typer(
        name="kubesealpy",
        help="Seal and unseal Kubernetes secrets compatible with Bitnami's kubeseal.",
        add_completion=False,
    )
    console = Console()

    @app.command()
    def seal(
        cert: str = typer.Option(
            ...,
            "--cert",
            "-c",
            help="Path to the sealing certificate (PEM format)",
        ),
        name: str = typer.Option(
            ...,
            "--name",
            "-n",
            help="Name of the secret",
        ),
        namespace: str = typer.Option(
            "default",
            "--namespace",
            "-N",
            help="Kubernetes namespace",
        ),
        scope: str = typer.Option(
            "strict",
            "--scope",
            "-s",
            help="Sealing scope: strict, namespace-wide, or cluster-wide",
        ),
    ) -> None:
        """Seal a Kubernetes secret."""
        console.print("[yellow]CLI seal command - not yet implemented[/yellow]")
        console.print(f"Would seal secret '{name}' in namespace '{namespace}'")
        console.print(f"Using certificate: {cert}")
        console.print(f"Scope: {scope}")

    @app.command()
    def unseal(
        key: str = typer.Option(
            ...,
            "--key",
            "-k",
            help="Path to the private key (PEM format)",
        ),
    ) -> None:
        """Unseal a Kubernetes sealed secret."""
        console.print("[yellow]CLI unseal command - not yet implemented[/yellow]")
        console.print(f"Would unseal using key: {key}")

    @app.command()
    def version() -> None:
        """Show the version."""
        from kubesealpy import __version__

        console.print(f"kubesealpy version {__version__}")

else:
    app = _fallback_app  # type: ignore[assignment]


if __name__ == "__main__":
    app()
