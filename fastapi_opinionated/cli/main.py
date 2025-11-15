import typer
from fastapi_opinionated.cli.commands.new import new
from fastapi_opinionated.cli.commands.list import list_cli
from fastapi_opinionated.cli.commands.plugins import plugins_cli

app = typer.Typer(add_completion=False)
app.add_typer(new, name="new")
app.add_typer(list_cli, name="list")
app.add_typer(plugins_cli, name="plugins")
def main():
    app()
