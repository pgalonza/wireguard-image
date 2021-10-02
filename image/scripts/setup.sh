#!/usr/bin/env bash 

echo "Uname info: $(uname -a)"
# check for wireguard module
ip link del dev test 2>/dev/null
if ip link add dev test type wireguard; then
  echo "**** It seems the wireguard module is already active. Skipping kernel header install and module compilation. ****"
  SKIP_COMPILE="true"
  ip link del dev test
else
  echo "**** The wireguard module is not active, will attempt kernel header install and module compilation. ****"
fi

# install headers if necessary
if [ "$SKIP_COMPILE" != "true" ] && [ ! -e /lib/modules/$(uname -r)/build ]; then
  echo "**** Attempting kernel header install ****"
  if dnf list --available kernel-headers-$(uname -r) 2&>1 > /dev/null; then
    dnf install -y \
      linux-headers-$(uname -r)
  else
    echo "**** No kernel headers found in the Centos repos!! Will try the headers from host (if mapped), may or may not work ****"
  fi
fi

if [ "$SKIP_COMPILE" != "true" ]; then
  if [ -e /lib/modules/$(uname -r)/build ]; then 
    echo "**** Kernel headers seem to be present, attempting to build the wireguard module... ****"
    if [ ! -f /lib/modules/$(uname -r)/build/certs/signing_key.pem ]; then
      mkdir -p /lib/modules/$(uname -r)/build/certs
      cd /lib/modules/$(uname -r)/build/certs
      cat << DUDE >> x509.genkey
[ req ]
default_bits = 4096
distinguished_name = req_distinguished_name
prompt = no
string_mask = utf8only
x509_extensions = myexts

[ req_distinguished_name ]
CN = Modules

[ myexts ]
basicConstraints=critical,CA:FALSE
keyUsage=digitalSignature
subjectKeyIdentifier=hash
authorityKeyIdentifier=keyid
DUDE
      echo "**** Generating signing key ****"
      openssl req -new -nodes -utf8 -sha512 -days 36500 -batch -x509 -config x509.genkey -outform DER -out signing_key.x509 -keyout signing_key.pem
    fi
    cd /app
    echo "**** Building the module ****"
    make -C wireguard-linux-compat/src -j$(nproc)
    make -C wireguard-linux-compat/src install
    echo "**** Let's test our new module. ****"
    ip link del dev test 2>/dev/null
    if ip link add dev test type wireguard; then
      echo "**** The module is active, moving forward with setup. ****"
      ip link del dev test
    else
      echo "**** The module is not active, review the logs. Sleeping now... ****"
      sleep infinity
    fi
  else
    echo "**** Kernel headers don't seem to be available, can't compile the module. Sleeping now... ****"
    sleep infinity
  fi
fi

python3 /scripts/generate_settings.py

# prepare symlinks
rm -rf /etc/wireguard
mkdir -p /etc/wireguard
ln -s /config/wg0.conf /etc/wireguard/wg0.conf

groupadd -g "${PGID}" wireguard
useradd -o -u "${PUID}" -g "${PGID}" -s /bin/bash wireguard

# permissions
chown -R wireguard:wireguard /config/*

_term() {
  echo "Caught SIGTERM signal!"
  wg-quick down wg0
}

trap _term SIGTERM

wg-quick up wg0

sleep infinity &

wait $!

