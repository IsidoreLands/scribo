import typer
# Import all our command modules
from . import speculator, praetor, comparator, inceptor

app = typer.Typer(
    name="scriptor",
    help="The canonized toolset for the AetherOS ecosystem."
)

# Register all the command modules as sub-applications
app.add_typer(speculator.app, name="speculator")
app.add_typer(praetor.app, name="praetor")
app.add_typer(comparator.app, name="compara")
app.add_typer(inceptor.app, name="inceptor")

if __name__ == "__main__":
    app()
