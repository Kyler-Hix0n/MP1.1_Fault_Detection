import socket
import datetime

# fun and joyous color codes
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

#Config params
MONITOR_PORT = 8000
TIMEOUT_WIN = 4.0           
MAX_MISSED_BEATS = 3

def run_monitor():
    # Setting up UDP for heartbeat
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", MONITOR_PORT))
    sock.settimeout(TIMEOUT_WIN)

    missed_beats = 0
    server_up = False

    print(f"🛡️ {GREEN}[{datetime.datetime.now()}] Vulcan Monitor initalized on port {MONITOR_PORT}.{RESET}")
    
    while True:
        try:

            data, addr = sock.recvfrom(1024)

            if data == b"HEARTBEAT":
                if not server_up:
                    print(f"🔌 {GREEN}[{datetime.datetime.now()}] Display Connection: Established with {addr}{RESET}")
                    server_up = True
                
                print(f"🟢 {GREEN}[{datetime.datetime.now()}] HEARTBEAT Status: Received - SERVER IS NOW ACTIVE! 💓{RESET}")
                missed_beats = 0
            
        except (socket.timeout, ConnectionResetError):
            missed_beats += 1
            print(f"⚠️ {YELLOW}[{datetime.datetime.now()}] Warning: Missed beat {missed_beats}/{MAX_MISSED_BEATS}{RESET}")

            if missed_beats >= MAX_MISSED_BEATS:
                if server_up:

                    #display the discontinued Connection
                    print(f"🚨 {RED}[{datetime.datetime.now()}] ALERT: Discontinued connection! Fault detected.{RESET}")
                    server_up = False
                else:
                    print(f"[{datetime.datetime.now()}] Status: Server is currently unreachable. Waiting...")

                #resetting counter to prevent infinite log spam
                missed_beats = 0


if __name__ == "__main__":
    run_monitor()



