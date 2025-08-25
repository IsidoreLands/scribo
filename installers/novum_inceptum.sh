#!/bin/bash
# Novum Inceptum: New Initiative Launcher v3
INITIATIVE_NAME=$1
USER_NAME=${2:-scribo_user} # Default to 'scribo_user' if not provided
IMAGE_NAME="scriptorium:latest"
# ... (helper functions remain the same) ...

# --- Main Logic ---
if [ -z "$INITIATIVE_NAME" ]; then
    echo "Usage: ./installers/novum_inceptum.sh <initiative_name> [optional_user_name]"
    exit 1
fi
# ... (rest of the script is the same until the docker run command) ...

# Launch the container, now passing the username to the Inceptor.
docker run -it --rm \
  -v "$HOME/scribo_projects/$INITIATIVE_NAME:/project" \
  -w "/project" \
  "$IMAGE_NAME" \
  bash -c "inceptor . $USER_NAME; exec bash"
