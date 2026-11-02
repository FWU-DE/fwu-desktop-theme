#!/bin/sh
# FWU-Theme installieren – ohne Paketmanager und ohne Abhängigkeiten.
#
#   ./install.sh                 als Benutzer: nach ~/.local, kein root nötig
#   sudo ./install.sh            systemweit: nach /usr/local
#   ./install.sh --omarchy       zusätzlich die Omarchy-Themes verlinken
#   ./install.sh --uninstall     wieder entfernen (gleiche Rechte wie beim Installieren)
#
# Für Paketbauten: --prefix /usr --destdir DIR (schreibt nach DIR/usr/…).

set -eu
cd "$(dirname "$0")"

prefix= destdir= omarchy= uninstall=
while [ $# -gt 0 ]; do
  case $1 in
    --prefix) prefix=$2; shift ;;
    --destdir) destdir=$2; shift ;;
    --omarchy) omarchy=1 ;;
    --uninstall) uninstall=1 ;;
    -h|--help) sed -n '2,10s/^# \{0,1\}//p' "$0"; exit 0 ;;
    *) echo "unbekannte Option: $1" >&2; exit 2 ;;
  esac
  shift
done

if [ -z "$prefix" ]; then
  if [ "$(id -u)" -eq 0 ]; then prefix=/usr/local; else prefix=$HOME/.local; fi
fi
user=
case $prefix in "$HOME"/*) user=1 ;; esac

share=$prefix/share
data=$share/fwu-desktop-theme
if [ -n "$user" ]; then
  autostart=${XDG_CONFIG_HOME:-$HOME/.config}/autostart
else
  autostart=/etc/xdg/autostart
fi

files="$prefix/bin/fwu-theme $data $share/themes/FWU $share/themes/FWU-Dark
$share/gnome-background-properties/fwu.xml $autostart/fwu-theme-watch.desktop
$share/doc/fwu-desktop-theme"

if [ -n "$uninstall" ]; then
  [ -x "$prefix/bin/fwu-theme" ] && [ -z "$destdir" ] && "$prefix/bin/fwu-theme" reset >/dev/null 2>&1 || true
  for f in $files; do rm -rf "$destdir$f"; done
  echo "FWU-Theme aus $prefix entfernt."
  exit 0
fi

D=$destdir
mkdir -p "$D$prefix/bin" "$D$data" "$D$share/themes" "$D$share/gnome-background-properties" \
  "$D$autostart" "$D$share/doc/fwu-desktop-theme"

install -m 755 bin/fwu-theme "$D$prefix/bin/fwu-theme"
rm -rf "$D$data/themes" "$D$data/gnome"
cp -R themes "$D$data/themes"
mkdir -p "$D$data/gnome"
cp -R gnome/gtk-3.0 gnome/gtk-4.0 gnome/wallpapers.tsv gnome/icons "$D$data/gnome/"
for t in FWU FWU-Dark; do
  rm -rf "$D$share/themes/$t"
  cp -R "gnome/shell/$t" "$D$share/themes/$t"
done
install -m 644 README.md "$D$share/doc/fwu-desktop-theme/README.md"

# Wallpapers for Settings → Appearance; motifs in both themes are one entry.
tab=$(printf '\t')
{
  echo '<?xml version="1.0" encoding="UTF-8"?>'
  echo '<!DOCTYPE wallpapers SYSTEM "gnome-wp-list.dtd">'
  echo '<wallpapers>'
  while IFS=$tab read -r _motif title light dark; do
    echo '  <wallpaper deleted="false">'
    echo "    <name>FWU · $title</name>"
    echo "    <filename>$data/themes/$light</filename>"
    echo "    <filename-dark>$data/themes/$dark</filename-dark>"
    echo '    <options>zoom</options>'
    echo '    <shade_type>solid</shade_type>'
    echo '  </wallpaper>'
  done < gnome/wallpapers.tsv
  echo '</wallpapers>'
} > "$D$share/gnome-background-properties/fwu.xml"

cat > "$D$autostart/fwu-theme-watch.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=FWU-Theme
Comment=Hält das FWU-Theme passend zum Hell-/Dunkelmodus
Exec=$prefix/bin/fwu-theme watch
OnlyShowIn=GNOME;
NoDisplay=true
X-GNOME-Autostart-Phase=Applications
EOF

[ -n "$destdir" ] && exit 0

echo "FWU-Theme installiert nach $prefix."
if [ -n "$omarchy" ]; then
  if [ -n "$user" ]; then
    "$prefix/bin/fwu-theme" omarchy
  else
    echo "Omarchy-Themes: als Benutzer »fwu-theme omarchy« ausführen."
  fi
fi
case :$PATH: in
  *:"$prefix/bin":*) cmd=fwu-theme ;;
  *) cmd="$prefix/bin/fwu-theme" ;;
esac
echo "GNOME:   $cmd apply        (oder: $cmd apply dark)"
[ -z "$omarchy" ] && echo "Omarchy: $cmd omarchy"
exit 0
