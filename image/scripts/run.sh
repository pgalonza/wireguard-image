#!/usr/bin/env bash

_term() {
  echo "Caught SIGTERM signal!"
  cd /app/wgdashboard/src/ && ./wgd.sh stop
  wg-quick down wg0
}
export ENVIRONMENT=production
export CONFIGURATION_PATH=/config

/scripts/setup.sh

trap _term SIGTERM

wg-quick up wg0

cd /app/wgdashboard/src/ && ./wgd.sh start

sleep infinity &

wait $!
