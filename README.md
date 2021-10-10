# WireGuard container on Centos image

I took ideas and examples from [linuxserver/docker-wireguard](https://github.com/linuxserver/docker-wireguard)

## Notes

Run container from CLI
```
sudo podman run -d \
-v /lib/modules:/lib/modules \
-v /usr/src/kernels:/usr/src/kernels \
-v ~/config:/config \
-e PUID=1000 \
-e PGID=1000 \
-e SERVERURL=example.ru \
-e SERVERPORT=51820 `#optional` \
-e PEERS=1 `#optional` \
-e INTERNAL_SUBNETv4=10.13.13.0 `#optional` \
-e INTERNAL_SUBNETv6=fc00:bfb7:3bdb:ae33 `#optional` \
-e ALLOWEDIPSv4=0.0.0.0/0,::/0 `#optional` \
-p 51820:51820/udp \
--sysctl="net.ipv4.conf.all.src_valid_mark=1" \
--privileged
wireguard
```

If you want to use ipv6

[IPv6 Address Types](https://www.ripe.net/participate/member-support/lir-basics/ipv6_reference_card.pdf)
```
sudo podman network create --subnet <Unique Local Addresses> --ipv6 wireguard
```
