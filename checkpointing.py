### This module periodically snapshots its operational state (the active blocklist) to a local file, ensuring the internal state survives a process crash.    
    
import json
import os
import time

STATE_FILE = "server_state.json"
DEFAULT_BLACKLIST = ["10.0.5.50", "192.168.1.99", "172.16.0.4"]

def load_state():
    """The standby node loads the most recent checkpoint upon boot."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
                return state.get("BLACKLIST", DEFAULT_BLACKLIST)
        except json.JSONDecodeError:
            pass
    return DEFAULT_BLACKLIST.copy()

def state_saver_daemon(blacklist_ref, interval=3.0):
    """The primary node periodically snapshots its operational state to shared storage."""
    while True:
            with open(STATE_FILE, "w") as f:
                json.dump({"BLACKLIST": blacklist_ref}, f)
            time.sleep(interval)
