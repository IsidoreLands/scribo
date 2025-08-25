import os
import sys
import difflib
import argparse
from datetime import datetime

SCRIBO_INBOX = os.path.expanduser("~/scribo_inbox")

def main():
    parser = argparse.ArgumentParser(description="Comparator: Generate a Scriptor patch file.")
    parser.add_argument("original", help="The path to the original source file.")
    parser.add_argument("revised", help="The path to the file with changes.")
    args = parser.parse_args()

    for f in [args.original, args.revised]:
        if not os.path.exists(f):
            print(f"Error: Input file not found at '{f}'")
            sys.exit(1)
    
    os.makedirs(SCRIBO_INBOX, exist_ok=True)

    with open(args.original, 'r') as f_orig, open(args.revised, 'r') as f_rev:
        diff_content = "".join(list(difflib.unified_diff(
            f_orig.readlines(), f_rev.readlines(), fromfile=args.original, tofile=args.revised
        )))

    if not diff_content:
        print("Files are identical. No patch generated.")
        return

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    patch_filename = f"{timestamp}-{os.path.splitext(os.path.basename(args.original))[0]}.patch"
    patch_filepath = os.path.join(SCRIBO_INBOX, patch_filename)
    
    header = f"--- target: {os.path.abspath(args.original)}\n"
    with open(patch_filepath, 'w') as f:
        f.write(header + diff_content)

    print(f"Comparator: Successfully generated patch: {patch_filepath}")

if __name__ == "__main__":
    main()
