import os
import sys
import difflib
import argparse
from datetime import datetime
# We now need the find_project_root function here as well
from .probator_tool import find_project_root

SCRIBO_INBOX = os.path.expanduser("~/scribo_inbox")

def generate_patch_file(original_file_path, revised_file_path):
    """
    Compares two files and generates a clean, relative, self-contained
    Scriptor patch file in the central inbox.
    """
    os.makedirs(SCRIBO_INBOX, exist_ok=True)

    with open(original_file_path, 'r') as f_orig, open(revised_file_path, 'r') as f_rev:
        original_lines = f_orig.readlines()
        revised_lines = f_rev.readlines()

    if original_lines == revised_lines:
        return None

    # --- NEW GIT-STYLE RELATIVE PATH LOGIC ---
    # Find the project root of the ORIGINAL file. This is our anchor.
    project_root = find_project_root(os.path.dirname(original_file_path))
    if not project_root:
        # If not in a project, fall back to the file's own directory
        project_root = os.path.dirname(original_file_path)

    # Calculate the simple, relative path from that root.
    relative_path = os.path.relpath(original_file_path, project_root)
    
    # Use this SAME relative path for both fromfile and tofile.
    # This creates a clean patch that the patch tool can understand.
    diff_content = "".join(list(difflib.unified_diff(
        original_lines, revised_lines,
        fromfile=f"a/{relative_path}", tofile=f"b/{relative_path}"
    )))
    # ----------------------------------------

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    patch_filename = f"{timestamp}-{os.path.splitext(os.path.basename(original_file_path))[0]}.patch"
    patch_filepath = os.path.join(SCRIBO_INBOX, patch_filename)
    
    header = f"--- target: {os.path.abspath(original_file_path)}\n"
    with open(patch_filepath, 'w') as f:
        f.write(header + diff_content)

    return patch_filepath

def main():
    parser = argparse.ArgumentParser(description="Comparator: Generate a Scriptor patch file.")
    parser.add_argument("original", help="The path to the original source file.")
    parser.add_argument("revised", help="The path to the file with changes.")
    args = parser.parse_args()
    patch_file = generate_patch_file(args.original, args.revised)
    if patch_file:
        print(f"Comparator: Successfully generated patch: {patch_file}")
    else:
        print("Files are identical. No patch generated.")

if __name__ == "__main__":
    main()
