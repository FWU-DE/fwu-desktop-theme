#!/usr/bin/env python3
"""Stage the package tree in build/root and write build/nfpm.yaml.

Usage: tools/build.py [VERSION]

Needs Python 3.11+ (tomllib). The installed fwu-theme command only reads the
JSON written here, so it runs on older Pythons too.
"""
import json
import os
import re
import shutil
import sys
import tomllib
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
STAGE = BUILD / "root"
SHARE = "usr/share/fwu-desktop-theme"
BACKGROUNDS = "usr/share/backgrounds/fwu"

# Omarchy theme name -> GNOME mode
VARIANTS = {"fwu": "light", "fwu-dark": "dark"}

# Darkest shade of the brand orange #e96429 that keeps white text at 4.5:1.
# Used for filled buttons, switches and selections in both modes.
ACCENT_BG = "#ca4d15"

TITLES = {
    "fwu-logo": "FWU-Logo",
    "kreis": "Leuchtender Kreis",
    "karte": "Karte Grünwald",
    "gebaeude": "Gebäude",
    "fassade": "Fassade",
    "papierwellen": "Papierwellen",
    "papierfalte": "Papierfalte",
    "untersicht": "Untersicht",
    "lichtspuren": "Lichtspuren",
    "berge": "Berge",
}


def motif(filename):
    """'3-kreis.jpg' -> 'kreis'"""
    return re.sub(r"^\d+-", "", Path(filename).stem)


def stage():
    if BUILD.exists():
        shutil.rmtree(BUILD)
    share = STAGE / SHARE
    share.mkdir(parents=True)

    palettes, wallpapers = {}, {}
    for theme, mode in VARIANTS.items():
        src = ROOT / "omarchy" / theme
        colors = tomllib.loads((src / "colors.toml").read_text())
        colors["accent_bg"] = ACCENT_BG
        colors["icons"] = (src / "icons.theme").read_text().strip()
        palettes[mode] = colors

        # Wallpapers live once, in the system backgrounds folder; the Omarchy
        # copy of the theme points its backgrounds/ there.
        bg_dir = STAGE / BACKGROUNDS / mode
        shutil.copytree(src / "backgrounds", bg_dir)
        wallpapers[mode] = {motif(f.name): f"/{BACKGROUNDS}/{mode}/{f.name}"
                            for f in sorted(bg_dir.iterdir())}

        shutil.copytree(src, share / "omarchy" / theme,
                        ignore=shutil.ignore_patterns("backgrounds", ".git"))
        os.symlink(f"/{BACKGROUNDS}/{mode}", share / "omarchy" / theme / "backgrounds")

    # Motifs in both themes become one GNOME wallpaper with a light and a dark
    # image; the others are offered on their own.
    order = list(wallpapers["light"]) + [m for m in wallpapers["dark"] if m not in wallpapers["light"]]
    entries = [{"motif": m, "title": TITLES.get(m, m.title()),
                "light": wallpapers["light"].get(m) or wallpapers["dark"][m],
                "dark": wallpapers["dark"].get(m) or wallpapers["light"][m]}
               for m in order]

    (share / "palettes.json").write_text(
        json.dumps({"palettes": palettes, "wallpapers": entries}, indent=2, ensure_ascii=False) + "\n")

    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<!DOCTYPE wallpapers SYSTEM "gnome-wp-list.dtd">',
           "<wallpapers>"]
    for e in entries:
        xml += ["  <wallpaper deleted=\"false\">",
                f"    <name>FWU · {escape(e['title'])}</name>",
                f"    <filename>{e['light']}</filename>",
                f"    <filename-dark>{e['dark']}</filename-dark>",
                "    <options>zoom</options>",
                "    <shade_type>solid</shade_type>",
                "  </wallpaper>"]
    xml.append("</wallpapers>")
    props = STAGE / "usr/share/gnome-background-properties"
    props.mkdir(parents=True)
    (props / "fwu.xml").write_text("\n".join(xml) + "\n")

    for rel, src in [("usr/bin/fwu-theme", "bin/fwu-theme"),
                     ("etc/xdg/autostart/fwu-theme-watch.desktop", "data/fwu-theme-watch.desktop"),
                     ("usr/share/doc/fwu-desktop-theme/README.md", "README.md")]:
        dest = STAGE / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / src, dest)
    (STAGE / "usr/bin/fwu-theme").chmod(0o755)


def nfpm_yaml(version):
    """One nfpm config for deb, rpm, apk and Arch packages."""
    contents = []
    for path in sorted(STAGE.rglob("*")):
        rel = path.relative_to(STAGE)
        if path.is_symlink():
            contents.append({"src": os.readlink(path), "dst": f"/{rel}", "type": "symlink"})
        elif path.is_file():
            entry = {"src": str(path.relative_to(ROOT)), "dst": f"/{rel}"}
            if rel.parts[0] == "etc":
                entry["type"] = "config"
            contents.append(entry)

    def deps(python, gi, glib):
        return {"depends": [python, gi, glib]}

    config = {
        "name": "fwu-desktop-theme",
        "arch": "all",
        "platform": "linux",
        "version": version,
        "release": 1,
        "maintainer": "FWU – Das Medieninstitut der Länder",
        "description": "FWU-Theme für GNOME und Omarchy: Farben, Shell-Theme, Hintergrundbilder",
        "homepage": "https://github.com/FWU-DE/fwu-desktop-theme",
        "license": "Proprietary",
        "contents": contents,
        "overrides": {
            "deb": {**deps("python3", "python3-gi", "libglib2.0-bin"),
                    "recommends": ["gnome-shell-extensions", "yaru-theme-icon"]},
            "rpm": {**deps("python3", "python3-gobject-base", "glib2"),
                    "recommends": ["gnome-shell-extension-user-theme"]},
            "apk": deps("python3", "py3-gobject3", "glib"),
            "archlinux": {**deps("python", "python-gobject", "glib2")},
        },
        "deb": {"fields": {"Section": "x11"}},
        "archlinux": {"packager": "FWU – Das Medieninstitut der Länder"},
    }
    if version.startswith("v"):
        config["version"] = version[1:]
    # JSON is valid YAML, so no PyYAML is needed here.
    (BUILD / "nfpm.yaml").write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    stage()
    nfpm_yaml(sys.argv[1] if len(sys.argv) > 1 else (ROOT / "VERSION").read_text().strip())
    print(f"staged {sum(1 for _ in STAGE.rglob('*'))} paths in {STAGE}")
