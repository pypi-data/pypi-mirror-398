from __future__ import annotations

import typer
from rich import print

from imageai.cli.detect import detect_app


app = typer.Typer(add_completion=False)
app.add_typer(detect_app)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Print installed package version and exit.",
    ),
) -> None:
    """
    imageai — explainable, physics-based image forensics.
    """

    if version:
        try:
            from importlib.metadata import version as _version
            print(_version("imageai"))
        except Exception:
            print("imageai (version unknown)")
        raise typer.Exit(code=0)

    if ctx.invoked_subcommand is None:
        print(ctx.get_help())
        raise typer.Exit(code=0)
