#!/bin/bash

# Store the base directory path
REPORTS_DIR="$(pwd)/reports"

# Remove existing 'last' whether it's a directory or symlink
if [ -d "$REPORTS_DIR/last" ]; then
    rm -rf "$REPORTS_DIR/last"
elif [ -L "$REPORTS_DIR/last" ]; then
    unlink "$REPORTS_DIR/last"
fi

# Navigate to the reports directory
cd "$REPORTS_DIR" || { echo "Error: Cannot access reports directory"; exit 1; }

# Get the latest folder sorted by modification time
latest=$(ls -t | head -n 1)

# Check if we have at least 1 directory
if [ -z "$latest" ]; then
    echo "Error: No directories found in reports/"
    exit 1
fi

# Create new symbolic link with absolute path
cd "$REPORTS_DIR" || exit 1
ln -s "$REPORTS_DIR/$latest" "$REPORTS_DIR/last" || { echo "Error: Could not create 'last' symlink"; exit 1; }

echo "Successfully created symlink:"
echo "last -> $latest"
