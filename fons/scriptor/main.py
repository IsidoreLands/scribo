python
import typer
from . import praetor, inceptor # Assuming we will make inceptor a command too

app = typer.Typer(
    name="scriptor",
    help="The canonized toolset for the AetherOS ecosystem."
)

# Add the top-level commands to the main application
app.add_typer(praetor.app, name="praetor")

# We can also add standalone commands
@app.command()
def init(name: str):
    """
    Initializes a new project initiative. A wrapper around the inceptor.
    """
    inceptor.create_initiative(f"./{name}", "scribo_user") # Simplified for now

if __name__ == "__main__":
    app()
