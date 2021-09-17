#!/usr/bin/env -S bash -x

ctr1=$(buildah from "docker.io/centos:latest")

buildah run "$ctr1" -- dnf update -y
buildah run "$ctr1" -- dnf install -y elfutils-libelf-devel pkgconfig "@Development Tools"
buildah run "$ctr1" -- dnf install -y curl qrencode git jq iptables python39
buildah run "$ctr1" -- pip3 install wgconfig qrcode[pil]
buildah run "$ctr1" -- /bin/bash -c 'dnf clean packages; \
dnf clean metadata; \
dnf clean all; \
rm -rf \
/tmp/* \
/var/tmp/*'
