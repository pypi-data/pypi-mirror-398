import sys
import os
import time
import json
import argparse
import threading
import ssl
import select
import termios
import tty
import websocket
import getpass
import base64

# --- CONFIGURATION ---
PROFILE_FILE = os.path.expanduser("~/.sussh_profiles.json")

# --- UTILITIES ---
def load_profiles():
    if not os.path.exists(PROFILE_FILE): return {}
    try:
        with open(PROFILE_FILE, 'r') as f: return json.load(f)
    except: return {}

def save_profile(name, target, token):
    data = load_profiles()
    data[name] = {"target": target, "token": token}
    with open(PROFILE_FILE, 'w') as f: json.dump(data, f)
    print(f"Profile '{name}' saved.")

def resolve_auth(target, provided_pass=None):
    token = provided_pass or os.getenv("PASS")
    if not token:
        try:
            token = getpass.getpass(f"Password for {target}: ")
        except KeyboardInterrupt:
            print()
            sys.exit(1)
    return token

def create_connection(target, token):
    user, host = target.split("@") if "@" in target else ("root", target)
    ws_scheme = "wss" if "https" in host or "app" in host else "ws"
    host_clean = host.replace("https://", "").replace("http://", "")
    url = f"{ws_scheme}://{host_clean}/sussh"
    headers = {"X-SVPS-TOKEN": token, "X-SVPS-USER": user}
    
    try:
        ws = websocket.WebSocket()
        ws.connect(url, header=headers, sslopt={"cert_reqs": ssl.CERT_NONE})
        return ws
    except Exception as e:
        print(f"Connection error: {e}")
        sys.exit(1)

# --- SSH SHELL MODE ---
stop_event = threading.Event()
OLD_TTY = None

def _restore_tty():
    if OLD_TTY:
        try: termios.tcsetattr(sys.stdin, termios.TCSADRAIN, OLD_TTY)
        except: pass
    os.system('stty sane')

def _input_listener(ws):
    """
    FIXED: Membaca input secara chunk (biar bisa paste)
    DAN mengubahnya menjadi STRING (decode) sebelum dikirim.
    """
    fd = sys.stdin.fileno()
    while not stop_event.is_set():
        # Cek apakah ada input
        r, _, _ = select.select([fd], [], [], 0.1)
        if r:
            try:
                # BACA 4KB SEKALIGUS (Handle Paste)
                data = os.read(fd, 4096)
                if not data: break
                
                # --- INI FIX PENTINGNYA ---
                # Convert Bytes -> String biar server gak bingung
                text_data = data.decode('utf-8', errors='ignore')
                ws.send(text_data)
                
            except OSError:
                pass
            except Exception:
                break

def start_shell(target, token):
    global OLD_TTY
    ws = create_connection(target, token)
    
    print(f"Connected to {target}")
    
    OLD_TTY = termios.tcgetattr(sys.stdin)
    try:
        tty.setraw(sys.stdin.fileno())
        
        t = threading.Thread(target=_input_listener, args=(ws,))
        t.daemon = True
        t.start()
        
        while True:
            try:
                data = ws.recv()
                if not data: break
                sys.stdout.write(data)
                sys.stdout.flush()
            except: break
            
    except Exception:
        pass
    finally:
        stop_event.set()
        _restore_tty()
        ws.close()
        print(f"\nConnection closed.")

# --- UPLOAD MODE ---
def start_upload(target, token):
    print("--- File Upload ---")
    local_path = input("Local path: ").strip()
    if not os.path.exists(local_path):
        print(f"Error: Not found.")
        return
    remote_path = input("Remote path (opt): ").strip() or os.path.basename(local_path)

    try:
        ws = create_connection(target, token)
        print("Uploading...")
        with open(local_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode('utf-8')
        ws.send(f"echo '{b64}' | base64 -d > {remote_path}\n")
        time.sleep(1)
        ws.send(f"ls -lh {remote_path}\n")
        time.sleep(0.5)
        print("Done.")
        ws.close()
    except Exception as e:
        print(f"Error: {e}")

# --- MAIN ---
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("target", nargs="?")
    parser.add_argument("-p", "--password")
    args = parser.parse_args()

    if args.target:
        token = resolve_auth(args.target, args.password)
        start_shell(args.target, token)
        return

    profiles = load_profiles()
    p_list = list(profiles.keys())
    
    print("Select:")
    for i, name in enumerate(p_list):
        print(f" {i+1}) {name}")
    print(" N) New")
    print(" U) Upload")
    
    c = input("> ").lower().strip()
    if c == 'n':
        t = input("Host: ")
        if not t: return
        pw = getpass.getpass("Pass: ")
        if input("Save? y/n: ") == 'y': save_profile(input("Name: "), t, pw)
        start_shell(t, pw)
    elif c == 'u':
        t = input("Host: ")
        start_upload(t, getpass.getpass("Pass: "))
    elif c.isdigit() and 1 <= int(c) <= len(p_list):
        n = p_list[int(c)-1]
        start_shell(profiles[n]['target'], profiles[n]['token'])

if __name__ == "__main__":
    try: main()
    except: _restore_tty()

