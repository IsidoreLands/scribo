import typer
# --- NEW: Import all our command modules ---
from . import praetor, inceptor, speculator, comparator

# The main Typer application. This is the 'scriptor' command.
app = typer.Typer(
    name="scriptor",
    help="The canonized toolset for the AetherOS ecosystem."
)

# --- NEW: Register all the command modules ---
app.add_typer(praetor.app, name="praetor")
app.add_typer(speculator.app, name="speculator")
# We can also add individual commands directly
# Note: We are making compara and inceptor top-level for ease of use.
app.command("compara")(comparator.main)
app.command("inceptor")(inceptor.main)

if __name__ == "__main__":
    app()
