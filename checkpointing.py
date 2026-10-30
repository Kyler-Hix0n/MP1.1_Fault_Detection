"""
checkpointing.py

This module handles the saving and loading of the firewall state (the blacklist)
to/from a local file. This provides the "Passive Redundancy (Warm Standby + Checkpointing)"
functionality required by Task 1 and Task 2.
"""
import json
import os
import threading

CHECKPOINT_FILE = "firewall_state.json"
CHECKPOINT_INTERVAL = 5.0 # Checkpoint every 5 seconds

def save_state(blacklist):
    """Saves the current blacklist to the checkpoint file."""
    try:
        with open(CHECKPOINT_FILE, 'w') as f:
            json.dump({"blacklist": blacklist}, f)
        print(f"[CHECKPOINT] State saved to {CHECKPOINT_FILE}")
    except Exception as e:
        print(f"[CHECKPOINT] Error saving state: {e}")

def load_state():
    """Loads the blacklist from the checkpoint file. Returns default if file missing or corrupt."""
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, 'r') as f:
                data = json.load(f)
                print(f"[CHECKPOINT] State loaded from {CHECKPOINT_FILE}")
                return data.get("blacklist", [])
        except json.JSONDecodeError:
            print(f"[CHECKPOINT] ERROR: Checkpoint file corrupt! Falling back to defaults.")
    
    print("[CHECKPOINT] No valid checkpoint found. Starting with default state.")
    # Return default if file doesn't exist or is corrupted
    return ["10.0.5.50", "192.168.1.99", "172.16.0.4"]

def run_checkpointer(get_blacklist_func):
    """Background thread that periodically saves the firewall state."""
    while True:
        import time
        time.sleep(CHECKPOINT_INTERVAL)
        save_state(get_blacklist_func())
