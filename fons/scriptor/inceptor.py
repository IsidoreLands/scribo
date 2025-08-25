# inceptor.py
# A tool to create and initialize a new project initiative with a dedicated venv.
import os
import sys
import venv

# The root directory where all projects will be stored.
PROJECTS_ROOT = os.path.expanduser("~/scribo_projects")

def create_initiative(initiative_path): # Take the full path as an argument
    """
    Creates a Python virtual environment within a given project directory.
    """
    try:
        venv_path = os.path.join(initiative_path, "venv")
        print(f"Inceptor: Initializing project structure in '{initiative_path}'...")
        os.makedirs(venv_path, exist_ok=True)
        venv.create(venv_path, with_pip=True)
        print(f"Inceptor: Successfully created venv at '{venv_path}'.")
        print("Inceptor: Project initialized.")
        return True

    except Exception as e:
        print(f"Inceptor: ERROR - Could not create initiative. Details: {e}")
        return False

def main():
    if len(sys.argv) != 2:
        # The argument will be the mount point inside the container, e.g., "."
        print("Usage: inceptor <path_to_initiative>")
        sys.exit(1)
    initiative_path = sys.argv[1]
    create_initiative(initiative_path)

if __name__ == "__main__":
    main()

