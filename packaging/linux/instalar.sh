#!/bin/sh
# Instala o NexStage na sua conta (não precisa de sudo): copia o programa para
# ~/.local/opt/NexStage e cria o atalho no menu de aplicativos.
# Suas músicas, Bíblias, fontes e configurações ficam em ~/.local/share/NexStage
# e não são tocadas ao instalar de novo por cima.
set -e
cd "$(dirname "$0")"
DEST="$HOME/.local/opt/NexStage"
APPS="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
BIN="$HOME/.local/bin"

mkdir -p "$DEST" "$APPS" "$BIN"
# remove a versão antiga do programa (os dados ficam em outra pasta)
find "$DEST" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
cp -R ./. "$DEST/"
chmod +x "$DEST/NexStage"

cat > "$APPS/NexStage.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=NexStage
Comment=Apresentador de letras, Bíblia e vídeos para igrejas
Exec=$DEST/NexStage
Icon=$DEST/NexStage.png
Terminal=false
Categories=AudioVideo;Presentation;
StartupNotify=false
DESKTOP

ln -sf "$DEST/NexStage" "$BIN/nexstage"
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database "$APPS" >/dev/null 2>&1 || true

echo "NexStage instalado em $DEST"
echo "Abra pelo menu de aplicativos (NexStage) ou rode: nexstage"
echo "Para encerrar: clique em 'Encerrar NexStage' no ícone da bandeja ou rode: nexstage --stop"
echo "(se 'nexstage' não for encontrado, inclua $BIN no PATH)"
