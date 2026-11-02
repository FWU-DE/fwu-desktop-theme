#!/bin/sh
# Build .deb, .rpm, .apk and Arch packages plus a tarball into dist/.
# Usage: tools/package.sh VERSION   (needs nfpm: https://nfpm.goreleaser.com)
set -eu
cd "$(dirname "$0")/.."
VERSION=${1#v}
export VERSION
rm -rf build dist
mkdir -p dist
./install.sh --prefix /usr --destdir build/root
for p in deb rpm apk archlinux; do
  nfpm package --config nfpm.yaml --packager "$p" --target dist/
done
git archive --format=tar.gz --prefix="fwu-desktop-theme-$VERSION/" -o "dist/fwu-desktop-theme-$VERSION.tar.gz" HEAD
ls -l dist
