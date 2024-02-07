#!/bin/bash

# Function to handle signals
handle_signal() {
  echo "Caught signal $1" >> /tmp/signals.out
}

# Trap signals and specify the corresponding handler
for n in $(seq 1 31) ; do
  trap "handle_signal $n" $n
done

# Keep script running to catch signals
echo "Script running with PID $$"
while true; do
  sleep 0.1
done
