"""Main CLI entry point for aftr."""

import typer

from aftr.commands.init import init

app = typer.Typer(
    name="aftr",
    help="CLI for bootstrapping Python data projects with UV, mise, and papermill",
    no_args_is_help=True,
)

app.command()(init)


if __name__ == "__main__":
    app()
