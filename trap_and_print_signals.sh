#!/bin/bash

# Function to handle signals
handle_signal() {
  echo "Caught signal $1" >> /tmp/signals.out
}

# Trap signals and specify the corresponding handler
trap 'handle_signal HUP' HUP
trap 'handle_signal INT' INT
trap 'handle_signal QUIT' QUIT
trap 'handle_signal ABRT' ABRT
trap 'handle_signal KILL' KILL
trap 'handle_signal ALRM' ALRM
trap 'handle_signal TERM' TERM
# Add more traps for other signals as needed

# Keep script running to catch signals
echo "Script running with PID $$"
while true; do
  sleep 0.1
done
