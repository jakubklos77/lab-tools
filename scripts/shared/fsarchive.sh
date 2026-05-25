#!/home/jakub/bin/run-in-terminal
#!/bin/bash

# Settings
DAYS=30
MOUNT_DIR=~/tmp
BACKUP_DIR=$MOUNT_DIR/Image
SSHFS="jakub@myklos.org:/media"
DEVICE=""
EXCLUDE=--exclude="/home/$USER/Android/android-sdk-linux/system-images"

set -e

# Ensure the script is running as root
if [ "$EUID" -ne 0 ]; then
  echo "Running as sudo..."
  exec sudo "$0" "$@"  # Re-run the script with sudo
fi

# Mount the remote filesystem
sshfs $SSHFS $MOUNT_DIR

# Clean up function
cleanup() {

  # Unmount the remote filesystem
  fusermount -u $MOUNT_DIR
}
trap cleanup EXIT SIGTERM

# Variables
# if $DEVICE is empty, use the first disk
if [ -z "$DEVICE" ]; then
  DEVICE=$(fdisk -l | grep -oP "/dev/[a-z0-9]+ " | head -n 1)
fi
HOSTNAME=$(hostname) # hostname
NOW=$(date +"%Y-%m-%d")
BACKUP=$BACKUP_DIR/$HOSTNAME
IMAGE=$BACKUP/$HOSTNAME-$NOW.fsa

# Print settings and wait
echo "Image: $IMAGE"
echo "Device: $DEVICE"
read -n 1 -p "Press any key to continue"

# Delete old backups
find $BACKUP -type f -mtime +$DAYS -delete

# Archive
fsarchiver savefs $EXCLUDE -v -A $IMAGE $DEVICE
