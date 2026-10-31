#!/bin/sh
# Remove o programa e o atalho. Seus dados em ~/.local/share/NexStage são mantidos.
APPS="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
"$HOME/.local/opt/NexStage/NexStage" --stop >/dev/null 2>&1 || true
rm -rf "$HOME/.local/opt/NexStage" "$APPS/NexStage.desktop" "$HOME/.local/bin/nexstage"
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$APPS" >/dev/null 2>&1 || true
echo "NexStage removido. Os dados continuam em ${XDG_DATA_HOME:-$HOME/.local/share}/NexStage"
