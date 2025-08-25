# Scriptorium: The Docker Blueprint
# Defines a secure, isolated environment for running Scriptor and developing initiatives.

# Use an official Python base image.
FROM python:3.10-slim

# Set the working directory inside the container.
WORKDIR /scriptorium

# Copy the project definition and the source code.
COPY pyproject.toml .
COPY fons ./fons

# Install Scriptor and its dependencies within the container.
# Using 'pip install .' is the standard way to install from a pyproject.toml.
RUN pip install --no-cache-dir .

# Create a non-root user for added security.
RUN useradd --create-home scribo_user
USER scribo_user

# Set the project root for the new user.
WORKDIR /home/scribo_user/projects

# Default command when the container runs.
CMD [ "bash" ]
