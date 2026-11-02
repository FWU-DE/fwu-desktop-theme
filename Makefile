# make install            – direkt ins System (PREFIX=/usr)
# make install DESTDIR=…  – für eigene Paketbauten
# make packages           – .deb, .rpm, .apk und Arch-Paket per nfpm (Docker)
VERSION := $(shell cat VERSION)
DESTDIR ?=

.PHONY: build install uninstall packages clean

build:
	python3 tools/build.py $(VERSION)

install: build
	cp -a build/root/. $(DESTDIR)/

uninstall:
	rm -rf $(DESTDIR)/usr/share/fwu-desktop-theme $(DESTDIR)/usr/share/backgrounds/fwu \
	  $(DESTDIR)/usr/share/doc/fwu-desktop-theme
	rm -f $(DESTDIR)/usr/bin/fwu-theme $(DESTDIR)/usr/share/gnome-background-properties/fwu.xml \
	  $(DESTDIR)/etc/xdg/autostart/fwu-theme-watch.desktop

packages: build
	mkdir -p dist
	for p in deb rpm apk archlinux; do \
	  docker run --rm -v "$$PWD":/src -w /src goreleaser/nfpm:v2.43.0 \
	    package --config build/nfpm.yaml --packager $$p --target dist/ || exit 1; \
	done

clean:
	rm -rf build dist
