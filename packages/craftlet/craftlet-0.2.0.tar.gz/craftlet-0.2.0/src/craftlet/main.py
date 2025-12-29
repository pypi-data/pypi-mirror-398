import typer

from craftlet.cli.CraftLetCLI import CraftLetCLI

app = typer.Typer(name="CraftLet", help="Entry Point of CraftLet CLI tool")
CraftLetCLI.registerTo(app=app)
