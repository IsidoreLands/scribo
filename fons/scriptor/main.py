import typer
from . import speculator, praetor # We only need to register the sub-applications

app = typer.Typer(
    name="scriptor",
    help="The canonized toolset for the AetherOS ecosystem."
)

app.add_typer(speculator.app, name="speculator")
app.add_typer(praetor.app, name="praetor")

if __name__ == "__main__":
    app()
