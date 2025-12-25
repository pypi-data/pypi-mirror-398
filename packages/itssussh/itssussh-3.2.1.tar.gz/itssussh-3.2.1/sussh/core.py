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
import atexit

PROFILE_FILE = os.path.expanduser("~/.sussh_profiles.json")
OLD_TTY = None
stdout_lock = threading.Lock()
stop_event = threading.Event()

def _restore_tty():
    global OLD_TTY
    if OLD_TTY:
        try:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, OLD_TTY)
        except:
            pass
    os.system('stty sane')

atexit.register(_restore_tty)

def load_profiles():
    if not os.path.exists(PROFILE_FILE): return {}
    try:
        with open(PROFILE_FILE, 'r') as f: return json.load(f)
    except: return {}

def save_profile(name, target, token):
    data = load_profiles()
    data[name] = {"target": target, "token": token}
    with open(PROFILE_FILE, 'w') as f: json.dump(data, f)
    try: os.chmod(PROFILE_FILE, 0o600)
    except: pass
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
    target_clean = target.replace("https://", "").replace("http://", "")
    user, host = target_clean.split("@") if "@" in target_clean else ("root", target_clean)
    
    ws_scheme = "wss" if "zeabur.app" in host or "railway.app" in host else "ws"
    url = f"{ws_scheme}://{host}/sussh"
    
    headers = {
        "X-SVPS-TOKEN": token,
        "X-SVPS-USER": user
    }

    try:
        ws = websocket.create_connection(
            url, 
            header=headers, 
            sslopt={"cert_reqs": ssl.CERT_NONE},
            timeout=10
        )
        return ws
    except websocket.WebSocketBadStatusException as e:
        if e.status_code == 429:
            print("\n[!] SERVER BUSY: User lain sedang aktif.")
        elif e.status_code == 403:
            print("\n[!] ACCESS DENIED: Password Salah.")
        else:
            print(f"\n[!] Gagal: Status {e.status_code}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[!] Error Koneksi: {e}")
        sys.exit(1)

def _input_listener(ws):
    fd = sys.stdin.fileno()
    while not stop_event.is_set():
        try:
            r, _, _ = select.select([fd], [], [], 0.05)
            if r:
                data = os.read(fd, 8192)
                if not data: break
                ws.send_binary(data)
        except:
            break

def start_shell(target, token):
    global OLD_TTY
    ws = create_connection(target, token)
    print(f"[*] Connected to {target} (ULTRA 6.6)")

    OLD_TTY = termios.tcgetattr(sys.stdin)
    
    try:
        tty.setraw(sys.stdin.fileno())
        t = threading.Thread(target=_input_listener, args=(ws,))
        t.daemon = True
        t.start()

        while not stop_event.is_set():
            try:
                opcode, data = ws.recv_data()
                if opcode == websocket.ABNF.OPCODE_CLOSE:
                    break
                
                if data:
                    with stdout_lock:
                        sys.stdout.write(data.decode('utf-8', errors='ignore'))
                        sys.stdout.flush()
            except:
                break
    finally:
        stop_event.set()
        _restore_tty()
        ws.close()
        print("\r\n[*] Connection closed. Terminal restored.\n")

def start_upload(target, token):
    print("--- Ultra Fast File Upload ---")
    local_path = input("Local path: ").strip()
    if not os.path.exists(local_path):
        print("Error: File not found.")
        return
    
    remote_path = input("Remote path: ").strip() or os.path.basename(local_path)

    try:
        ws = create_connection(target, token)
        print(f"[*] Uploading...")
        with open(local_path, "rb") as f:
            ws.send(f"> {remote_path}\n")
            chunk_size = 1024 * 32 
            while True:
                chunk = f.read(chunk_size)
                if not chunk: break
                b64_chunk = base64.b64encode(chunk).decode()
                ws.send(f"echo -n '{b64_chunk}' | base64 -d >> {remote_path}\n")
                sys.stdout.write("#")
                sys.stdout.flush()
        print(f"\n[+] Upload Selesai.")
        ws.close()
    except Exception as e:
        print(f"\nError: {e}")

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

    if not p_list:
        print("Belum ada profil.")
        c = 'n'
    else:
        print("\nSelect SVPS Target:")
        for i, name in enumerate(p_list):
            print(f" {i+1}) {name} ({profiles[name]['target']})")
        print(" N) New Profile | U) Quick Upload")
        c = input("> ").lower().strip()

    if c == 'n':
        t = input("Host (user@host): ")
        if not t: return
        pw = getpass.getpass("Pass: ")
        if input("Simpan profil? (y/n): ").lower() == 'y':
            save_profile(input("Nama Profil: "), t, pw)
        start_shell(t, pw)
    elif c == 'u':
        t = input("Target Host: ")
        start_upload(t, getpass.getpass("Pass: "))
    elif c.isdigit() and 1 <= int(c) <= len(p_list):
        n = p_list[int(c)-1]
        start_shell(profiles[n]['target'], profiles[n]['token'])

if __name__ == "__main__":
    main()

