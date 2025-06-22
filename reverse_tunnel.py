import subprocess
import threading
import time
import os
import signal
import argparse

# Module-level constants with DEFAULT_ prefix
DEFAULT_REMOTE_HOST = "zebuz.com"
DEFAULT_REMOTE_SAW_SCRIPT = "/home/rsage/stuff/saw.sh"
DEFAULT_REMOTE_TEST_SCRIPT = "/home/rsage/tmp/test_connection.sh"
DEFAULT_LOCAL_SSH_PORT = 22
DEFAULT_REMOTE_TUNNEL_PORT = 22222

class SSHReverseTunnelManager:
    def __init__(self, remote_host, remote_saw_script, remote_test_script, local_port, remote_port):
        self.remote_host = remote_host
        self.remote_saw_script = remote_saw_script
        self.remote_test_script = remote_test_script
        self.local_port = local_port
        self.remote_port = remote_port

        self.reverse_tunnel_process = None
        self._stop_event = threading.Event() # Event to signal threads to stop

        print(f"Initialized SSHReverseTunnelManager for {self.remote_host}")

    def _run_reverse_tunnel(self):
        """
        Opens and maintains the reverse SSH tunnel. This method is intended to be run in a thread.
        """
        tunnel_spec = f"{self.remote_port}:localhost:{self.local_port}"
        cmd = ["ssh", "-R", tunnel_spec, self.remote_host, "bash", self.remote_saw_script]
        print(f"Starting reverse tunnel with command: {' '.join(cmd)}")

        while not self._stop_event.is_set():
            try:
                self.reverse_tunnel_process = subprocess.Popen(cmd)
                self.reverse_tunnel_process.wait()  # Wait for the process to terminate
                if not self._stop_event.is_set(): # Only print if not intentionally stopped
                    print("Reverse tunnel SSH process terminated. Restarting...")
            except Exception as e:
                if not self._stop_event.is_set():
                    print(f"Error in reverse tunnel thread: {e}")
            time.sleep(5)  # Short delay before restarting if it dies

    def _monitor_connection(self):
        """
        Monitors the reverse tunnel connection and restarts it if the test fails.
        This method is intended to be run in a thread.
        """
        test_cmd = ["ssh", self.remote_host, self.remote_test_script, str(self.remote_port)]
        while not self._stop_event.is_set():
            print(f"Testing connection with command: {' '.join(test_cmd)}")
            try:
                result = subprocess.run(test_cmd, timeout=10, capture_output=True, text=True)

                if result.returncode != 0:
                    print(f"Connection test failed at {time.ctime()}. Output:\n{result.stdout}{result.stderr}")
                    self._kill_reverse_tunnel_process()
                else:
                    print(f"Connection test successful at {time.ctime()}. Output:\n{result.stdout.strip()}")

            except subprocess.TimeoutExpired:
                print(f"Connection test timed out at {time.ctime()}.")
                self._kill_reverse_tunnel_process()
            except Exception as e:
                print(f"Error during connection monitoring: {e}")

            # Wait, but check stop event periodically to allow faster shutdown
            for _ in range(600 // 5): # Check every 5 seconds for 10 minutes (600 seconds)
                if self._stop_event.is_set():
                    break
                time.sleep(5)

    def _kill_reverse_tunnel_process(self):
        """
        Helper method to kill the reverse tunnel SSH process if it's running.
        """
        if self.reverse_tunnel_process and self.reverse_tunnel_process.poll() is None:
            pid = self.reverse_tunnel_process.pid
            print(f"Killing reverse tunnel SSH process (PID: {pid})...")
            try:
                os.kill(pid, signal.SIGTERM)
                # Give it a moment to terminate gracefully
                time.sleep(2)
                if self.reverse_tunnel_process.poll() is None:
                    print(f"Process {pid} did not terminate gracefully, sending SIGKILL...")
                    os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                print(f"Process {pid} already terminated.")
            except Exception as e:
                print(f"Error while killing process {pid}: {e}")
        else:
            print("Reverse tunnel process not found or already terminated.")

    def start(self):
        """
        Starts the two threads for managing the SSH reverse tunnel.
        """
        print("Starting SSH reverse tunnel management threads...")
        self._stop_event.clear()

        self.tunnel_thread = threading.Thread(target=self._run_reverse_tunnel, daemon=True)
        self.tunnel_thread.start()

        self.monitor_thread = threading.Thread(target=self._monitor_connection, daemon=True)
        self.monitor_thread.start()

        try:
            while not self._stop_event.is_set():
                time.sleep(1) # Keep the main thread alive
        except KeyboardInterrupt:
            print("\nScript terminated by user. Stopping threads...")
            self.stop()
        finally:
            # Ensure stop is called on unexpected exits too (e.g., if a daemon thread dies)
            self.stop()


    def stop(self):
        """
        Signals the threads to stop and attempts to terminate the SSH process.
        """
        if not self._stop_event.is_set():
            self._stop_event.set()
            print("Stop event set. Waiting for threads to finish...")

            # Give threads a moment to react to the stop event
            # Use join with a timeout to avoid blocking indefinitely
            if self.tunnel_thread.is_alive():
                self.tunnel_thread.join(timeout=5)
            if self.monitor_thread.is_alive():
                self.monitor_thread.join(timeout=5)

            self._kill_reverse_tunnel_process()
            print("SSHReverseTunnelManager stopped.")

def get_parsed_args():
    """
    Parses command-line arguments for SSH tunnel configuration.
    """
    parser = argparse.ArgumentParser(
        description="Manages an SSH reverse tunnel connection with automatic restart.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter # Shows default values in help
    )

    parser.add_argument(
        "--host",
        type=str,
        default=DEFAULT_REMOTE_HOST,
        help="The remote SSH host (e.g., 'zebuz.com')."
    )
    parser.add_argument(
        "--saw-script",
        type=str,
        default=DEFAULT_REMOTE_SAW_SCRIPT,
        help="Path to the 'saw' script on the remote host."
    )
    parser.add_argument(
        "--test-script",
        type=str,
        default=DEFAULT_REMOTE_TEST_SCRIPT,
        help="Path to the connection test script on the remote host."
    )
    parser.add_argument(
        "--local-port",
        type=int,
        default=DEFAULT_LOCAL_SSH_PORT,
        help="The local SSH server port to tunnel from (usually 22)."
    )
    parser.add_argument(
        "--remote-port",
        type=int,
        default=DEFAULT_REMOTE_TUNNEL_PORT,
        help="The remote port on the host that will tunnel to your local port."
    )

    return parser.parse_args()

def main():
    """
    Main function to parse arguments and start the SSHReverseTunnelManager.
    """
    args = get_parsed_args()

    manager = SSHReverseTunnelManager(
        remote_host=args.host,
        remote_saw_script=args.saw_script,
        remote_test_script=args.test_script,
        local_port=args.local_port,
        remote_port=args.remote_port
    )

    manager.start()

if __name__ == "__main__":
    main()
