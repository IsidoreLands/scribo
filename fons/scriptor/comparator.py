import os
import sys
import difflib
import argparse
from datetime import datetime

SCRIBO_INBOX = os.path.expanduser("~/scribo_inbox")

def generate_patch_file(original_file_path, revised_file_path):
    """
    Compares two files and generates a self-contained Scriptor patch file
    in the central inbox.

    Returns the path to the generated patch file, or None if files are identical.
    """
    for f in [original_file_path, revised_file_path]:
        if not os.path.exists(f):
            # Using a print here as this is a library function, logging is for the daemon
            print(f"Error: Input file not found at '{f}'")
            return None
    
    os.makedirs(SCRIBO_INBOX, exist_ok=True)

    with open(original_file_path, 'r') as f_orig, open(revised_file_path, 'r') as f_rev:
        diff_content = "".join(list(difflib.unified_diff(
            f_orig.readlines(), f_rev.readlines(),
            fromfile=original_file_path, tofile=revised_file_path
        )))

    if not diff_content:
        return None # Files are identical

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    patch_filename = f"{timestamp}-{os.path.splitext(os.path.basename(original_file_path))[0]}.patch"
    patch_filepath = os.path.join(SCRIBO_INBOX, patch_filename)
    
    # The header must contain the absolute path for the daemon to find it
    header = f"--- target: {os.path.abspath(original_file_path)}\n"
    with open(patch_filepath, 'w') as f:
        f.write(header + diff_content)

    return patch_filepath

def main():
    """The command-line interface for the Comparator tool."""
    parser = argparse.ArgumentParser(description="Comparator: Generate a Scriptor patch file.")
    parser.add_argument("original", help="The path to the original source file.")
    parser.add_argument("revised", help="The path to the file containing the desired changes.")
    args = parser.parse_args()

    patch_file = generate_patch_file(args.original, args.revised)

    if patch_file:
        print(f"Comparator: Successfully generated patch: {patch_file}")
    else:
        print("Files are identical. No patch generated.")

if __name__ == "__main__":
    main()
