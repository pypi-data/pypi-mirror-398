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
import signal
from datetime import datetime

VERSION = "4.2.1-FIX"
PROFILE_FILE = os.path.expanduser("~/.sussh_profiles.json")
OLD_TTY = None
stdout_lock = threading.Lock()
stop_event = threading.Event()

LICENSE_TEMPLATES = {
    "MIT": """MIT License
Copyright (c) {year} Eternals

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.""",
    
    "Apache 2.0": """Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.""",

    "GNU GPLv3": """This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.""",

    "Unlicense": """This is free and unencumbered software released into the public domain.
Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means."""
}

def ensure_project_metadata():
    """Memastikan README.md dan LICENSE tersedia sesuai aturan Fiber."""
    print("\n[*] Checking Project Integrity (Fiber)...")
    
    readme_path = "README.md"
    current_dir = os.path.basename(os.getcwd())
    
    if not os.path.exists(readme_path) or os.path.getsize(readme_path) == 0:
        print("    [+] README.md missing or empty. Generating default...")
        content = (
            f"# {current_dir}\n\n"
            "Project ini di upload melalui **fiber**.\n\n"
            "**Author:** Eternals\n"
            "**Date:** " + datetime.now().strftime("%Y-%m-%d")
        )
        with open(readme_path, "w") as f:
            f.write(content)
    else:
        print("    [OK] README.md exists.")

    license_path = "LICENSE"
    if not os.path.exists(license_path):
        print("    [!] LICENSE is missing! You must choose one:")
        keys = list(LICENSE_TEMPLATES.keys())
        for i, key in enumerate(keys):
            print(f"        {i+1}) {key}")
        
        while True:
            try:
                choice = input("    > Select License (Number): ").strip()
                if not choice.isdigit(): continue
                idx = int(choice) - 1
                if 0 <= idx < len(keys):
                    selected = keys[idx]
                    year = datetime.now().year
                    content = LICENSE_TEMPLATES[selected].format(year=year)
                    with open(license_path, "w") as f:
                        f.write(content)
                    print(f"    [+] Created LICENSE ({selected})")
                    break
            except KeyboardInterrupt:
                sys.exit(0)
            except:
                pass
    else:
        print("    [OK] LICENSE exists.")
    print("-" * 40)

def _restore_tty():
    global OLD_TTY
    if OLD_TTY:
        try:
            termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, OLD_TTY)
        except:
            pass
    sys.stdout.write("\033[?25h\033[0m")
    sys.stdout.flush()

def load_profiles():
    if not os.path.exists(PROFILE_FILE):
        return {}
    try:
        with open(PROFILE_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_profile(name, target, token, session):
    data = load_profiles()
    data[name] = {"target": target, "token": token, "session": session}
    with open(PROFILE_FILE, "w") as f:
        json.dump(data, f)
    try:
        os.chmod(PROFILE_FILE, 0o600)
    except:
        pass

def resolve_auth(target, provided):
    token = provided or os.getenv("PASS")
    if not token:
        token = getpass.getpass(f"{target}'s password: ")
    return token

def create_connection(target, token, session):
    target = target.replace("https://", "").replace("http://", "")
    user, host = target.split("@") if "@" in target else ("root", target)
    scheme = "wss" if any(x in host for x in ["zeabur.app", "railway.app", "onrender.com", "herokuapp.com"]) else "ws"
    url = f"{scheme}://{host}/sussh"
    headers = {
        "X-SVPS-TOKEN": token,
        "X-SVPS-USER": user,
        "X-SESSION-ID": session
    }
    ws = websocket.create_connection(
        url,
        header=headers,
        sslopt={"cert_reqs": ssl.CERT_NONE},
        timeout=10
    )
    ws.settimeout(0.2)
    return ws

def _input_listener(ws):
    fd = sys.stdin.fileno()
    while not stop_event.is_set():
        try:
            r, _, _ = select.select([fd], [], [], 0.1)
            if not r:
                continue
            
            data = os.read(fd, 4096)
            
            if b"\x1c" in data: 
                print("\r\n[!] Force Quit Triggered.")
                stop_event.set()
                ws.close()
                os._exit(0)
            
            if not data:
                stop_event.set()
                break
            
            ws.send_binary(data)
            
        except OSError:
            pass
        except Exception:
            stop_event.set()
            break

def start_shell(target, token, session):
    global OLD_TTY
    stop_event.clear()
    
    prev_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)

    try:
        ws = create_connection(target, token, session)
        sys.stdout.write("\033c")
        sys.stdout.write(f"\r\n[SVPS] Connected. Press 'Ctrl+\\' to force quit.\r\n")
        sys.stdout.flush()
        
        OLD_TTY = termios.tcgetattr(sys.stdin)
        tty.setraw(sys.stdin.fileno())
        
        t = threading.Thread(target=_input_listener, args=(ws,), daemon=True)
        t.start()
        
        while not stop_event.is_set():
            try:
                opcode, data = ws.recv_data()
                if opcode == websocket.ABNF.OPCODE_CLOSE:
                    break
                if opcode == websocket.ABNF.OPCODE_PING:
                    ws.pong(data)
                    continue
                if data:
                    with stdout_lock:
                        sys.stdout.write(data.decode("utf-8", "ignore"))
                        sys.stdout.flush()
            except websocket.WebSocketTimeoutException:
                continue
            except Exception:
                break
    except Exception as e:
        print(f"Connection Failed: {e}")
    finally:
        stop_event.set()
        try:
            ws.close()
        except:
            pass
        _restore_tty()
        signal.signal(signal.SIGINT, prev_handler)
        print("\n[SVPS] Session Closed.")

def start_upload(target, token):
    ensure_project_metadata()
    
    lp = input("Local path: ").strip()
    if not os.path.exists(lp):
        print("File not found.")
        return
    rp = input("Remote path (opt): ").strip() or os.path.basename(lp)
    ws = create_connection(target, token, "upload")
    ws.send(f"> {rp}\n")
    print("Uploading...", end="", flush=True)
    try:
        with open(lp, "rb") as f:
            while True:
                chunk = f.read(49152)
                if not chunk:
                    break
                ws.send(f"echo -n '{base64.b64encode(chunk).decode()}' | base64 -d >> {rp}\n")
                time.sleep(0.001)
        print("\nDone")
    except Exception as e:
        print(f"\nUpload failed: {e}")
    finally:
        ws.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("target", nargs="?")
    parser.add_argument("-p", "--password")
    parser.add_argument("-s", "--session", default="main")
    parser.add_argument("-u", "--upload", action="store_true")
    parser.add_argument("-v", "--version", action="version", version=f"Sussh {VERSION}")
    args = parser.parse_args()

    if args.target:
        token = resolve_auth(args.target, args.password)
        if args.upload:
            start_upload(args.target, token)
        else:
            start_shell(args.target, token, args.session)
        return

    profiles = load_profiles()
    keys = list(profiles.keys())

    if keys:
        for i, k in enumerate(keys):
            print(f"{i+1}) {k}")
        print("N) New | U) Upload")
        c = input("> ").strip().lower()
    else:
        c = "n"

    if c == "n":
        t = input("Host: ").strip()
        if not t:
            return
        pw = getpass.getpass("Pass: ")
        sess = input("Session [main]: ").strip() or "main"
        if input("Save? (y/n): ").lower() == "y":
            save_profile(input("Name: "), t, pw, sess)
        start_shell(t, pw, sess)
    elif c == "u":
        t = input("Host: ").strip()
        start_upload(t, getpass.getpass("Pass: "))
    elif c.isdigit() and 1 <= int(c) <= len(keys):
        p = profiles[keys[int(c) - 1]]
        start_shell(p["target"], p["token"], p.get("session", "main"))

if __name__ == "__main__":
    main()

