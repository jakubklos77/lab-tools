#!/bin/bash

REPO_DIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"

# .bashrc (append lab-tools shell config)
BASHRC_BLOCK=$(cat <<EOF

# Load lab-tools shell config
for f in "$REPO_DIR/shell/"*.sh; do
  [ -r "\$f" ] && source "\$f"
done
EOF
)

if ! grep -q "lab-tools shell config" "$HOME/.bashrc"; then
    echo "$BASHRC_BLOCK" >> "$HOME/.bashrc"
    echo "Appended lab-tools shell config block to ~/.bashrc"
else
    echo "~/.bashrc already contains lab-tools shell config block, skipping"
fi

# symlink ~/scripts/shared
mkdir -p "$HOME/scripts"
ln -sfn "$REPO_DIR/scripts/shared" "$HOME/scripts/shared" 2>/dev/null
echo "Created symlink ~/scripts/shared"

# symlinks in ~/bin for specific scripts
mkdir -p "$HOME/bin"
ln -sf "$REPO_DIR/scripts/shared/lgrep.sh" "$HOME/bin/lgrep"
ln -sf "$REPO_DIR/scripts/shared/run-in-terminal" "$HOME/bin/run-in-terminal"
ln -sf "$REPO_DIR/scripts/shared/exif_merge/main.sh" "$HOME/bin/exif_merge"
echo "Created ~/bin symlinks for scripts"

# symlinks in ~/bin
for f in "$REPO_DIR/bin/"*; do
    ln -sf "$f" "$HOME/bin/$(basename "$f")"
done
echo "Created ~/bin symlinks for bin/*"

# Copy repo .config to ~/.config (no overwrite)
cp --recursive --update=none "$REPO_DIR/.config/." "$HOME/.config/"
echo "Copied .config to ~/.config"

# install fabric
if [ -d "$HOME/app/fabric" ]; then
    echo "~/app/fabric already exists, skipping fabric install"
else
    mkdir -p "$HOME/app/fabric"

    # Symlink to config dir inside ~/app/fabric (config itself stays in ~/.config/fabric)
    ln -sf "$HOME/.config/fabric" "$HOME/app/fabric/config" 2>/dev/null
    echo "Created ~/app/fabric with config symlink to ~/.config/fabric"

    # Download and extract fabric binary
    FABRIC_URL="https://github.com/danielmiessler/Fabric/releases/latest/download/fabric_Linux_x86_64.tar.gz"
    echo "Downloading fabric..."
    curl -fsSL "$FABRIC_URL" | tar -xz -C "$HOME/app/fabric" fabric
    echo "Extracted fabric binary to ~/app/fabric"

    # Symlink fabric binary to ~/bin
    ln -sf "$HOME/app/fabric/fabric" "$HOME/bin/fabric"
    echo "Created ~/bin/fabric symlink"
fi