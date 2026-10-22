from flask import Flask, request, jsonify
import socket
import threading
import time
import random
import os

app = Flask(__name__)

HEARTBEAT_IP = '127.0.0.1'
HEARTBEAT_PORT = 8000
HEARTBEAT_INTERVAL = 3.0  # T = 3 second

# LlamaLlama.com (or whatever fun website we want to make)is NOT in this list initially
BLACKLIST = ["10.0.5.50", "192.168.1.99", "172.16.0.4"]

# A dictionary simulating DNS
DNS_RECORDS = {
    "llamallama.com": "10.0.99.99",
    "some blocked website": "10.0.5.50"
}

def send_heartbeat():
    """Background thread emitting a UDP heartbeat."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        sock.sendto(b"HEARTBEAT", (HEARTBEAT_IP, HEARTBEAT_PORT))
        time.sleep(HEARTBEAT_INTERVAL)

@app.route('/')
def browser_home():
    html = """
    <!DOCTYPE html>
    <html>
    <head><title>My Web Browser</title></head>
    <body style="font-family: Arial; padding: 50px; background-color: #f4f4f9;">
        <h2>Welcome to your Browser</h2>
        <p>Protected by Vulcan Network Sentinel Firewall</p>
        <h3>My Bookmarks:</h3>
        <ul>
            <li><a href="/visit?site=llamallama.com" style="font-size: 20px; color: blue;">🦙 Visit LlamaLlama.com (Favorite!)</a></li>
            <li><a href="/visit?site=some blocked website" style="font-size: 20px; color: red;">☠️ Visit sketchy-site.com</a></li>
        </ul>
    </body>
    </html>
    """
    return html

@app.route('/visit', methods=['GET'])
def inspect_traffic():
    """The Firewall Inspection Engine."""
    site = request.args.get('site')
    target_ip = DNS_RECORDS.get(site, "0.0.0.0")

    # The Non-Deterministic Crash (5% chance)
    if random.randint(1, 20) == 1:
        print("\n[FATAL ERROR] Buffer overflow in Firewall routing! Crashing...")
        os._exit(1)

    # Firewall Logic
    if target_ip in BLACKLIST:
        print(f"[FIREWALL] BLOCKED access to {site} ({target_ip})")
        return f"""
        <body style="background-color: darkred; color: white; text-align: center; padding: 50px; font-family: Arial;">
            <h1>🛑 ACCESS DENIED</h1>
            <h2>Vulcan Firewall blocked connection to: {target_ip}</h2>
            <p>Reason: IP address is on the restricted blacklist.</p>
            <a href="/" style="color: yellow;">Go Back</a>
        </body>
        """, 403
    else:
        print(f"[FIREWALL] ALLOWED access to {site} ({target_ip})")
        
        # If it's the Llama site, show the fun webpage!
        if site == "llamallama.com":
            return render_llama_website()
        
        return f"<h3>Welcome to {site}</h3><a href='/'>Go Back</a>", 200

def render_llama_website():
    return """
    <body style="background-color: #ffb3ba; text-align: center; font-family: 'Comic Sans MS', cursive;">
        <h1 style="color: #ba1a49;">Welcome to LlamaLlama.com! 🦙</h1>
        <p>The best place on the internet!</p>
        <pre style="font-size: 20px;">
           //
          //
       __//__ 
      /      \ 
      |  0 0  |
      |   U   |
       \____/ 
        |  |
        |  |
        </pre>
        <br>
        <a href="/">Close Tab</a>
    </body>
    """

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
    print("[FIREWALL] Starting Web Sentinel on port 8000...")
    threading.Thread(target=send_heartbeat, daemon=True).start()
    app.run(host='127.0.0.1', port=8000)
