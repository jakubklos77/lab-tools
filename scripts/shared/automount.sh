#!/usr/bin/env bash

set -euo pipefail

# Get currently connected Wi-Fi SSID
SSID=$(nmcli -t -f active,ssid dev wifi | awk -F: '$1=="yes"{print $2}')

case "$SSID" in
    ALDEBARAN|ALDEBARAN_GUEST|"")
        MOUNT=true
        ;;
esac

if [[ "${MOUNT:-}" == true ]]; then
    # Unmount if already mounted
    fusermount3 -u "$HOME/media" 2>/dev/null || true

    # Mount
    sshfs -o reconnect,ServerAliveInterval=15,ServerAliveCountMax=3,noatime $USER@192.168.0.5:/media "$HOME/media"
fi