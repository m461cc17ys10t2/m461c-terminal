"""
M461C Terminal - made by m461c c17y
100% Python, no other languages.
Run it with:  python m461c_terminal.py
"""

import os
import threading
import hashlib
import sys
import ast
import json
import time
import shlex
import random
import secrets
import string
import shutil
import operator
import webbrowser
import platform
import subprocess
from datetime import datetime

# ----------------------------------------------------------------------
# SETTINGS / STATE
# ----------------------------------------------------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "m461c_config.json")

DEFAULT_CONFIG = {"prompt": "m461c", "color": "magenta"}

VERSION = "1.4"
SUB_URL = "https://www.youtube.com/@kingfigueredo?sub_confirmation=1"
NOTES_PATH = os.path.join(SCRIPT_DIR, "m461c_notes.txt")
USERS_PATH = os.path.join(SCRIPT_DIR, "m461c_users.json")
CHAT_PATH = os.path.join(SCRIPT_DIR, "m461c_chat.json")
DM_PATH = os.path.join(SCRIPT_DIR, "m461c_dms.json")
CODE_DIR = os.path.join(SCRIPT_DIR, "m461c_code")

FOUNDER_USERNAME = "m461c c17y"
FOUNDER_PASSWORD_HASH = hashlib.sha256("0596929gf".encode()).hexdigest()

COLORS = {
    "red": "\033[91m",
    "green": "\033[92m",
    "yellow": "\033[93m",
    "blue": "\033[94m",
    "magenta": "\033[95m",
    "cyan": "\033[96m",
    "white": "\033[97m",
}
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_PATH, "r") as f:
            cfg.update(json.load(f))
    except (OSError, ValueError):
        pass
    cfg.pop("subscribed", None)
    return cfg


def save_users(users):
    try:
        with open(USERS_PATH, "w") as f:
            json.dump(users, f, indent=2)
    except OSError as e:
        print(f"[ERROR] Could not save users: {e}")


def load_users():
    users = {}
    if os.path.exists(USERS_PATH):
        try:
            with open(USERS_PATH, "r") as f:
                users = json.load(f)
        except (OSError, ValueError):
            users = {}

    if FOUNDER_USERNAME not in users:
        users[FOUNDER_USERNAME] = {
            "password": FOUNDER_PASSWORD_HASH,
            "role": "FOUNDER / OWNER / ADMIN",
            "created_at": "System Genesis",
            "last_login": "Never",
            "banned": False,
            "friends": [],
            "notifications": [],
        }
        save_users(users)
    else:
        # Ensure new schema fields exist for older users
        updated = False
        if users[FOUNDER_USERNAME].get("role") != "FOUNDER / OWNER / ADMIN":
            users[FOUNDER_USERNAME]["role"] = "FOUNDER / OWNER / ADMIN"
            users[FOUNDER_USERNAME]["banned"] = False
            updated = True
        for uname in users:
            if "friends" not in users[uname]:
                users[uname]["friends"] = []
                updated = True
            if "notifications" not in users[uname]:
                users[uname]["notifications"] = []
                updated = True
        if updated:
            save_users(users)

    return users


def save_config():
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(state["config"], f, indent=2)
    except OSError as e:
        print(f"[ERROR] Could not save settings: {e}")


load_users()

state = {
    "devmode": False,
    "is_admin": False,
    "is_mod": False,
    "history": [],
    "start": time.time(),
    "config": load_config(),
    "current_user": None,
    "announcement": None,
}


def enable_ansi():
    if os.name == "nt":
        os.system("")


def accent():
    return COLORS.get(state["config"]["color"], COLORS["magenta"])


# ----------------------------------------------------------------------
# NORMAL COMMANDS
# ----------------------------------------------------------------------
def banner():
    c = accent()
    print(f"""{c}{BOLD}
=========================================================
        W E L C O M E   T O   T H E
        M 4 6 1 C   T E R M I N A L
        made by m461c c17y
========================================================={RESET}
""")
    if state.get("announcement"):
        print(f"{c}{BOLD}[ANNOUNCEMENT]{RESET} {state['announcement']}\n")
    print(f"Type {BOLD}/help{RESET} to see all the commands.\n")


def cmd_help(args):
    c = accent()
    print(f"\n{c}{BOLD}=== M461C TERMINAL HELP ==={RESET}")

    print(f"\n{BOLD}SOCIAL & CHAT COMMANDS{RESET} (requires login)")
    print(f"  {c}/social <username>    {RESET} Send a friend request to a user")
    print(f"  {c}/notifications        {RESET} View notifications & accept requests")
    print(f"  {c}/dm <username>        {RESET} Open private 1-on-1 chat with a friend")
    print(f"  {c}/chat                 {RESET} Open public live social chatroom")

    print(f"\n{BOLD}NORMAL COMMANDS{RESET} (always available)")
    for name, (_, desc, access) in COMMANDS.items():
        if access == "normal" and name not in ("social", "notifications", "dm", "chat"):
            print(f"  {c}/{name:<22}{RESET} {desc}")

    print(f"\n{BOLD}DEV MODE COMMANDS{RESET} (turn on with /devmode /on)")
    for name, (_, desc, access) in COMMANDS.items():
        if access == "dev":
            print(f"  {c}/{name:<22}{RESET} {desc}")

    if state["is_admin"] or state["is_mod"]:
        print(f"\n{c}{BOLD}MODERATOR / ADMIN COMMANDS{RESET}")
        for name, (_, desc, access) in COMMANDS.items():
            if access == "admin":
                print(f"  {c}/{name:<22}{RESET} {desc}")

    print(f"\n{BOLD}TERMINAL COMMANDS{RESET} (no slash needed)")
    print("  All standard terminal commands (dir/ls, cd, pwd, python, etc.) work as well.")
    print(f"\nDev mode: {'ON' if state['devmode'] else 'OFF'}  |  Admin/Mod: {'ON' if (state['is_admin'] or state['is_mod']) else 'OFF'}\n")


def cmd_sub(args):
    print(f"{accent()}[SUB] Opening the subscribe page...{RESET}")
    print(f"If it doesn't open, go to: {SUB_URL}")
    try:
        webbrowser.open(SUB_URL)
    except Exception:
        pass


def cmd_clear(args):
    os.system("cls" if os.name == "nt" else "clear")
    banner()


def cmd_devmode(args):
    choice = args[0].lower().lstrip("/") if args else ""
    if choice not in ("on", "off"):
        print(f"Dev mode is {'ON' if state['devmode'] else 'OFF'}. Usage: /devmode /on  or  /devmode /off")
        return
    state["devmode"] = choice == "on"
    if state["devmode"]:
        print(f"{accent()}[DEVMODE] ON - dev commands unlocked. Type /help to see them.{RESET}")
    else:
        print("[DEVMODE] OFF")


def cmd_welcome(args):
    banner()


def cmd_time(args):
    print(datetime.now().strftime("%A, %B %d %Y  %I:%M:%S %p"))


def cmd_uptime(args):
    secs = int(time.time() - state["start"])
    h, rem = divmod(secs, 3600)
    m, s = divmod(rem, 60)
    print(f"Terminal has been running for {h}h {m}m {s}s")


def cmd_history(args):
    if not state["history"]:
        print("No history yet.")
    for i, line in enumerate(state["history"], 1):
        print(f"  {i:>3}  {line}")


def cmd_whoami(args):
    try:
        sys_user = os.getlogin()
    except OSError:
        sys_user = os.environ.get("USER") or os.environ.get("USERNAME") or "unknown"
    users = load_users()
    curr = state["current_user"]
    if curr and curr in users:
        role = users[curr].get("role", "Member")
        logged_in = f"{curr} ({role})"
    else:
        logged_in = "Not logged in"
    print(f"System User: {sys_user}  |  Account: {logged_in}  |  Dev mode: {'ON' if state['devmode'] else 'OFF'}")


def cmd_about(args):
    print("M461C Terminal - made by m461c c17y (magic, get it?)")
    print(f"Running on Python {platform.python_version()} ({platform.system()})")


# Safe calculator (no eval)
_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _calc(node):
    if isinstance(node, ast.Expression):
        return _calc(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        left, right = _calc(node.left), _calc(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 1000:
            raise ValueError("exponent too big")
        return _OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_calc(node.operand))
    raise ValueError("unsupported expression")


def cmd_calc(args):
    if not args:
        print("Usage: /calc 2 + 2 * 5")
        return
    try:
        print("=", _calc(ast.parse(" ".join(args), mode="eval")))
    except ZeroDivisionError:
        print("[ERROR] Cannot divide by zero.")
    except (ValueError, SyntaxError):
        print("[ERROR] I can only do numbers with + - * / // % **")


def cmd_echo(args):
    print(" ".join(args))


def cmd_pwd(args):
    print(os.getcwd())


def cmd_ls(args):
    path = args[0] if args else "."
    try:
        for entry in sorted(os.listdir(path), key=str.lower):
            full = os.path.join(path, entry)
            print(f"  {entry}/" if os.path.isdir(full) else f"  {entry}")
    except OSError as e:
        print(f"[ERROR] {e}")


def cmd_coinflip(args):
    print(random.choice(["Heads", "Tails"]))


def cmd_dice(args):
    sides = 6
    if args:
        try:
            sides = int(args[0])
            if sides < 2:
                raise ValueError
        except ValueError:
            print("Usage: /dice [sides]   Example: /dice 20")
            return
    print(f"Rolled a d{sides}: {random.randint(1, sides)}")


def cmd_timer(args):
    try:
        seconds = int(args[0])
        if seconds < 1:
            raise ValueError
    except (IndexError, ValueError):
        print("Usage: /timer <seconds>   Example: /timer 30")
        return
    try:
        for left in range(seconds, 0, -1):
            print(f"\r  Time left: {left:>4}s ", end="", flush=True)
            time.sleep(1)
        print(f"\r{accent()}  Time's up!        {RESET}")
    except KeyboardInterrupt:
        print("\n[INFO] Timer cancelled.")


def cmd_note(args):
    if not args:
        print("Usage: /note <text>   (see them with /notes)")
        return
    author = state["current_user"] or "guest"
    try:
        with open(NOTES_PATH, "a") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M')}] ({author}) {' '.join(args)}\n")
        print("[NOTE] Saved.")
    except OSError as e:
        print(f"[ERROR] {e}")


def cmd_notes(args):
    try:
        with open(NOTES_PATH, "r") as f:
            text = f.read().strip()
        print(text if text else "No notes yet.")
    except OSError:
        print("No notes yet. Add one with /note <text>")


def cmd_passgen(args):
    length = 16
    if args:
        try:
            length = int(args[0])
            if not 4 <= length <= 128:
                raise ValueError
        except ValueError:
            print("Usage: /passgen [length 4-128]")
            return
    chars = string.ascii_letters + string.digits + "!@#$%^&*-_"
    print("".join(secrets.choice(chars) for _ in range(length)))


def cmd_signup(args):
    print(f"{accent()}=== CREATE NEW ACCOUNT ==={RESET}")
    username = input("Enter username: ").strip()
    if not username:
        print("[ERROR] Username cannot be empty.")
        return
    users = load_users()
    if username in users:
        print("[ERROR] Username already exists. Try /login")
        return
    password = input("Enter password: ").strip()
    if len(password) < 4:
        print("[ERROR] Password must be at least 4 characters long.")
        return

    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    users[username] = {
        "password": pwd_hash,
        "role": "Member",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "last_login": "Never",
        "banned": False,
        "friends": [],
        "notifications": [],
    }
    save_users(users)
    print(f"[SUCCESS] Account '{username}' created successfully! Log in with /login")


def cmd_login(args):
    print(f"{accent()}=== LOGIN ==={RESET}")
    username = input("Enter username: ").strip()
    if not username:
        print("[ERROR] Username cannot be empty.")
        return
    users = load_users()
    if username not in users:
        print("[ERROR] Username not found. Create an account with /signup first.")
        return
    
    if users[username].get("banned", False):
        print("[ERROR] This account has been banned from the terminal.")
        return

    password = input("Enter password: ").strip()
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()

    if users[username]["password"] == pwd_hash:
        state["current_user"] = username
        users[username]["last_login"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_users(users)

        role = users[username].get("role", "Member")
        role_upper = role.upper()
        if username == FOUNDER_USERNAME or "ADMIN" in role_upper or "OWNER" in role_upper:
            state["is_admin"] = True
            state["is_mod"] = True
            state["devmode"] = True
            print(f"\n{accent()}{BOLD}[FOUNDER / OWNER / ADMIN ACCESS GRANTED]{RESET}")
            print(f"{accent()}Welcome back, {username}! Dev mode & all Owner/Admin commands unlocked.{RESET}")
        elif "MOD" in role_upper:
            state["is_mod"] = True
            state["is_admin"] = False
            print(f"\n{accent()}{BOLD}[MODERATOR ACCESS GRANTED]{RESET}")
            print(f"{accent()}Welcome back, {username}! Moderator privileges active.{RESET}")
        else:
            state["is_admin"] = False
            state["is_mod"] = False
            print(f"[SUCCESS] Welcome back, {username}!")
    else:
        print("[ERROR] Incorrect password.")


def cmd_signout(args):
    if not state["current_user"]:
        print("[INFO] You are not logged into any account.")
        return
    print(f"[INFO] Signed out from account: {state['current_user']}")
    state["current_user"] = None
    state["is_admin"] = False
    state["is_mod"] = False
    state["devmode"] = False
    print("[INFO] Permissions locked.")


def cmd_version(args):
    print(f"M461C Terminal v{VERSION}")


def cmd_exit(args):
    print("Goodbye from the M461C Terminal!")
    sys.exit(0)


# ----------------------------------------------------------------------
# SOCIAL, NOTIFICATIONS & DM SYSTEMS
# ----------------------------------------------------------------------
def cmd_social(args):
    if not state["current_user"]:
        print("[ERROR] You must be logged in to send friend requests! Use /login.")
        return
    if not args:
        print("Usage: /social <username>")
        return
    
    target = " ".join(args).strip()
    curr = state["current_user"]
    if target == curr:
        print("[ERROR] You cannot add yourself as a friend.")
        return

    users = load_users()
    if target not in users:
        print(f"[ERROR] User '{target}' does not exist.")
        return
    
    if target in users[curr].get("friends", []):
        print(f"[INFO] You and {target} are already friends!")
        return

    # Check if request already pending
    for notif in users[target].get("notifications", []):
        if notif.get("from") == curr and notif.get("type") == "friend_request":
            print(f"[INFO] Friend request already sent to {target}.")
            return

    # Add notification to target user
    notif_data = {
        "id": secrets.token_hex(4),
        "type": "friend_request",
        "from": curr,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "text": f"{curr} sent you a friend request."
    }
    users[target]["notifications"].append(notif_data)
    save_users(users)
    print(f"[SUCCESS] Friend request sent to {target}!")


def cmd_notifications(args):
    if not state["current_user"]:
        print("[ERROR] You must be logged in to view notifications! Use /login.")
        return

    users = load_users()
    curr = state["current_user"]
    notifs = users[curr].get("notifications", [])

    c = accent()
    print(f"\n{c}{BOLD}=== YOUR NOTIFICATIONS ({len(notifs)}) ==={RESET}")
    if not notifs:
        print("No new notifications.")
        return

    for idx, notif in enumerate(notifs, 1):
        print(f"  {idx}. [{notif.get('time', '')}] {notif.get('text', '')}")

    print("\nOptions:")
    print("  Accept/Decline friend requests by typing:  accept <number>  or  decline <number>")
    print("  Or press Enter to go back.")
    
    choice = input(f"{c}[NOTIFS] {curr} > {RESET}").strip().lower()
    if not choice:
        return

    parts = choice.split()
    if len(parts) == 2 and parts[0] in ("accept", "decline"):
        try:
            num = int(parts[1])
            if not 1 <= num <= len(notifs):
                raise ValueError
        except ValueError:
            print("[ERROR] Invalid notification number.")
            return

        target_notif = notifs[num - 1]
        if target_notif.get("type") == "friend_request":
            sender = target_notif.get("from")
            if parts[0] == "accept":
                # Add each other to friends list
                if sender not in users[curr]["friends"]:
                    users[curr]["friends"].append(sender)
                if sender in users and curr not in users[sender]["friends"]:
                    users[sender]["friends"].append(curr)
                print(f"[SUCCESS] You are now friends with {sender}!")
            else:
                print(f"[INFO] Declined friend request from {sender}.")
            
            # Remove notification
            users[curr]["notifications"].pop(num - 1)
            save_users(users)
        else:
            print("[INFO] Notification acknowledged.")


def load_dms():
    if not os.path.exists(DM_PATH):
        return {}
    try:
        with open(DM_PATH, "r") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_dms(dms):
    try:
        with open(DM_PATH, "w") as f:
            json.dump(dms, f, indent=2)
    except OSError as e:
        print(f"[ERROR] Could not save DMs: {e}")


def cmd_dm(args):
    if not state["current_user"]:
        print("[ERROR] You must be logged in to use private DMs! Use /login.")
        return
    if not args:
        print("Usage: /dm <username>")
        return

    friend = " ".join(args).strip()
    curr = state["current_user"]

    users = load_users()
    if friend not in users:
        print(f"[ERROR] User '{friend}' does not exist.")
        return

    if friend not in users[curr].get("friends", []):
        print(f"[ERROR] You must be friends with '{friend}' before sending DMs! Use /social {friend}")
        return

    # Create a consistent room key between both users
    room_key = "__".join(sorted([curr, friend]))

    c = accent()
    print(f"\n{c}{BOLD}=== PRIVATE CHATROOM WITH {friend} ==={RESET}")
    print("Type /exit or /quit to leave chat.\n" + "-" * 50)

    chat_active = True
    last_count = 0

    def dm_listener():
        nonlocal last_count
        all_dms = load_dms()
        room_msgs = all_dms.get(room_key, [])
        for msg in room_msgs:
            print(f"{DIM}[{msg.get('time', '')}]{RESET} {c}{msg.get('sender', '')}{RESET}: {msg.get('text', '')}")
        last_count = len(room_msgs)
        print(f"{c}[DM:{friend}] {curr} > {RESET}", end="", flush=True)

        while chat_active:
            time.sleep(0.4)
            if not chat_active:
                break
            try:
                all_dms = load_dms()
                room_msgs = all_dms.get(room_key, [])
                if len(room_msgs) > last_count:
                    sys.stdout.write("\r\033[K")
                    for msg in room_msgs[last_count:]:
                        print(f"{DIM}[{msg.get('time', '')}]{RESET} {c}{msg.get('sender', '')}{RESET}: {msg.get('text', '')}")
                    last_count = len(room_msgs)
                    print(f"{c}[DM:{friend}] {curr} > {RESET}", end="", flush=True)
            except Exception:
                pass

    t = threading.Thread(target=dm_listener, daemon=True)
    t.start()

    try:
        while chat_active:
            line = input().strip()
            if not line:
                print(f"{c}[DM:{friend}] {curr} > {RESET}", end="", flush=True)
                continue

            if line.lower() in ("/exit", "/quit"):
                chat_active = False
                print("[INFO] Left private chat.")
                break

            all_dms = load_dms()
            if room_key not in all_dms:
                all_dms[room_key] = []

            new_msg = {
                "sender": curr,
                "text": line,
                "time": datetime.now().strftime("%H:%M:%S")
            }
            all_dms[room_key].append(new_msg)
            if len(all_dms[room_key]) > 200:
                all_dms[room_key] = all_dms[room_key][-200:]
            save_dms(all_dms)
            print(f"{c}[DM:{friend}] {curr} > {RESET}", end="", flush=True)
    except (KeyboardInterrupt, EOFError):
        chat_active = False
        print("\n[INFO] Exiting private chat.")


# ----------------------------------------------------------------------
# LIVE PUBLIC CHATROOM SYSTEM
# ----------------------------------------------------------------------
def load_chat():
    if not os.path.exists(CHAT_PATH):
        return []
    try:
        with open(CHAT_PATH, "r") as f:
            return json.load(f)
    except (OSError, ValueError):
        return []


def save_chat(messages):
    try:
        with open(CHAT_PATH, "w") as f:
            json.dump(messages, f, indent=2)
    except OSError as e:
        print(f"[ERROR] Could not save chat: {e}")


def cmd_chat(args):
    if not state["current_user"]:
        print("[ERROR] You must be logged in to enter the live chatroom! Use /login or /signup.")
        return

    users = load_users()
    curr = state["current_user"]
    if users.get(curr, {}).get("banned", False):
        print("[ERROR] You are banned from the chatroom.")
        return

    c = accent()
    print(f"\n{c}{BOLD}=== LIVE PUBLIC SOCIAL CHATROOM ==={RESET}")
    print("Commands inside chat:")
    print("  /exit or /quit  -> leave chat")
    if state["is_admin"] or state["is_mod"]:
        print("  /clear          -> clear all chat messages")
        print("  /ban <user>     -> ban a user from the terminal")
    print("-" * 50)

    chat_active = True
    last_count = 0

    def chat_listener():
        nonlocal last_count
        initial_msgs = load_chat()
        for msg in initial_msgs:
            sender = msg.get("sender", "unknown")
            text = msg.get("text", "")
            timestamp = msg.get("time", "")
            role = msg.get("role", "Member")
            badge = "[OWNER]" if sender == FOUNDER_USERNAME else ("[MOD]" if "MOD" in role.upper() else "")
            print(f"\r{DIM}[{timestamp}]{RESET} {c}{badge}{sender}{RESET}: {text}")
        last_count = len(initial_msgs)
        print(f"{c}[CHAT] {curr} > {RESET}", end="", flush=True)

        while chat_active:
            time.sleep(0.4)
            if not chat_active:
                break

            try:
                fresh_users = load_users()
                if fresh_users.get(curr, {}).get("banned", False):
                    print(f"\n{COLORS['red']}[ERROR] You have been banned from the chatroom/terminal!{RESET}")
                    state["current_user"] = None
                    state["is_admin"] = False
                    state["is_mod"] = False
                    os._exit(0)

                messages = load_chat()
                if len(messages) < last_count:
                    last_count = len(messages)
                elif len(messages) > last_count:
                    sys.stdout.write("\r\033[K")
                    for msg in messages[last_count:]:
                        sender = msg.get("sender", "unknown")
                        text = msg.get("text", "")
                        timestamp = msg.get("time", "")
                        role = msg.get("role", "Member")
                        badge = "[OWNER]" if sender == FOUNDER_USERNAME else ("[MOD]" if "MOD" in role.upper() else "")
                        print(f"{DIM}[{timestamp}]{RESET} {c}{badge}{sender}{RESET}: {text}")
                    last_count = len(messages)
                    print(f"{c}[CHAT] {curr} > {RESET}", end="", flush=True)
            except Exception:
                pass

    t = threading.Thread(target=chat_listener, daemon=True)
    t.start()

    try:
        while chat_active:
            line = input().strip()
            if not line:
                print(f"{c}[CHAT] {curr} > {RESET}", end="", flush=True)
                continue

            if line.lower() in ("/exit", "/quit"):
                chat_active = False
                print("[INFO] Leaving chatroom.")
                break

            if line.startswith("/"):
                parts = line.split()
                cmd = parts[0].lower()
                chat_args = parts[1:]
                fresh_users = load_users()

                if cmd == "/clear" and (state["is_admin"] or state["is_mod"]):
                    save_chat([])
                    last_count = 0
                    print(f"\n{accent()}[CHAT] Chatroom cleared by {curr}.{RESET}\n")
                    print(f"{c}[CHAT] {curr} > {RESET}", end="", flush=True)
                    continue
                elif cmd == "/ban" and (state["is_admin"] or state["is_mod"]):
                    if not chat_args:
                        print("[ERROR] Usage: /ban <username>")
                    else:
                        target = " ".join(chat_args).strip()
                        if target == FOUNDER_USERNAME:
                            print("[ERROR] Cannot ban the Founder/Owner.")
                        elif target in fresh_users:
                            fresh_users[target]["banned"] = True
                            save_users(fresh_users)
                            print(f"[SUCCESS] User '{target}' has been banned.")
                        else:
                            print(f"[ERROR] User '{target}' not found.")
                    print(f"{c}[CHAT] {curr} > {RESET}", end="", flush=True)
                    continue
                else:
                    print("[ERROR] Unknown chat command or insufficient permissions.")
                    print(f"{c}[CHAT] {curr} > {RESET}", end="", flush=True)
                    continue

            fresh_users = load_users()
            role = fresh_users.get(curr, {}).get("role", "Member")
            new_msg = {
                "sender": curr,
                "role": role,
                "text": line,
                "time": datetime.now().strftime("%H:%M:%S")
            }
            messages = load_chat()
            messages.append(new_msg)
            if len(messages) > 100:
                messages = messages[-100:]
            save_chat(messages)
    except (KeyboardInterrupt, EOFError):
        chat_active = False
        print("\n[INFO] Exiting chatroom.")


# ----------------------------------------------------------------------
# FOUNDER / OWNER / ADMIN / MOD COMMANDS
# ----------------------------------------------------------------------
def cmd_users(args):
    c = accent()
    users = load_users()
    print(f"\n{c}{BOLD}=== REGISTERED ACCOUNTS & ACTIVE SESSION ==={RESET}")
    print(f"Total Registered Accounts: {len(users)}")
    print("-" * 95)
    print(f"{'USERNAME':<16} | {'ROLE':<20} | {'FRIENDS':<8} | {'STATUS':<9} | {'BANNED':<6} | {'LAST LOGIN'}")
    print("-" * 95)
    for uname, info in users.items():
        role = info.get("role", "Member")
        friends_count = len(info.get("friends", []))
        status = "ACTIVE" if state["current_user"] == uname else "Offline"
        banned = "YES" if info.get("banned", False) else "No"
        last_login = info.get("last_login", "Unknown")
        print(f"{uname:<16} | {role:<20} | {friends_count:<8} | {status:<9} | {banned:<6} | {last_login}")
    print("-" * 95 + "\n")


def cmd_deluser(args):
    if not args:
        print("Usage: /deluser <username>")
        return
    target = " ".join(args).strip()
    if target == FOUNDER_USERNAME:
        print("[ERROR] Cannot delete the Founder / Owner account.")
        return
    users = load_users()
    if target not in users:
        print(f"[ERROR] User '{target}' does not exist.")
        return
    confirm = input(f"Are you sure you want to delete account '{target}'? (y/n): ").strip().lower()
    if confirm == "y":
        del users[target]
        save_users(users)
        print(f"[ADMIN] Account '{target}' has been deleted.")
    else:
        print("[INFO] Cancelled.")


def cmd_ban(args):
    if not args:
        print("Usage: /ban <username>")
        return
    target = " ".join(args).strip()
    if target == FOUNDER_USERNAME:
        print("[ERROR] Cannot ban the Founder / Owner.")
        return
    users = load_users()
    if target not in users:
        print(f"[ERROR] User '{target}' does not exist.")
        return
    users[target]["banned"] = True
    save_users(users)
    print(f"[MOD/ADMIN] User '{target}' has been banned from the terminal & chatroom.")


def cmd_unban(args):
    if not args:
        print("Usage: /unban <username>")
        return
    target = " ".join(args).strip()
    users = load_users()
    if target not in users:
        print(f"[ERROR] User '{target}' does not exist.")
        return
    users[target]["banned"] = False
    save_users(users)
    print(f"[MOD/ADMIN] User '{target}' has been unbanned.")


def cmd_mod(args):
    if not args:
        print("Usage: /mod <username>")
        return
    target = " ".join(args).strip()
    users = load_users()
    if target not in users:
        print(f"[ERROR] User '{target}' does not exist.")
        return
    users[target]["role"] = "MODERATOR"
    save_users(users)
    print(f"[ADMIN] '{target}' has been granted Moderator permission!")


def cmd_demote(args):
    if not args:
        print("Usage: /demote <username>")
        return
    target = " ".join(args).strip()
    if target == FOUNDER_USERNAME:
        print("[ERROR] Cannot demote Founder.")
        return
    users = load_users()
    if target not in users:
        print(f"[ERROR] User '{target}' does not exist.")
        return
    users[target]["role"] = "Member"
    save_users(users)
    print(f"[ADMIN] '{target}' has been demoted to Member.")


def cmd_promote(args):
    if not args:
        print("Usage: /promote <username>")
        return
    target = " ".join(args).strip()
    users = load_users()
    if target not in users:
        print(f"[ERROR] User '{target}' does not exist.")
        return
    users[target]["role"] = "ADMIN"
    save_users(users)
    print(f"[ADMIN] '{target}' has been promoted to ADMIN.")


def cmd_announce(args):
    if not args:
        state["announcement"] = None
        print("[ADMIN] Banner announcement cleared.")
        return
    state["announcement"] = " ".join(args)
    print(f"[ADMIN] Banner announcement set to: {state['announcement']}")


# ----------------------------------------------------------------------
# DEV MODE COMMANDS
# ----------------------------------------------------------------------
def cmd_color(args):
    if not args or args[0].lower() not in COLORS:
        print("Usage: /color <name>   Options: " + ", ".join(COLORS))
        return
    state["config"]["color"] = args[0].lower()
    save_config()
    print(f"{accent()}[DEV] Accent color set to {args[0].lower()}.{RESET}")


def cmd_prompt(args):
    if not args:
        print("Usage: /prompt <text>   Example: /prompt magic")
        return
    state["config"]["prompt"] = " ".join(args)
    save_config()
    print(f"[DEV] Prompt name set to '{state['config']['prompt']}'.")


def cmd_config(args):
    print("[DEV] Current settings:")
    for k, v in state["config"].items():
        print(f"  {k}: {v}")
    print(f"  config file: {CONFIG_PATH}")


def cmd_resetconfig(args):
    state["config"] = dict(DEFAULT_CONFIG)
    save_config()
    print("[DEV] Customization reset to defaults.")


def cmd_sysinfo_short(args):
    print(f"Python {platform.python_version()} on {platform.system()} {platform.release()}")
    print(f"Working directory: {os.getcwd()}")


# ----------------------------------------------------------------------
# YOUR PROGRAMS
# ----------------------------------------------------------------------
def run_database():
    print("-------------Welcome to the Database!{made by m461c c17y}-------------")
    input("Press any key for your first question. ")
    name = input("What is your full name? ")
    print(f"Wow, {name}. That is a awesome name! ")
    time.sleep(1)
    DOB = input("What is your Date of birth? ")
    fav_color = input("What is your favorite color? ")
    time.sleep(1)
    print("-----------------LOADING COLLECTED DATA-----------------")
    time.sleep(2)
    print("-----------------YOUR DATA-----------------")
    print(f"Name: {name}")
    time.sleep(0.2)
    print(f"Date of birth: {DOB}")
    time.sleep(0.2)
    print(f"Favorite Color: {fav_color}")
    time.sleep(0.2)

    choice = input("\nWould you like to save this to a .txt file? (y/n): ").strip().lower()

    if choice == 'y':
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, "database_report.txt")

        with open(file_path, "w") as f:
            f.write("--- MY DATA ---\n")
            f.write(f"Name: {name}\n")
            f.write(f"Date of birth: {DOB}\n")
            f.write(f"Favorite color: {fav_color}\n")

        print(f"\n[SUCCESS] File saved at: {file_path}")
    else:
        print("\n[INFO] Skipped saving.")

    input("\nPress Enter to exit...")


def run_syshook():
    print(r"""
=========================================
          S Y S H O O K                  
          by m461c c17y                  
=========================================
""")
    time.sleep(0.5)
    input("Press Enter to see your specs...")
    time.sleep(1)
    print("Obtaining system access...")
    time.sleep(0.4)
    print("Getting system information...")
    time.sleep(0.8)
    print("System information obtained, displaying info now.")
    time.sleep(0.1)
    print("\n--- MY COMPUTER SPECS ---")
    time.sleep(0.4)

    comp_name = platform.node()
    os_info = f"{platform.system()} {platform.release()}"
    processor = platform.processor()
    cores = os.cpu_count()

    print(f"Computer Name    : {comp_name}")
    time.sleep(0.4)
    print(f"Operating System : {os_info}")
    time.sleep(0.4)
    print(f"Processor        : {processor}")
    time.sleep(0.4)
    print(f"CPU Cores        : {cores}")
    print("-" * 25)

    choice = input("\nWould you like to save this to a .txt file? (y/n): ").strip().lower()

    if choice == 'y':
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, "syshook_report.txt")

        with open(file_path, "w") as f:
            f.write("=========================================\n")
            f.write("          S Y S H O O K                  \n")
            f.write("          by m461c c17y                  \n")
            f.write("=========================================\n\n")
            f.write("--- MY COMPUTER SPECS ---\n")
            f.write(f"Computer Name    : {comp_name}\n")
            f.write(f"Operating System : {os_info}\n")
            f.write(f"Processor        : {processor}\n")
            f.write(f"CPU Cores        : {cores}\n")

        print(f"\n[SUCCESS] File saved at: {file_path}")
    else:
        print("\n[INFO] Skipped saving.")

    input("\nPress Enter to exit...")


def _run_program(func):
    try:
        func()
    except KeyboardInterrupt:
        print("\n[INFO] Program cancelled.")
    print()


def cmd_database(args):
    _run_program(run_database)


def cmd_syshook(args):
    _run_program(run_syshook)


LANGUAGES = [
    ("Python", ".py", sys.executable),
    ("JavaScript", ".js", "node"),
    ("HTML", ".html", None),
    ("C", ".c", None),
    ("C++", ".cpp", None),
    ("Java", ".java", None),
    ("Lua", ".lua", "lua"),
    ("Ruby", ".rb", "ruby"),
    ("Bash", ".sh", "bash"),
    ("Plain text", ".txt", None),
]

CODE_HELP = """  :save        save the file
  :show        show your code with line numbers
  :edit N      rewrite line N
  :del N       delete line N
  :clear       erase everything
  :run         save and run it (Python, JavaScript, Lua, Ruby, Bash)
  :help        show this list
  :quit        leave the code area"""


def cmd_code(args):
    c = accent()
    print(f"\n{c}{BOLD}=== M461C CODE AREA ==={RESET}")
    print("This coding area is simple on purpose. It has no autocomplete, no")
    print("suggestions and no error checking, so you have to type every line")
    print("yourself. That's how you actually learn the code (and remember it!).\n")

    for i, (name, ext, _) in enumerate(LANGUAGES, 1):
        print(f"  {c}{i:>2}{RESET}  {name} ({ext})")
    choice = input("\nPick a language number (or q to cancel): ").strip().lower()
    if choice in ("q", ""):
        return
    if not choice.isdigit() or not 1 <= int(choice) <= len(LANGUAGES):
        print("[ERROR] That isn't one of the options.")
        return
    lang, ext, runner = LANGUAGES[int(choice) - 1]

    fname = os.path.basename(input("File name: ").strip())
    if not fname:
        print("[ERROR] You need a file name.")
        return
    if not fname.lower().endswith(ext):
        fname += ext

    os.makedirs(CODE_DIR, exist_ok=True)
    path = os.path.join(CODE_DIR, fname)
    lines = []
    saved = True

    if os.path.exists(path):
        if input(f"{fname} already exists. Open it to keep editing? (y/n): ").strip().lower() == "y":
            with open(path, "r") as f:
                lines = f.read().split("\n")
            if lines and lines[-1] == "":
                lines.pop()
        else:
            print("[INFO] Cancelled so nothing gets overwritten.")
            return

    def save():
        with open(path, "w") as f:
            f.write("\n".join(lines) + ("\n" if lines else ""))
        print(f"[SAVED] {path}")

    def show():
        if not lines:
            print("  (empty)")
        for n, text in enumerate(lines, 1):
            print(f"{n:>3} | {text}")

    print(f"\nEditing {fname} ({lang}). Type code line by line.")
    print("Lines that start with : are editor commands. Type :help to see them.\n")
    if lines:
        show()

    while True:
        try:
            text = input(f"{len(lines) + 1:>3} | ")
        except (EOFError, KeyboardInterrupt):
            print()
            text = ":quit"

        if not text.startswith(":"):
            lines.append(text)
            saved = False
            continue

        parts = text[1:].split()
        cmd = parts[0].lower() if parts else ""
        num = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None

        if cmd == "save":
            save()
            saved = True
        elif cmd == "show":
            show()
        elif cmd == "help":
            print(CODE_HELP)
        elif cmd == "clear":
            lines.clear()
            saved = False
            print("[INFO] Cleared.")
        elif cmd in ("del", "edit"):
            if num is None or not 1 <= num <= len(lines):
                print(f"Usage: :{cmd} N   (N is a line number from :show)")
            elif cmd == "del":
                removed = lines.pop(num - 1)
                saved = False
                print(f"[DELETED] {removed}")
            else:
                lines[num - 1] = input(f"{num:>3} | ")
                saved = False
        elif cmd == "run":
            save()
            saved = True
            exe = runner if runner == sys.executable else (shutil.which(runner) if runner else None)
            if exe is None:
                if runner is None:
                    print(f"[INFO] {lang} can't be run from here. Your file is saved in:\n       {CODE_DIR}")
                else:
                    print(f"[INFO] '{runner}' isn't installed on this computer, so I can't run {lang}.")
            else:
                print(f"--- running {fname} ---")
                try:
                    subprocess.run([exe, path], cwd=CODE_DIR)
                except KeyboardInterrupt:
                    print("\n[INFO] Stopped.")
                print("--- finished ---")
        elif cmd == "quit":
            if not saved and input("You have unsaved changes. Save first? (y/n): ").strip().lower() == "y":
                save()
            print("[INFO] Left the code area.\n")
            return
        else:
            print("Unknown editor command. Type :help")


def run_universalexeconverter():
    print("===============================================================================")
    print("          ADVANCED UNIVERSAL EXE BUILDER {made by m461c c17y} ")
    print("===============================================================================")

    print("\nHow to get a path: Right-click your file -> 'Copy as path'")
    target_path = input("Paste the path to your file here and press Enter: ").strip()

    if target_path.startswith('"') and target_path.endswith('"'):
        target_path = target_path[1:-1]

    if not os.path.exists(target_path):
        print(f"\n[ERROR] Could not find file at: {target_path}")
        input("\nPress Enter to close...")
        return

    file_name = os.path.basename(target_path)
    file_dir = os.path.dirname(target_path)

    print(f"\n[+] Found target: {file_name}")

    icon_path = ""
    use_icon = input("Do you want to add a custom icon? (y/n): ").strip().lower()
    if use_icon == 'y':
        icon_path = input("Paste the path to your .ico file and press Enter: ").strip()
        if icon_path.startswith('"') and icon_path.endswith('"'):
            icon_path = icon_path[1:-1]
        if not os.path.exists(icon_path) or not icon_path.lower().endswith('.ico'):
            print("[!] Invalid or missing .ico file. Proceeding without an icon.")
            icon_path = ""

    hide_window = input("Do you want to hide the black terminal window when the EXE runs? (y/n): ").strip().lower()

    prev_dir = os.getcwd()
    os.chdir(file_dir)

    try:
        print("\n[+] Ensuring compiler components are installed...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        print("[+] Compiling into a standalone application...")
        dist_dir = os.path.join(file_dir, "Compiled_EXEs")

        cmd = [sys.executable, "-m", "PyInstaller", "--onefile", f"--distpath={dist_dir}"]

        if hide_window == 'y':
            cmd.append("--noconsole")
        else:
            cmd.append("--console")

        if icon_path:
            cmd.extend(["--icon", icon_path])

        if target_path.endswith('.py'):
            cmd.append(target_path)
        else:
            wrapper_script = os.path.join(file_dir, "_temp_runner.py")
            with open(wrapper_script, "w") as f:
                f.write("import os\n")
                f.write(f"os.system({file_name!r})\n")
            base_name = os.path.splitext(file_name)[0]
            cmd.extend([f"--name={base_name}", wrapper_script])

        try:
            subprocess.run(cmd, check=True)
            print("\n[SUCCESS] Completed! Your personalized EXE is inside the 'Compiled_EXEs' folder.")
        except Exception as e:
            print(f"\n[ERROR] Compilation failed: {e}")

        temp_runner = os.path.join(file_dir, "_temp_runner.py")
        if not target_path.endswith('.py') and os.path.exists(temp_runner):
            os.remove(temp_runner)
    finally:
        os.chdir(prev_dir)

    input("\nProcess finished. Press Enter to exit...")


def cmd_universalexeconverter(args):
    _run_program(run_universalexeconverter)


# ----------------------------------------------------------------------
# COMMAND TABLE
# ----------------------------------------------------------------------
COMMANDS = {
    "help": (cmd_help, "Show all commands", "normal"),
    "signup": (cmd_signup, "Create a new local account", "normal"),
    "login": (cmd_login, "Log into your account", "normal"),
    "signout": (cmd_signout, "Sign out of your account", "normal"),
    "social": (cmd_social, "Send a friend request:  /social <username>", "normal"),
    "notifications": (cmd_notifications, "View notifications & accept friend requests", "normal"),
    "dm": (cmd_dm, "Open private chat with friend:  /dm <username>", "normal"),
    "chat": (cmd_chat, "Open public live social chatroom", "normal"),
    "sub": (cmd_sub, "Opens my YouTube channel to subscribe", "normal"),
    "clear": (cmd_clear, "Clear the screen", "normal"),
    "devmode": (cmd_devmode, "Turn dev mode on/off:  /devmode /on | /devmode /off", "normal"),
    "welcome": (cmd_welcome, "Show the welcome banner again", "normal"),
    "time": (cmd_time, "Show the current date and time", "normal"),
    "uptime": (cmd_uptime, "How long the terminal has been running", "normal"),
    "history": (cmd_history, "Show commands you've typed", "normal"),
    "whoami": (cmd_whoami, "Show your user, account role, and dev mode status", "normal"),
    "calc": (cmd_calc, "Calculator:  /calc 2 + 2 * 5", "normal"),
    "echo": (cmd_echo, "Print text:  /echo hello", "normal"),
    "pwd": (cmd_pwd, "Show the folder you're in", "normal"),
    "ls": (cmd_ls, "List files:  /ls [folder]", "normal"),
    "coinflip": (cmd_coinflip, "Flip a coin", "normal"),
    "dice": (cmd_dice, "Roll a dice:  /dice [sides]", "normal"),
    "timer": (cmd_timer, "Countdown timer:  /timer <seconds>", "normal"),
    "note": (cmd_note, "Save a quick note:  /note <text>", "normal"),
    "notes": (cmd_notes, "Show your saved notes", "normal"),
    "passgen": (cmd_passgen, "Make a random password:  /passgen [length]", "normal"),
    "version": (cmd_version, "Show the terminal version", "normal"),
    "about": (cmd_about, "About the M461C Terminal", "normal"),
    "exit": (cmd_exit, "Close the terminal", "normal"),
    "database": (cmd_database, "Run the Database program", "dev"),
    "syshook": (cmd_syshook, "Run SysHook (computer specs)", "dev"),
    "code": (cmd_code, "Simple code area: pick a language, write, save, run", "dev"),
    "universalexeconverter": (cmd_universalexeconverter, "Run the Universal EXE Converter", "dev"),
    "color": (cmd_color, "Change accent color:  /color <name>", "dev"),
    "prompt": (cmd_prompt, "Change prompt name:  /prompt <text>", "dev"),
    "config": (cmd_config, "Show your customization settings", "dev"),
    "resetconfig": (cmd_resetconfig, "Reset customization to defaults", "dev"),
    "sysinfo": (cmd_sysinfo_short, "Quick Python/OS/folder info", "dev"),
    "users": (cmd_users, "View all registered users, roles, and active status", "admin"),
    "deluser": (cmd_deluser, "Delete a user account:  /deluser <username>", "admin"),
    "ban": (cmd_ban, "Ban a user from terminal/chat:  /ban <username>", "admin"),
    "unban": (cmd_unban, "Unban a user:  /unban <username>", "admin"),
    "mod": (cmd_mod, "Grant moderator permissions:  /mod <username>", "admin"),
    "demote": (cmd_demote, "Demote moderator to member:  /demote <username>", "admin"),
    "promote": (cmd_promote, "Promote a user to Admin:  /promote <username>", "admin"),
    "announce": (cmd_announce, "Set a banner announcement:  /announce <msg>", "admin"),
}


def run_shell(line):
    try:
        parts = shlex.split(line, posix=(os.name != "nt"))
    except ValueError:
        parts = line.split()

    if parts and parts[0].lower() in ("exit", "quit"):
        cmd_exit([])
        return

    if parts and parts[0].lower() == "cd":
        target = parts[1] if len(parts) > 1 else os.path.expanduser("~")
        try:
            os.chdir(os.path.expanduser(target))
        except OSError as e:
            print(f"[ERROR] {e}")
        return

    if parts and parts[0].lower() in ("cls", "clear"):
        cmd_clear([])
        return

    try:
        subprocess.run(line, shell=True, cwd=os.getcwd())
    except KeyboardInterrupt:
        print("\n[INFO] Command interrupted.")
    except Exception as e:
        print(f"[ERROR] {e}")


def make_prompt():
    c = accent()
    cfg = state["config"]
    tags = ""
    if state["is_admin"]:
        tags += "[OWNER]"
    elif state["is_mod"]:
        tags += "[MOD]"
    if state["devmode"]:
        tags += "[DEV]"
    user_tag = f"[{state['current_user']}]" if state["current_user"] else "[guest]"
    cwd = os.path.basename(os.getcwd()) or os.getcwd()
    return f"{c}{BOLD}{cfg['prompt']}{RESET}{DIM}{tags}{user_tag}{RESET} {cwd} > "


def main():
    enable_ansi()
    cmd_clear([])

    while True:
        try:
            line = input(make_prompt()).strip()
        except EOFError:
            print()
            cmd_exit([])
        except KeyboardInterrupt:
            print("\n(Type /exit to quit)")
            continue

        if not line:
            continue

        state["history"].append(line)

        if line.startswith("/"):
            parts = line.split()
            name = parts[0][1:].lower()
            args = parts[1:]
            entry = COMMANDS.get(name)

            if entry is None:
                print(f"Unknown command '/{name}'. Type /help to see all commands.")
            elif entry[2] == "dev" and not state["devmode"]:
                print(f"'/{name}' is a dev mode command. Turn it on with /devmode /on")
            elif entry[2] == "admin" and not (state["is_admin"] or state["is_mod"]):
                print(f"'/{name}' is restricted to Moderators and Owner accounts.")
            else:
                try:
                    entry[0](args)
                except SystemExit:
                    raise
                except Exception as e:
                    print(f"[ERROR] /{name} crashed: {e}")
        else:
            run_shell(line)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n[CRITICAL ERROR] {e}")
        input("\nPress Enter to exit...")