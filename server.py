from flask import Flask, request, send_from_directory
import os
import json
import urllib.request
import urllib.parse

app = Flask(__name__)

SERVER_IP = '127.0.0.1'
SERVER_PORT = 8080

# Where the firewall process (firewall.py) is listening for inspection requests
FIREWALL_URL = 'http://127.0.0.1:8001/inspect'
FIREWALL_TIMEOUT = 1.0  # seconds to wait for a verdict before treating the firewall as down

# A dictionary simulating DNS
DNS_RECORDS = {
    "llamallama.com": "10.0.99.99",
    "some blocked website": "10.0.5.50"
}

def ask_firewall(target_ip):
    """Ask the firewall process for a verdict. Returns "ALLOW", "BLOCK", or None if the firewall is down."""
    url = f"{FIREWALL_URL}?{urllib.parse.urlencode({'ip': target_ip})}"
    try:
        with urllib.request.urlopen(url, timeout=FIREWALL_TIMEOUT) as resp:
            return json.loads(resp.read())["verdict"]
    except Exception:
        # Connection refused / reset / timeout -> firewall crashed or is unreachable
        return None

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Mario GIF that bounces around the page like a DVD screensaver
MARIO_GIF_HTML = """
<img id="mario" src="/mario-dance.gif" alt="Mario dancing" style="position: fixed; left: 0; top: 0; width: 120px; z-index: 9999;">
<script>
    const mario = document.getElementById('mario');
    let x = 50, y = 50, dx = 6, dy = 6;  // position and speed in pixels per frame
    function bounce() {
        const maxX = window.innerWidth - mario.offsetWidth;
        const maxY = window.innerHeight - mario.offsetHeight;
        x += dx;
        y += dy;
        if (x <= 0 || x >= maxX) { dx = -dx; x = Math.max(0, Math.min(x, maxX)); }
        if (y <= 0 || y >= maxY) { dy = -dy; y = Math.max(0, Math.min(y, maxY)); }
        mario.style.left = x + 'px';
        mario.style.top = y + 'px';
        requestAnimationFrame(bounce);
    }
    requestAnimationFrame(bounce);
</script>
"""

@app.route('/mario-dance.gif')
def mario_gif():
    return send_from_directory(BASE_DIR, 'mario-dance.gif')

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
def visit_site():
    """Route the user's request through the firewall, then serve the site."""
    site = request.args.get('site')
    target_ip = DNS_RECORDS.get(site, "0.0.0.0")
    print(f"   user IP = {request.remote_addr}, target_ip = {target_ip}")

    verdict = ask_firewall(target_ip)

    if verdict == "BLOCK":
        print(f"[SERVER] Firewall BLOCKED access to {site} ({target_ip})")
        return f"""
        <body style="background-color: darkred; color: white; text-align: center; padding: 50px; font-family: Arial;">
            <h1>🛑 ACCESS DENIED</h1>
            <h2>Vulcan Firewall blocked connection to: {target_ip}</h2>
            <p>Reason: IP address is on the restricted blacklist.</p>
            <a href="/" style="color: yellow;">Go Back</a>
        </body>
        """, 403

    if verdict is None:
        # Fail-open: the firewall is down, so the server stays available but traffic is NOT filtered
        print(f"[SERVER] ⚠️  Firewall unreachable! Letting {site} ({target_ip}) through UNFILTERED")
        banner = """
        <div style="background-color: orange; color: black; padding: 10px; text-align: center; font-family: Arial;">
            ⚠️ Vulcan Firewall is DOWN - this connection was not inspected! 
        </div>
        """
    else:
        print(f"[SERVER] Firewall ALLOWED access to {site} ({target_ip})")
        banner = ""

    # If it's the Llama site, show the fun webpage!
    if site == "llamallama.com":
        return banner + render_llama_website()

    return f"{banner}<h3>Welcome to {site}</h3><a href='/'>Go Back</a>{MARIO_GIF_HTML}", 200

def render_llama_website():
    return """
    <body style="background-color: #ffb3ba; text-align: center; font-family: 'Comic Sans MS', cursive;">
        <h1 style="color: #ba1a49;">Welcome to LlamaLlama.com! 🦙</h1>
        <p>The best place on the internet!</p>
        <pre style="font-size: 20px;">
           //
          //
       __//__
      /      \\
      |  0 0  |
      |   U   |
       \\____/
        |  |
        |  |
        </pre>
        <br>
        <a href="/">Close Tab</a>
    </body>
    """

if __name__ == '__main__':
    print(f"[SERVER] Starting web server on port {SERVER_PORT}...")
    app.run(host=SERVER_IP, port=SERVER_PORT)
