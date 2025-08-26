import os
import patch
from .probator_tool import find_project_root # We can reuse this function

def perfice_resarcio(patch_path):
    with open(patch_path, 'r') as f:
        patch_content = f.read()

    first_line = patch_content.split('\n', 1)[0]
    if not first_line.startswith('--- target: '):
        return None
    target_file = first_line.split('--- target: ')[1].strip()
    if not os.path.exists(target_file):
        return None

    # --- NEW ROOT-FINDING LOGIC ---
    # We find the project root and tell the patch tool to work from there.
    project_root = find_project_root(os.path.dirname(target_file))
    if not project_root:
        # Fallback if we're not in a proper project
        project_root = os.path.dirname(target_file)
    # ----------------------------

    print(f"Perfector: Mending '{os.path.basename(target_file)}' (root: {project_root})")
    patch_set = patch.fromstring(patch_content.encode('utf-8'))
    
    # We no longer need 'strip'. We just provide the correct root.
    if patch_set.apply(root=project_root):
        return target_file
    else:
        print(f"  -> Error: Could not apply patch.")
        return None
