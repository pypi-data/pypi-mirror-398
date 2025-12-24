import typer

from adaptivegears import __version__
from adaptivegears.aws.cli import app as aws_app
from adaptivegears.pg.cli import app as pg_app
from adaptivegears.util.cli import _uuid7

app = typer.Typer(help="AdaptiveGears CLI tools")


def version_callback(value: bool):
    if value:
        print(f"adaptivegears {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", "-v", callback=version_callback, is_eager=True
    ),
):
    pass


@app.command()
def uuid(
    v7: bool = typer.Option(False, "-7", help="Generate UUID v7 (time-sortable)"),
    count: int = typer.Option(1, "-n", help="Number of UUIDs to generate"),
):
    """Generate UUIDs."""
    import uuid as uuid_lib

    for _ in range(count):
        if v7:
            print(_uuid7())
        else:
            print(uuid_lib.uuid4())


# Register subcommands
app.add_typer(aws_app, name="aws")
app.add_typer(pg_app, name="pg")
