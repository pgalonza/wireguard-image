#!/usr/bin/env bash

_term() {
  echo "Caught SIGTERM signal!"
  wg-quick down wg0
}

/scripts/setup.sh

trap _term SIGTERM

wg-quick up wg0

sleep infinity &

wait $!
