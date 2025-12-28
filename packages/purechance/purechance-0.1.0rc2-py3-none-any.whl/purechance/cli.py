import typer
from rich.console import Console

import purechance

console = Console()
app = typer.Typer(add_completion=False)

ITEMS_ARG = typer.Argument(..., help="Input items.")

SEED_OPT = typer.Option(None, help="Seed for the random number generator.")


@app.callback(invoke_without_command=True)
def version(
    show: bool = typer.Option(
        False, "--version", "-v", help="Show app version and exit."
    ),
) -> None:
    if show:
        typer.echo(f"{purechance.__name__} {purechance.__version__}")
        raise typer.Exit()


@app.command()
def integers(
    size: int = typer.Argument(1, help="Number of random integers to sample."),
    lower: int = typer.Option(0, help="Lower bound (inclusive)."),
    upper: int = typer.Option(
        purechance.signed_max(32), help="Upper bound (exclusive)."
    ),
    seed: int | None = SEED_OPT,
) -> None:
    """Show uniformly sampled random integers."""
    rng = purechance.get_rng(seed)
    values = list(purechance.integers(size, lower, upper, rng))
    console.print(values)


@app.command()
def pick(
    items: list[str] = ITEMS_ARG,
    replace: bool = typer.Option(True, help="Sample with replacement."),
    size: int = typer.Option(1, help="Number of items to pick."),
    seed: int | None = SEED_OPT,
) -> None:
    """Show randomly picked items from the provided list."""
    rng = purechance.get_rng(seed)
    picked = purechance.draw(items, replace, size, rng)
    console.print(picked)


@app.command()
def shuffle(items: list[str] = ITEMS_ARG, seed: int | None = SEED_OPT) -> None:
    """Show a randomly shuffled list of the provided items."""
    rng = purechance.get_rng(seed)
    shuffled = purechance.shuffle(items, rng)
    console.print(shuffled)


def main() -> None:
    """Canonical entry point for CLI execution."""
    app()
