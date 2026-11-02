#!/usr/bin/env python3
"""Generate gnome/ from the two themes in themes/.

Usage: tools/build.py

Only needed after changing themes/*/colors.toml or the wallpapers; the
output is committed, so installing needs neither Python nor this script.
The GNOME Shell overrides are derived from the shell stylesheet of the
machine running this (GNOME Shell's gnome-shell-theme.gresource); without
one, the existing gnome/shell files are kept.
"""
import colorsys
import re
import shutil
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "gnome"
SHELL_GRESOURCE = "/usr/share/gnome-shell/gnome-shell-theme.gresource"

VARIANTS = {"light": "fwu", "dark": "fwu-dark"}
SHELL_THEMES = {"light": "FWU", "dark": "FWU-Dark"}

# Darkest shade of the brand orange #e96429 that keeps white text at 4.5:1.
# Used for filled buttons, switches and selections in both modes.
ACCENT_BG = "#ca4d15"

TITLES = {
    "fwu-logo": "FWU-Logo", "kreis": "Leuchtender Kreis", "karte": "Karte Grünwald",
    "gebaeude": "Gebäude", "fassade": "Fassade", "papierwellen": "Papierwellen",
    "papierfalte": "Papierfalte", "untersicht": "Untersicht",
    "lichtspuren": "Lichtspuren", "berge": "Berge",
}

HEADER = "/* Erzeugt von tools/build.py aus themes/{theme}/colors.toml – nicht von Hand ändern. */\n"


# --- colours -----------------------------------------------------------------

def rgb(hexstr):
    h = hexstr.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def hexc(r, g, b):
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(v))) for v in (r, g, b))


def mix(a, b, t):
    (r1, g1, b1), (r2, g2, b2) = rgb(a), rgb(b)
    return hexc(r1 + (r2 - r1) * t, g1 + (g2 - g1) * t, b1 + (b2 - b1) * t)


def rgba(hexstr, alpha):
    return "rgba(%d, %d, %d, %s)" % (*rgb(hexstr), alpha)


def palette(theme):
    p = tomllib.loads((ROOT / "themes" / theme / "colors.toml").read_text())
    p["accent_bg"] = ACCENT_BG
    return p


# --- GTK ---------------------------------------------------------------------

def adw_colors(mode, p):
    """libadwaita's named colours for one mode, filled from the FWU palette."""
    fg, bg = p["foreground"], p["background"]
    if mode == "light":
        c = {
            "window_bg": bg, "view_bg": p["lighter_background"],
            "headerbar_bg": p["dark_background"], "headerbar_backdrop": bg,
            "sidebar_bg": p["dark_background"], "sidebar_backdrop": bg,
            "secondary_sidebar_bg": bg, "secondary_sidebar_backdrop": bg,
            "card_bg": p["lighter_background"], "thumbnail_bg": p["lighter_background"],
            "popover_bg": p["lighter_background"], "dialog_bg": bg,
            "shade": rgba("#3a1a0a", 0.07),
        }
    else:
        raised = mix(p["lighter_background"], fg, 0.05)
        c = {
            "window_bg": bg, "view_bg": p["dark_background"],
            "headerbar_bg": p["lighter_background"], "headerbar_backdrop": bg,
            "sidebar_bg": p["lighter_background"], "sidebar_backdrop": bg,
            "secondary_sidebar_bg": bg, "secondary_sidebar_backdrop": p["dark_background"],
            "card_bg": rgba(fg, 0.06), "thumbnail_bg": raised,
            "popover_bg": raised, "dialog_bg": p["lighter_background"],
            "shade": rgba("#000000", 0.36),
        }
    for k in ("window", "view", "headerbar", "sidebar", "secondary_sidebar",
              "card", "thumbnail", "popover", "dialog"):
        c[f"{k}_fg"] = fg
    c.update({
        "accent": p["accent"], "accent_bg": p["accent_bg"], "accent_fg": "#ffffff",
        "destructive": p["red"], "destructive_bg": "#ba2c2c", "destructive_fg": "#ffffff",
        "success": p["green"], "success_bg": "#297047", "success_fg": "#ffffff",
        "warning": p["yellow"], "warning_bg": "#7d5d00", "warning_fg": "#ffffff",
        "error": p["red"], "error_bg": "#ba2c2c", "error_fg": "#ffffff",
    })
    return {k + "_color": v for k, v in c.items()}


def define_colors(colors):
    return "".join(f"@define-color {k} {v};\n" for k, v in colors.items())


def css_vars(colors, indent):
    return "\n".join(f"{indent}--{k.replace('_', '-')}: {v};" for k, v in colors.items())


def gtk4(mode, pal):
    """libadwaita 1.6+ reads the variables and switches by media query by
    itself; older versions only know @define-color, which fwu-theme swaps."""
    light, dark = adw_colors("light", pal["light"]), adw_colors("dark", pal["dark"])
    return (HEADER.format(theme=VARIANTS[mode])
            + define_colors(light if mode == "light" else dark)
            + "\n:root {\n" + css_vars(light, "  ") + "\n}\n"
            + "\n@media (prefers-color-scheme: dark) {\n  :root {\n"
            + css_vars(dark, "    ") + "\n  }\n}\n")


def gtk3(mode, pal):
    p = pal[mode]
    c = adw_colors(mode, p)
    # Adwaita (GTK 3) names first, then the libadwaita names adw-gtk3 uses.
    legacy = {
        "theme_bg_color": c["window_bg_color"], "theme_fg_color": p["foreground"],
        "theme_base_color": c["view_bg_color"], "theme_text_color": p["foreground"],
        "theme_selected_bg_color": p["accent_bg"], "theme_selected_fg_color": "#ffffff",
        "theme_unfocused_bg_color": c["window_bg_color"], "theme_unfocused_fg_color": p["foreground"],
        "theme_unfocused_selected_bg_color": p["accent_bg"],
        "theme_unfocused_selected_fg_color": "#ffffff",
    }
    return HEADER.format(theme=VARIANTS[mode]) + define_colors(legacy) + define_colors(c)


# --- GNOME Shell -------------------------------------------------------------

HEX = re.compile(r"#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
RGB = re.compile(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)")


def recolor(r, g, b, warm_hue, accent):
    """Warm up neutral greys; turn the old Adwaita blue into FWU orange."""
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    if max(r, g, b) - min(r, g, b) <= 8:
        if l <= 0.02 or l >= 0.995:
            return None
        return colorsys.hls_to_rgb(warm_hue, l, 0.10 if l < 0.5 else 0.25)
    if s > 0.4 and 195 / 360 <= h <= 235 / 360:
        ah, _, as_ = colorsys.rgb_to_hls(*(v / 255 for v in rgb(accent)))
        return colorsys.hls_to_rgb(ah, l, as_)
    return None


def recolor_value(value, p):
    warm_hue = colorsys.rgb_to_hls(*(v / 255 for v in rgb(p["background"])))[0]
    value = value.replace("-st-accent-fg-color", "#ffffff").replace("-st-accent-color", p["accent_bg"])

    def sub_hex(m):
        new = recolor(*rgb(m.group(0)), warm_hue, p["accent_bg"])
        return hexc(*(v * 255 for v in new)) if new else m.group(0)

    def sub_rgb(m):
        new = recolor(*(int(v) for v in m.groups()), warm_hue, p["accent_bg"])
        if not new:
            return m.group(0)
        return "%s(%d, %d, %d" % (m.group(0).split("(")[0], *(round(v * 255) for v in new))

    return RGB.sub(sub_rgb, HEX.sub(sub_hex, value))


def shell(mode, p, source, version):
    """GNOME's own stylesheet, then only the declarations whose colours change.

    Importing the stock stylesheet keeps the theme working on other GNOME
    versions; an override for a selector that no longer exists does nothing.
    """
    css = re.sub(r"/\*.*?\*/", "", source, flags=re.S)
    out = [f"/* FWU – GNOME-Shell-Theme ({'hell' if mode == 'light' else 'dunkel'}).",
           f" * Überschreibt nur Farben; abgeleitet von GNOME Shell {version}",
           " * (GPL-2.0-or-later) mit tools/build.py – nicht von Hand ändern. */",
           f'@import url("resource:///org/gnome/shell/theme/gnome-shell-{mode}.css");', ""]
    for selector, body in re.findall(r"([^{}]+)\{([^{}]*)\}", css):
        changed = []
        for decl in body.split(";"):
            if ":" not in decl:
                continue
            prop, value = (x.strip() for x in decl.split(":", 1))
            new = recolor_value(value, p)
            if new != value:
                changed.append(f"  {prop}: {new};")
        if changed:
            out.append(" ".join(selector.split()) + " {\n" + "\n".join(changed) + " }")
    return "\n".join(out) + "\n"


def shell_sources():
    try:
        import gi
        from gi.repository import Gio
        res = Gio.Resource.load(SHELL_GRESOURCE)
        version = "?"
        import subprocess
        r = subprocess.run(["gnome-shell", "--version"], capture_output=True, text=True)
        if r.returncode == 0:
            version = r.stdout.split()[-1]
        return version, {m: res.lookup_data(f"/org/gnome/shell/theme/gnome-shell-{m}.css", 0)
                         .get_data().decode() for m in VARIANTS}
    except Exception as e:
        print(f"Shell-Stylesheet nicht lesbar ({e}) – gnome/shell bleibt unverändert")
        return None, None


# --- wallpapers --------------------------------------------------------------

def motif(filename):
    """'3-kreis.jpg' -> 'kreis'"""
    return re.sub(r"^\d+-", "", Path(filename).stem)


def wallpapers():
    """Tab-separated: motif, title, light image, dark image (relative to themes/).
    Motifs in both themes become one entry with a light and a dark image."""
    found = {mode: {motif(f.name): f"{theme}/backgrounds/{f.name}"
                    for f in sorted((ROOT / "themes" / theme / "backgrounds").iterdir())}
             for mode, theme in VARIANTS.items()}
    order = list(found["light"]) + [m for m in found["dark"] if m not in found["light"]]
    rows = []
    for m in order:
        light = found["light"].get(m) or found["dark"][m]
        dark = found["dark"].get(m) or found["light"][m]
        rows.append("\t".join([m, TITLES.get(m, m.title()), light, dark]))
    return "\n".join(rows) + "\n"


# --- main ----------------------------------------------------------------------

def write(rel, text):
    path = OUT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)


def main():
    pal = {mode: palette(theme) for mode, theme in VARIANTS.items()}
    for d in ("gtk-3.0", "gtk-4.0"):
        shutil.rmtree(OUT / d, ignore_errors=True)
    for mode in VARIANTS:
        write(f"gtk-4.0/{mode}.css", gtk4(mode, pal))
        write(f"gtk-3.0/{mode}.css", gtk3(mode, pal))
    write("wallpapers.tsv", wallpapers())
    write("icons", "\n".join(f"{m}\t{(ROOT / 'themes' / t / 'icons.theme').read_text().strip()}"
                             for m, t in VARIANTS.items()) + "\n")

    version, sources = shell_sources()
    if sources:
        for mode, name in SHELL_THEMES.items():
            write(f"shell/{name}/gnome-shell/gnome-shell.css", shell(mode, pal[mode], sources[mode], version))
    print(f"gnome/ erzeugt ({'mit' if sources else 'ohne'} Shell-Themes)")


if __name__ == "__main__":
    main()
