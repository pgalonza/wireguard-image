#!/usr/bin/env -S bash -x

ctr1=$(buildah from "docker.io/centos:latest")

buildah run "$ctr1" -- dnf update -y
#buildah run "$ctr1" -- dnf install -y elfutils-libelf-devel pkgconfig "@Development Tools"
buildah run "$ctr1" -- dnf install -y curl qrencode git jq iptables python39
buildah run "$ctr1" -- pip3 install -r ./wireguard-requirements.txt
buildah run "$ctr1" -- /bin/bash -c 'WIREGUARD_RELEASE=$(curl -sX GET "https://api.github.com/repos/WireGuard/wireguard-tools/tags" | jq -r .[0].name); \
mkdir /app; \
cd /app; \
git clone https://git.zx2c4.com/wireguard-linux-compat && \
git clone https://git.zx2c4.com/wireguard-tools && \
cd wireguard-tools && \
git checkout "${WIREGUARD_RELEASE}" && \
make -C ./src -j$(nproc) && \
make -C ./src install && \
dnf clean packages; \
dnf clean metadata; \
dnf clean all; \
rm -rf \
/app/wireguard-tools \
/tmp/* \
/var/tmp/*'
buildah copy "$ctr1" './image/scripts' '/scripts'
buildah run "$ctr1" -- /bin/sh -c 'chmod +x /scripts/*'
# buildah run "$ctr1" -- sh -c 'umask 077; touch /etc/wireguard/wg0.conf'
buildah run "$ctr1" -- /bin/sh -c 'echo "net.ipv4.ip_forward = 1" >> /etc/sysctl.d/99-custom.conf'
buildah run "$ctr1" -- /bin/sh -c 'echo "net.ipv4.conf.all.forwarding = 1" >> /etc/sysctl.d/99-custom.conf'
buildah run "$ctr1" -- /bin/sh -c 'echo "net.ipv6.conf.all.forwarding = 1" >> /etc/sysctl.d/99-custom.conf'

## Run our server and expose the port
buildah config --cmd "/bin/sh -c '/scripts/setup.sh ; /scripts/run.sh'" "$ctr1"
buildah config --port 51820 "$ctr1"
## Commit this container to an image name
buildah commit "$ctr1" "${CI_REGISTRY_IMAGE}"
