import typer
import os
import sys
import difflib
from datetime import datetime
from .probator_tool import find_project_root

app = typer.Typer(name="compara", help="Generates a Scriptor patch file by comparing two files.")

# (The generate_patch_file function is unchanged)
def generate_patch_file(original_file_path, revised_file_path):
    # ... (all the logic from the last correct version of this function)
    SCRIBO_INBOX = os.path.expanduser("~/scribo_inbox")
    os.makedirs(SCRIBO_INBOX, exist_ok=True)
    with open(original_file_path, 'r') as f_orig, open(revised_file_path, 'r') as f_rev:
        original_lines = f_orig.readlines()
        revised_lines = f_rev.readlines()
    if original_lines == revised_lines:
        return None
    project_root = find_project_root(os.path.dirname(original_file_path))
    if not project_root:
        project_root = os.path.dirname(original_file_path)
    relative_path = os.path.relpath(original_file_path, project_root)
    diff_content = "".join(list(difflib.unified_diff(
        original_lines, revised_lines,
        fromfile=f"a/{relative_path}", tofile=f"b/{relative_path}"
    )))
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    patch_filename = f"{timestamp}-{os.path.splitext(os.path.basename(original_file_path))[0]}.patch"
    patch_filepath = os.path.join(SCRIBO_INBOX, patch_filename)
    header = f"--- target: {os.path.abspath(original_file_path)}\n"
    with open(patch_filepath, 'w') as f:
        f.write(header + diff_content)
    return patch_filepath

@app.callback(invoke_without_command=True)
def main(
    original: str = typer.Argument(..., help="The path to the original source file."),
    revised: str = typer.Argument(..., help="The path to the file with changes.")
):
    """
    Compares an original and revised file and generates a patch.
    """
    patch_file = generate_patch_file(original, revised)
    if patch_file:
        print(f"Comparator: Successfully generated patch: {patch_file}")
    else:
        print("Files are identical. No patch generated.")
