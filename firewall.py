from flask import Flask, request, jsonify
import socket
import threading
import time
import random
import os

app = Flask(__name__)

FIREWALL_IP = '127.0.0.1'
FIREWALL_PORT = 8001  # the web server (server.py) asks us for verdicts here

HEARTBEAT_IP = '127.0.0.1'
HEARTBEAT_PORT = 8000
HEARTBEAT_INTERVAL = 3.0  # T = 3 second

# LlamaLlama.com (or whatever fun website we want to make) is NOT in this list initially
BLACKLIST = ["10.0.5.50", "192.168.1.99", "172.16.0.4"]

def send_heartbeat():
    """Background thread emitting a UDP heartbeat."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        sock.sendto(b"HEARTBEAT", (HEARTBEAT_IP, HEARTBEAT_PORT))
        time.sleep(HEARTBEAT_INTERVAL)

@app.route('/inspect', methods=['GET'])
def inspect_traffic():
    """The Firewall Inspection Engine: returns an ALLOW/BLOCK verdict for an IP and Payload."""
    target_ip = request.args.get('ip', "0.0.0.0")
    
    # --- NEW STUFF: Grab the payload from the request ---
    payload = request.args.get('payload', "")

    # The Non-Deterministic Crash (5% chance)
    if random.randint(1, 20) == 1:
        print("\n[FATAL ERROR] Buffer overflow in Firewall routing! Crashing...")
        os._exit(1)

    # 1. Inspect IP against Blacklist (Original functionality)
    if target_ip in BLACKLIST:
        print(f"[FIREWALL] BLOCKED {target_ip} (Blacklisted IP)")
        return jsonify({"ip": target_ip, "verdict": "BLOCK"}), 200

    # --- NEW STUFF: Inspect Dummy Packet Payload for malicious signatures <----------
    MALICIOUS_SIGNATURES = ["drop table", "script>", "malware"]
    if any(sig in payload.lower() for sig in MALICIOUS_SIGNATURES):
        print(f"[FIREWALL] BLOCKED {target_ip} (Malicious Payload Detected: {payload})")
        return jsonify({"ip": target_ip, "verdict": "BLOCK"}), 200

    # If it passes the blacklist and the payload check, allow it!
    print(f"[FIREWALL] ALLOWED {target_ip}")
    return jsonify({"ip": target_ip, "verdict": "ALLOW"}), 200

@app.route('/hack', methods=['POST'])
def hack_blacklist():
    """Attacker endpoint: secretly add IPs to the blacklist."""
    target_ip = request.args.get('ip')
    if target_ip and target_ip not in BLACKLIST:
        BLACKLIST.append(target_ip)
        print(f"[WARNING] 🚨 UNAUTHORIZED BLACKLIST MODIFICATION: {target_ip} added!")
        return jsonify({"status": "hacked", "message": f"{target_ip} is now blocked!"}), 200
    return jsonify({"error": "Missing or duplicate IP"}), 400

if __name__ == '__main__':
    print(f"[FIREWALL] Starting Vulcan Firewall on port {FIREWALL_PORT}...")
    threading.Thread(target=send_heartbeat, daemon=True).start()
    app.run(host=FIREWALL_IP, port=FIREWALL_PORT)
