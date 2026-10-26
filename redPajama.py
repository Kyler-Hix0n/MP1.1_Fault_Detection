import os
import signal
import subprocess

FIREWALL_PORT = 8001
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SPOOFER = os.path.join(BASE_DIR, "heartbeat_spoofer.py")

def start_spoofer():
    """Launch the heartbeat spoofer so the monitor keeps seeing a 'healthy'
    firewall after we've killed the real one. Runs in the background."""
    proc = subprocess.Popen(["python3", SPOOFER])
    print(f"[STOP] Started heartbeat spoofer (pid {proc.pid}) - monitor will stay fooled.")
    return proc

def stop_firewall():
    """Kill whatever process is listening on the firewall port (simulates a crash on demand)."""
    result = subprocess.run(["lsof", "-t", f"-iTCP:{FIREWALL_PORT}", "-sTCP:LISTEN"],
                            capture_output=True, text=True)
    pids = [int(pid) for pid in result.stdout.split()]

    if not pids:
        print(f"[STOP] No firewall running on port {FIREWALL_PORT}.")
        return

    for pid in pids:
        os.kill(pid, signal.SIGKILL)
        print(f"[STOP] Killed firewall process {pid} on port {FIREWALL_PORT}.")

if __name__ == '__main__':
    stop_firewall()
    start_spoofer()
