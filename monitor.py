"""
monitor.py (Updated for Part 2)

Changes:
1. Implements automated failover (Task 3).
2. Spawns the secondary firewall process when the primary fails.
3. Parses role from heartbeat to avoid split-brain confusion if delayed primary heartbeats arrive.
"""
import socket
import datetime
import subprocess
import time
import sys

# color codes
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

MONITOR_PORT = 8000
TIMEOUT_WIN = 4.0
MAX_MISSED_BEATS = 3
SECONDARY_PORT = 8002

def start_secondary_node():
    """Spawns the secondary firewall process (Task 3: Automated Failover)."""
    print(f"🔄 {YELLOW}[{datetime.datetime.now()}] FAILOVER TRIGGERED: Spawning Secondary Node...{RESET}")
    try:
        # Launch firewall.py as SECONDARY on the secondary port
        subprocess.Popen([sys.executable, "firewall.py", "SECONDARY", str(SECONDARY_PORT)])
        print(f"✅ {GREEN}[{datetime.datetime.now()}] Secondary Node Online. Service Restored.{RESET}")
    except Exception as e:
        print(f"❌ {RED}Failed to start secondary node: {e}{RESET}")

def run_monitor():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", MONITOR_PORT))
    sock.settimeout(TIMEOUT_WIN)

    missed_beats = 0
    server_up = False
    active_role = "PRIMARY" # Tracks which node we expect heartbeats from

    print(f"🛡️ {GREEN}[{datetime.datetime.now()}] Vulcan Monitor initalized on port {MONITOR_PORT}.{RESET}")

    while True:
        try:
            data, addr = sock.recvfrom(1024)
            message = data.decode('utf-8', errors='ignore')

            if message.startswith("HEARTBEAT"):
                role = message.split(":")[1] if ":" in message else "UNKNOWN"

                # Check for split-brain/zombie primary (Task 4: Adversarial resilience)
                if active_role == "SECONDARY" and role == "PRIMARY":
                     print(f"👻 {RED}[{datetime.datetime.now()}] Split-Brain Warning: Received heartbeat from PRIMARY, but SECONDARY is active! Ignoring zombie primary.{RESET}")
                     continue

                if not server_up:
                    print(f"🔌 {GREEN}[{datetime.datetime.now()}] Connection Established with {role} at {addr}{RESET}")
                    server_up = True
                    active_role = role

                print(f"🟢 {GREEN}[{datetime.datetime.now()}] HEARTBEAT ({role}): Received 💓{RESET}")
                missed_beats = 0

        except (socket.timeout, ConnectionResetError):
            missed_beats += 1
            print(f"⚠️ {YELLOW}[{datetime.datetime.now()}] Warning: Missed beat {missed_beats}/{MAX_MISSED_BEATS}{RESET}")

            if missed_beats >= MAX_MISSED_BEATS:
                if server_up:
                    print(f"🚨 {RED}[{datetime.datetime.now()}] ALERT: Crash Detected! Primary failed.{RESET}")
                    server_up = False

                    if active_role == "PRIMARY":
                        # Task 3: Trigger Failover
                        start_secondary_node()
                        active_role = "SECONDARY" # Expect heartbeats from secondary now
                        # reset counter so we don't immediately fail the secondary
                        missed_beats = 0
                else:
                    print(f"[{datetime.datetime.now()}] Status: No active server reachable. Waiting...")
                    missed_beats = 0


if __name__ == "__main__":
    run_monitor()



