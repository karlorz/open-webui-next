#!/bin/bash

# Define variables
SERVICE_FILE="open-webui.service"
SERVICE_PATH="/etc/systemd/system/"
DESTINATION_PATH="/opt/open-webui/"
APP_USERNAME="root"

# Create the destination directory if it doesn't exist
if [ ! -d "$DESTINATION_PATH" ]; then
  echo "Creating destination directory $DESTINATION_PATH"
  sudo mkdir -p "$DESTINATION_PATH"
else
  echo "Destination directory $DESTINATION_PATH already exists"
fi

# Stop the service if it's already running
echo "Stopping the service"
sudo systemctl stop "$SERVICE_FILE"

# Copy the service file to the systemd directory, force overwrite
echo "Copying service file to $SERVICE_PATH"
sudo cp -f "$SERVICE_FILE" "$SERVICE_PATH"

# Copy the current directory contents to the destination directory, force overwrite
echo "Copying current directory to $DESTINATION_PATH"
sudo cp -rf "$(pwd)/"* "$DESTINATION_PATH"

# Change the ownership of the destination directory
echo "Changing ownership of the destination directory"
sudo chown -R "$APP_USERNAME":"$APP_USERNAME" "$DESTINATION_PATH"

# Reload systemd to recognize the new service
echo "Reloading systemd daemon"
sudo systemctl daemon-reload

# Enable the service to start on boot
echo "Enabling the service"
sudo systemctl enable "$SERVICE_FILE"

# Start the service
echo "Starting the service"
sudo systemctl start "$SERVICE_FILE"

sleep 1

# Check the status of the service
echo "Checking the status of the service"
sudo systemctl status "$SERVICE_FILE"