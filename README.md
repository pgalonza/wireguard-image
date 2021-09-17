# WireGuard container on Centos image

I took ideas and examples from https://github.com/linuxserver/docker-wireguard

## Notes

Run container from cli
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
-e INTERNAL_SUBNET=10.13.13.0 `#optional` \
-e ALLOWEDIPS=0.0.0.0/0 `#optional` \
-p 51820:51820/udp \
--privileged
wireguard
```
