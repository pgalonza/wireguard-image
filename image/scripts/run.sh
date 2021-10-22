#!/usr/bin/env bash

_term() {
  echo "Caught SIGTERM signal!"
  /app/wgdashboard/wgd.sh stop
  wg-quick down wg0
}
export ENVIRONMENT=production

/scripts/setup.sh

trap _term SIGTERM

wg-quick up wg0
/app/wgdashboard/wgd.sh start

sleep infinity &

wait $!
