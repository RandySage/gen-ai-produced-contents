#! /usr/bin/env python3

import os
import signal
import sys

# Path to the log file
log_file_path = "/tmp/signals.log"


def signal_handler(signum, frame):
    """Signal handler function."""
    with open(log_file_path, "a") as log_file:
        log_file.write(f"Received signal: {signum}\n")
    print(f"Received signal: {signum}, check {log_file_path} for a log entry.")


def setup_signal_handlers():
    """Set up signal handlers."""
    # List of signals to catch
    signals_to_catch = [signal.SIGINT, signal.SIGTERM, signal.SIGUSR1]

    for sig in signals_to_catch:
        signal.signal(sig, signal_handler)


def main():
    """Implement script functionality."""
    setup_signal_handlers()
    print(f"Running... (PID: {os.getpid()})")
    print(f"Log file: {log_file_path}")
    # Keep the program running to catch signals
    while True:
        signal.pause()  # Wait for a signal


if __name__ == "__main__":
    main()
