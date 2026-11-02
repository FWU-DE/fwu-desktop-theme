# FWU · Desktop-Theme für GNOME und Omarchy

Das FWU-Theme als installierbares Paket – für **GNOME** auf Debian, Ubuntu, Fedora, openSUSE, Alpine und Arch sowie für **Omarchy**. Farben und Hintergrundbilder stammen aus den beiden Omarchy-Themes:

- hell: [omarchy-fwu-theme](https://github.com/FWU-DE/omarchy-fwu-theme)
- dunkel: [omarchy-fwu-dark-theme](https://github.com/FWU-DE/omarchy-fwu-dark-theme)

## Installieren

Die Pakete liegen unter [Releases](https://github.com/FWU-DE/fwu-desktop-theme/releases).

| System | Paket | Befehl |
|---|---|---|
| Debian, Ubuntu | `.deb` | `sudo apt install ./fwu-desktop-theme_*.deb` |
| Fedora, openSUSE, RHEL | `.rpm` | `sudo dnf install ./fwu-desktop-theme-*.rpm` |
| Arch, Omarchy | `.pkg.tar.zst` | `sudo pacman -U fwu-desktop-theme-*.pkg.tar.zst` |
| Alpine, postmarketOS | `.apk` | `sudo apk add --allow-untrusted fwu-desktop-theme-*.apk` |
| alle anderen | Quellcode | `sudo make install` |

Mit `gh` geht der Download auch ohne Browser:

```sh
gh release download --repo FWU-DE/fwu-desktop-theme --pattern '*.deb'
```

### GNOME

```sh
fwu-theme apply          # folgt dem Hell-/Dunkel-Schalter von GNOME
fwu-theme apply dark     # und schaltet gleich auf dunkel
```

Für Leiste und Menüs braucht GNOME die Erweiterung **User Themes** (`gnome-shell-extensions`; Fedora: `gnome-shell-extension-user-theme`). Fehlt sie, sagt `fwu-theme apply` Bescheid.

Flatpak-Apps lesen die Farben nur mit Freigabe: `fwu-theme apply --flatpak`.

### Omarchy

Mit Zugriff auf die FWU-Repos wie gehabt:

```sh
omarchy theme install https://github.com/FWU-DE/omarchy-fwu-theme
omarchy theme install https://github.com/FWU-DE/omarchy-fwu-dark-theme
```

Ohne GitHub-Zugang über das Paket:

```sh
fwu-theme omarchy
omarchy theme set fwu-dark
```

## Was das Paket an GNOME ändert

| Teil | Wie |
|---|---|
| Hintergrundbilder | in *Einstellungen → Darstellung* als »FWU · …«; Motive aus beiden Themes erscheinen als ein Bild mit heller und dunkler Fassung |
| Programme (GTK 4 / libadwaita) | Farben über `~/.config/gtk-4.0/gtk.css`: Fenster, Kopfleisten, Seitenleisten, Karten, Akzent |
| Programme (GTK 3) | Farben über `~/.config/gtk-3.0/gtk.css` |
| Leiste, Menüs, Übersicht | Shell-Themes `FWU` und `FWU-Dark`, erzeugt aus dem Stylesheet der installierten GNOME-Version – passt also auch nach GNOME-Updates |
| Akzentfarbe | `orange` für Programme, die keine eigenen Farben laden |
| Symbole | `Yaru-red` bzw. `Yaru-red-dark`, falls installiert |

Ein kleiner Hintergrundprozess (`fwu-theme watch`, startet bei der Anmeldung) wechselt GTK-3-Farben, Shell-Theme und Symbole, wenn der Dunkelmodus umgeschaltet wird. GTK-4-Programme wechseln selbst.

`fwu-theme apply` ändert nur die eigenen Einstellungen des Benutzers. In die eigenen `gtk.css` setzt es einen markierten Block an den Anfang und lässt den Rest stehen.

## Befehle

| Befehl | Wirkung |
|---|---|
| `fwu-theme apply [light\|dark]` | Theme einschalten |
| `fwu-theme wallpaper list` | Motive anzeigen |
| `fwu-theme wallpaper fassade` | Motiv wählen; `next` für das nächste |
| `fwu-theme omarchy [--force]` | Omarchy-Themes aus dem Paket verlinken |
| `fwu-theme status` | Zustand anzeigen |
| `fwu-theme reset` | alles zurücknehmen |

## Farben

| Rolle | hell | dunkel |
|---|---|---|
| Hintergrund | `#fff9f4` | `#1d1a18` |
| Text | `#1d1a18` | `#fff3e9` |
| Akzent (Text, Links) | `#ac4119` | `#e96429` |
| Akzent (Flächen, weiße Schrift) | `#ca4d15` | `#ca4d15` |

`#ca4d15` ist das dunkelste Markenorange, auf dem weiße Schrift noch 4,5 : 1 erreicht; `#e96429` selbst schafft nur 3,3 : 1.

## Entwickeln

Die Omarchy-Repos bleiben die Quelle für Farben und Bilder. Nach Änderungen dort:

```sh
tools/sync-omarchy.sh    # Themes nach omarchy/ holen
git commit -am "Omarchy-Themes aktualisiert"
```

Eine neue Version entsteht mit einem Tag: `VERSION` anpassen, dann `git tag v1.1.0 && git push --tags`. GitHub Actions baut daraus `.deb`, `.rpm`, `.apk`, das Arch-Paket und ein Tarball und hängt sie an das Release.

Lokal: `make build` erzeugt den Paketbaum in `build/root`, `make packages` baut alle Pakete mit nfpm in Docker.

## Quellen

Kartendaten © [OpenStreetMap](https://www.openstreetmap.org/copyright)-Mitwirkende (ODbL). Name und Logo gehören FWU – Das Medieninstitut der Länder. Die Shell-Themes werden auf dem Rechner aus dem GNOME-Shell-Stylesheet (GPL-2.0-or-later) erzeugt und nicht mit dem Paket verteilt.
