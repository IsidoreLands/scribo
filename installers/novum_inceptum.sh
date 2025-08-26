#!/bin/bash
# Novum Inceptum: New Initiative Launcher v3
INITIATIVE_NAME=$1
USER_NAME=${2:-scribo_user} # Default to 'scribo_user' if not provided
IMAGE_NAME="scriptorium:latest"

print_header() {
    echo "================================================================================"
    echo " $1"
    echo "================================================================================"
}
exit_on_error() {
    echo ""
    echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    echo " ERROR: $1"
    echo "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
    exit 1
}

if [ -z "$INITIATIVE_NAME" ]; then
    echo "Usage: ./installers/novum_inceptum.sh <initiative_name> [optional_user_name]"
    exit 1
fi

print_header "Building the Scriptorium Docker Image"
docker build -t "$IMAGE_NAME" . || exit_on_error "Docker image build failed."

INITIATIVE_PATH="$HOME/scribo_projects/$INITIATIVE_NAME"
mkdir -p "$INITIATIVE_PATH" || exit_on_error "Failed to create project directory on host."

print_header "Launching Sandboxed Docker Environment for '$INITIATIVE_NAME'"
echo "Your project at '$INITIATIVE_PATH' is mounted inside the container at '/project'."
echo "The Inceptor will now run INSIDE the container to initialize the environment."
echo "To exit the container, type 'exit'."
echo ""

docker run -it --rm \
  -v "$INITIATIVE_PATH:/project" \
  -w "/project" \
  -e "USER_NAME=${USER_NAME}" \ # Pass username as an environment variable
  "$IMAGE_NAME" \
  bash -c "scriptor init . ; exec bash" # Use our new unified command
