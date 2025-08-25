import os
import patch

def perfice_resarcio(patch_path):
    """
    Applies a patch from a file. (Perfice Resarcio: "Complete the patch.")
    Returns the target file path on success, None on failure.
    """
    with open(patch_path, 'r') as f:
        patch_content = f.read()

    first_line = patch_content.split('\n', 1)[0]
    if not first_line.startswith('--- target: '):
        print(f"Error: Invalid patch file '{patch_path}'. Missing target header.")
        return None

    target_file = first_line.split('--- target: ')[1].strip()
    if not os.path.exists(target_file):
        print(f"Error: Target file '{target_file}' not found.")
        return None

    print(f"Perfector: Mending '{os.path.basename(target_file)}'...")
    patch_set = patch.fromstring(patch_content.encode('utf-8'))

    if patch_set.apply(root=os.path.dirname(target_file) or '.'):
        return target_file
    else:
        print(f"  -> Error: Could not apply patch.")
        return None
