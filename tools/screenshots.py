#!/usr/bin/env python3
"""Render README screenshots with placeholder data into docs/.

Usage: tools/screenshots.py   (inside a desktop session; needs GTK 4 and
libadwaita 1.6+ with Python bindings)

A demo window with made-up content is drawn over an FWU wallpaper, coloured
by gnome/gtk-4.0/*.css exactly as installed, once light and once dark. The
window shows on screen for a moment while it is rendered.
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, GLib, Gtk  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
WIDTH, HEIGHT = 1440, 900

SCENES = [
    ("light", "themes/fwu/backgrounds/3-kreis.jpg", "docs/gnome-hell.png"),
    ("dark", "themes/fwu-dark/backgrounds/6-fassade.jpg", "docs/gnome-dunkel.png"),
]

FRAME_CSS = """
.demo-window {
  border-radius: 14px;
  box-shadow: 0 18px 48px rgba(0, 0, 0, 0.45), 0 0 0 1px rgba(0, 0, 0, 0.12);
}
"""


def row(title, subtitle=None, suffix=None):
    r = Adw.ActionRow(title=title)
    if subtitle:
        r.set_subtitle(subtitle)
    if suffix:
        r.add_suffix(suffix)
    return r


def switch(active):
    s = Gtk.Switch(active=active, valign=Gtk.Align.CENTER)
    return s


def demo_window():
    # Sidebar
    sidebar = Gtk.ListBox(css_classes=["navigation-sidebar"])
    for icon, label in [("go-home-symbolic", "Start"), ("x-office-document-symbolic", "Unterricht"),
                        ("folder-videos-symbolic", "Mediathek"), ("user-bookmarks-symbolic", "Merkliste"),
                        ("emblem-system-symbolic", "Einstellungen")]:
        box = Gtk.Box(spacing=12, margin_top=8, margin_bottom=8, margin_start=6)
        box.append(Gtk.Image(icon_name=icon))
        box.append(Gtk.Label(label=label, xalign=0))
        sidebar.append(box)
    sidebar.select_row(sidebar.get_row_at_index(4))
    side = Adw.ToolbarView()
    side.add_top_bar(Adw.HeaderBar(show_end_title_buttons=False, title_widget=Adw.WindowTitle(title="Beispiel-App")))
    side.set_content(sidebar)

    # Content
    page = Adw.PreferencesPage()
    account = Adw.PreferencesGroup(title="Konto")
    account.add(row("Max Mustermann", "max.mustermann@example.org",
                    Gtk.Button(label="Abmelden", valign=Gtk.Align.CENTER)))
    entry = Adw.EntryRow(title="Lerngruppe")
    entry.set_text("Beispielklasse 7b")
    account.add(entry)
    page.add(account)

    prefs = Adw.PreferencesGroup(title="Darstellung", description="Alle Inhalte sind Beispieldaten.")
    prefs.add(row("Benachrichtigungen", "Bei neuen Materialien", switch(True)))
    prefs.add(row("Offline verfügbar", "Medien auf diesem Gerät speichern", switch(False)))
    level = Gtk.LevelBar(value=0.62, valign=Gtk.Align.CENTER, width_request=180)
    prefs.add(row("Speicher", "6,2 von 10 GB belegt", level))
    page.add(prefs)

    actions = Gtk.Box(spacing=12, halign=Gtk.Align.END, margin_top=6)
    actions.append(Gtk.Button(label="Löschen", css_classes=["destructive-action"]))
    actions.append(Gtk.Button(label="Abbrechen"))
    actions.append(Gtk.Button(label="Speichern", css_classes=["suggested-action"]))
    group = Adw.PreferencesGroup()
    group.add(actions)
    page.add(group)

    content = Adw.ToolbarView()
    header = Adw.HeaderBar(show_start_title_buttons=False, title_widget=Adw.WindowTitle(title="Einstellungen"))
    header.pack_end(Gtk.Button(icon_name="open-menu-symbolic"))
    header.pack_start(Gtk.ToggleButton(icon_name="edit-find-symbolic", active=True))
    content.add_top_bar(header)
    search = Gtk.SearchEntry(placeholder_text="Suchen", margin_start=12, margin_end=12, margin_top=6, margin_bottom=6)
    content.add_top_bar(search)
    content.set_content(page)

    split = Adw.NavigationSplitView(sidebar=Adw.NavigationPage(child=side, title="Beispiel-App"),
                                    content=Adw.NavigationPage(child=content, title="Einstellungen"))
    split.set_min_sidebar_width(240)
    frame = Gtk.Box(css_classes=["demo-window", "background"], overflow=Gtk.Overflow.HIDDEN,
                    width_request=980, height_request=640, halign=Gtk.Align.CENTER, valign=Gtk.Align.CENTER)
    split.set_hexpand(True)
    frame.append(split)
    return frame


def scene(wallpaper):
    overlay = Gtk.Overlay()
    pic = Gtk.Picture.new_for_filename(str(ROOT / wallpaper))
    pic.set_content_fit(Gtk.ContentFit.COVER)
    overlay.set_child(pic)
    overlay.add_overlay(demo_window())
    overlay.set_size_request(WIDTH, HEIGHT)
    return overlay


def render(win, widget, out):
    paintable = Gtk.WidgetPaintable(widget=widget)
    snap = Gtk.Snapshot()
    paintable.snapshot(snap, WIDTH, HEIGHT)
    node = snap.to_node()
    texture = win.get_renderer().render_texture(node, None)
    texture.save_to_png(str(ROOT / out))
    print("geschrieben:", out)


def shoot(mode, wallpaper, out):
    app = Adw.Application(application_id="de.fwu.ThemeScreenshots." + mode)

    def activate(_app):
        frame = Gtk.CssProvider()
        frame.load_from_string(FRAME_CSS)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), frame,
                                                  Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        Adw.StyleManager.get_default().set_color_scheme(
            Adw.ColorScheme.FORCE_DARK if mode == "dark" else Adw.ColorScheme.FORCE_LIGHT)
        win = Adw.ApplicationWindow(application=app, default_width=WIDTH, default_height=HEIGHT, resizable=False)
        content = scene(wallpaper)
        win.set_content(content)
        win.present()

        def done():
            render(win, content, out)
            app.quit()
            return False
        GLib.timeout_add(1200, done)

    app.connect("activate", activate)
    app.run([])


def main():
    if len(sys.argv) == 4:
        shoot(*sys.argv[1:])
        return 0
    # Each scene runs in its own process with a scratch config dir whose
    # gtk.css imports the theme, so GTK loads it exactly as on a real desktop.
    with tempfile.TemporaryDirectory() as cfg:
        gtk = Path(cfg) / "gtk-4.0"
        gtk.mkdir()
        shutil.copy(ROOT / "gnome/gtk-4.0/light.css", gtk / "fwu-desktop-theme.css")
        (gtk / "gtk.css").write_text('@import url("fwu-desktop-theme.css");\n')
        env = dict(os.environ, XDG_CONFIG_HOME=cfg)
        for scene_args in SCENES:
            subprocess.run([sys.executable, __file__, *scene_args], env=env, check=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
