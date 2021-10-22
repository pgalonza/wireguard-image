#!/usr/bin/env -S bash -x

ctr1=$(buildah from "registry.gitlab.com/pgalonza/basic-images/base-wireguard:latest")

buildah run "$ctr1" -- dnf update -y
buildah run "$ctr1" -- dnf install -y elfutils-libelf-devel pkgconfig "@Development Tools"
buildah run "$ctr1" -- dnf install -y curl qrencode git jq iptables python39
buildah run "$ctr1" -- /bin/bash -c 'WIREGUARD_RELEASE=$(curl -sX GET "https://api.github.com/repos/WireGuard/wireguard-tools/tags" | jq -r .[0].name); \
mkdir /app; \
cd /app; \
git clone https://git.zx2c4.com/wireguard-linux-compat && \
git clone -b $WIREGUARD_RELEASE https://git.zx2c4.com/wireguard-tools && \
cd wireguard-tools && \
make -C ./src -j$(nproc) && \
make -C ./src install && \
dnf clean packages; \
dnf clean metadata; \
dnf clean all; \
rm -rf \
/var/cache/yum \
/app/wireguard-tools \
/tmp/* \
/var/tmp/*'
# Wait when accept pull requests
# WGDASHBOARD_RELEASE=$(curl -sX GET https://github.com/donaldzou/WGDashboard/releases/latest | grep -oE "v[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}");
buildah run "$ctr1" -- /bin/bash -c 'WGDASHBOARD_RELEASE=develop; \
cd /app; \
git clone -b $WGDASHBOARD_RELEASE https://github.com/pgalonza/WGDashboard.git wgdashboard && \
cd ./wgdashboard/src; \
rm ./db/hi.txt >  /dev/null 2>&1; \
chmod u+x wgd.sh; \
chmod -R 755 /etc/wireguard'
buildah run "$ctr1" -- pip3 install -r /app/wgdashboard/src/requirements.txt
buildah copy "$ctr1" './image/scripts' '/scripts'
buildah copy "$ctr1" './wireguard-requirements.txt' '/app/wireguard-requirements.txt'
buildah run "$ctr1" -- pip3 install -r /app/wireguard-requirements.txt
buildah run "$ctr1" -- /bin/sh -c 'chmod +x /scripts/*'
# buildah run "$ctr1" -- sh -c 'umask 077; touch /etc/wireguard/wg0.conf'
buildah run "$ctr1" -- /bin/sh -c 'echo "net.ipv4.ip_forward = 1" >> /etc/sysctl.d/99-custom.conf'
buildah run "$ctr1" -- /bin/sh -c 'echo "net.ipv4.conf.all.forwarding = 1" >> /etc/sysctl.d/99-custom.conf'
buildah run "$ctr1" -- /bin/sh -c 'echo "net.ipv6.conf.all.forwarding = 1" >> /etc/sysctl.d/99-custom.conf'

## Run our server and expose the port
buildah config --cmd "/scripts/run.sh" "$ctr1"
buildah config --port 51820 "$ctr1"
## Commit this container to an image name
buildah commit "$ctr1" "${CI_REGISTRY_IMAGE}"