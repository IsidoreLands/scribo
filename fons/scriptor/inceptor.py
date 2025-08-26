import os
import sys
import venv
import subprocess
# This is now a library function, not a script with a main block
def create_initiative(initiative_path, user_name):
    try:
        venv_path = os.path.join(initiative_path, "venv")
        print(f"Inceptor: Initializing '{os.path.basename(initiative_path)}' for user '{user_name}'...")
        os.makedirs(venv_path, exist_ok=True)
        venv.create(venv_path, with_pip=True)
        with open(os.path.join(initiative_path, "README.md"), "w") as f:
            f.write(f"# Initiative: {os.path.basename(initiative_path)}\n\nOwner: {user_name}\n")
        subprocess.run(["git", "init"], cwd=initiative_path, capture_output=True)
        print("Inceptor: Project initialized.")
        return True
    except Exception as e:
        print(f"Inceptor: ERROR - Could not create initiative. Details: {e}")
        return False
