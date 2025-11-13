import typer
from fastapi_opinionated.cli.commands.new import new

app = typer.Typer(add_completion=False)
app.add_typer(new, name="new")


def main():
    app()
