#!/bin/bash

simulate_response() {
  for n in $(seq 1 20) ; do
    echo "$(date +%H:%M:%S.%3N) Sim respond signal '$1'" >> /tmp/response.out
    sleep 0.01
  done
}

# Function to handle signals
handle_signal() {
  echo "$(date +%H:%M:%S.%3N) Caught signal '$1'" >> /tmp/signals.out
  simulate_response $1 &
}

# Trap signals and specify the corresponding handler, excluding 17 SIGCHLD
for signal in $(kill -l | grep -oh 'SIG\S*' | grep -ve '[+-]' -ve CHLD | sed -e 's/^SIG//'
) ; do
  trap "handle_signal $signal" $signal
done

# Keep script running to catch signals
echo "Script running with PID $$"
while true; do
  sleep 0.1
done
