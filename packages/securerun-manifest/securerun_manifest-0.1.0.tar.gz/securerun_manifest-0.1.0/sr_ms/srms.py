
import os, sys, json, time, base64, getpass, hashlib, shutil, gc, argparse, traceback

VERSION = "0.1.0"
PBKDF2_ITER = 200_000
DK_LEN = 32

BASE_DIR = os.path.join(os.path.expanduser("~/.local/share"), "sr-ms")
LOCKED_DIR = os.path.join(BASE_DIR, "locked")
MOD_DIR = os.path.join(BASE_DIR, "mods")
_runtime_cache = {}

def ensure_dirs():
    os.makedirs(LOCKED_DIR, exist_ok=True)

def sr_path(label: str) -> str:
    safe = label.replace("/", "_").replace("..","_").replace(" ", "_")
    return os.path.join(LOCKED_DIR, f"{safe}.sr-ms")

def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def derive_key(password: str, salt: bytes, iterations=PBKDF2_ITER, dklen=DK_LEN) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, dklen=dklen)

def xor_encrypt(plain: bytes, key: bytes) -> bytearray:
    return bytearray([plain[i] ^ key[i % len(key)] for i in range(len(plain))])

def xor_decrypt(cipher: bytes, key: bytes) -> bytearray:
    return xor_encrypt(cipher, key)

def zero_bytes(b: bytearray):
    try:
        for i in range(len(b)):
            b[i] = 0
    except Exception:
        pass

ALLOWED_MOD_COMMANDS = {
    "run": lambda args: run(args[0]),
    "delete": lambda args: delete(args[0]),
    "flush": lambda args: flush(),
    "labels": lambda args: list_labels(),
    "reset": lambda args: reset(confirm=True)
}

def load_mods():
    os.makedirs(MOD_DIR, exist_ok=True)
    mods = {}

    for fname in os.listdir(MOD_DIR):
        if not fname.endswith(".mod-sr-ms"):
            continue

        path = os.path.join(MOD_DIR, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            commands = data.get("commands", {})
            for name, steps in commands.items():
                if name in mods:
                    print(f"[WARN] Mod command '{name}' overridden")
                mods[name] = steps

        except Exception as e:
            print(f"[WARN] Failed to load mod {fname}: {e}")

    return mods
    
def lock(label: str, filepath: str, password: str = None):
    if not filepath.endswith(".py"):
        raise ValueError("Only .py files allowed")
    if password is None:
        password = getpass.getpass("Enter password: ")
    if not os.path.isfile(filepath):
        raise FileNotFoundError(filepath)

    with open(filepath, "rb") as f:
        raw = f.read()

    file_hash = sha256_bytes(raw)
    salt = os.urandom(16)
    key = derive_key(password, salt)
    ct = xor_encrypt(raw, key)
    zero_bytes(bytearray(key))
    payload = {
        "meta": {
            "filename": os.path.basename(filepath),
            "locked_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "method": "xor",
            "pbkdf2_iter": PBKDF2_ITER
        },
        "data": {
            "file_hash": file_hash,
            "salt": base64.b64encode(salt).decode("utf-8"),
            "ciphertext": base64.b64encode(ct).decode("utf-8")
        }
    }

    path = sr_path(label)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    os.replace(tmp, path)

    zero_bytes(ct)
    del raw
    gc.collect()
    print(f"[INFO] Locked '{filepath}' as '{label}'")

def decrypt_payload(payload: dict, password: str) -> bytes:
    data = payload["data"]
    salt = base64.b64decode(data["salt"])
    ct = base64.b64decode(data["ciphertext"])
    key = derive_key(password, salt)
    try:
        plain = xor_decrypt(ct, key)
    except Exception:
        zero_bytes(bytearray(key))
        raise RuntimeError("Decryption failed (wrong password or corrupted)")
    zero_bytes(bytearray(key))
    if sha256_bytes(plain) != data.get("file_hash"):
        zero_bytes(plain)
        raise ValueError("Integrity check failed")
    return plain

def run(label: str, password: str = None):
    path = sr_path(label)
    if not os.path.isfile(path):
        raise FileNotFoundError(path)

    plain = _runtime_cache.get(label)
    if plain is None:
        if password is None:
            password = getpass.getpass(f"Enter password for '{label}': ")
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        plain = decrypt_payload(payload, password)
        _runtime_cache[label] = plain

    src = plain.decode("utf-8", errors="replace")
    filename = os.path.basename(label) + ".py"
    print(f"[INFO] Running {label}...")
    start = time.time()
    try:
        code_obj = compile(src, filename, "exec")
        g = {"__name__": "__main__", "__file__": filename}
        exec(code_obj, g, g)
    except Exception as e:
        print(f"[ERROR] Runtime error: {e}")
        print(traceback.format_exc())
    finally:
        elapsed = time.time() - start
        print(f"[INFO] Finished running {label} in {elapsed:.2f}s")
        zero_bytes(_runtime_cache.pop(label, bytearray()))
        gc.collect()

def delete(label: str):
    path = sr_path(label)
    if os.path.isfile(path):
        os.remove(path)
        print(f"[INFO] Deleted {label}")
    _runtime_cache.pop(label, None)

def flush():
    for k, v in list(_runtime_cache.items()):
        zero_bytes(bytearray(v))
        _runtime_cache.pop(k, None)
    gc.collect()
    print("[INFO] Runtime cache flushed")

def reset(confirm: bool = False):
    if not confirm:
        print("[WARN] Use --confirm to actually reset all locked files")
        return
    if os.path.isdir(LOCKED_DIR):
        for f in os.listdir(LOCKED_DIR):
            if f.endswith(".sr-ms"):
                os.remove(os.path.join(LOCKED_DIR, f))
    _runtime_cache.clear()
    gc.collect()
    print("[INFO] FULL reset done")

def export_sr(label: str, out_path: str = None):
    path = sr_path(label)
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    if out_path is None:
        out_path = os.path.join(os.getcwd(), os.path.basename(path))
    shutil.copy2(path, out_path)
    print(f"[INFO] Exported {label} to {out_path}")

def import_sr(file_path: str, label: str = None):
    if not os.path.isfile(file_path):
        raise FileNotFoundError(file_path)
    if label is None:
        label = os.path.splitext(os.path.basename(file_path))[0]
    dest_path = sr_path(label)
    shutil.copy2(file_path, dest_path)
    print(f"[INFO] Imported {file_path} as {label}")

def list_labels() -> list:
    if not os.path.isdir(LOCKED_DIR):
        return []
    labels = [f[:-6] for f in os.listdir(LOCKED_DIR) if f.endswith(".sr-ms")]
    for l in labels:
        print(l)
    return labels

def run_mod(name, user_args, mods):
    steps = mods.get(name)
    if not steps:
        raise ValueError("Unknown mod command")

    for step in steps:
        cmd = step.get("cmd")
        args = []

        for a in step.get("args", []):
            if a == "{label}":
                if not user_args:
                    raise ValueError("Label required")
                args.append(user_args[0])
            else:
                args.append(a)

        if cmd not in ALLOWED_MOD_COMMANDS:
            raise ValueError("Command not allowed in mod")

        ALLOWED_MOD_COMMANDS[cmd](args)
        
def main():
    ensure_dirs()  
    MODS = load_mods()
    parser = argparse.ArgumentParser(description="SR-MS - Secure Run Manifest")
    sub = parser.add_subparsers(dest="cmd", help="commands")

    p_lock = sub.add_parser("lock"); p_lock.add_argument("label"); p_lock.add_argument("file"); p_lock.add_argument("--password")
    p_run = sub.add_parser("run"); p_run.add_argument("label"); p_run.add_argument("--password")
    p_delete = sub.add_parser("delete"); p_delete.add_argument("label")
    p_reset = sub.add_parser("reset"); p_reset.add_argument("--confirm", action="store_true")
    p_export = sub.add_parser("export"); p_export.add_argument("label"); p_export.add_argument("--out")
    p_import = sub.add_parser("import"); p_import.add_argument("file"); p_import.add_argument("--label")
    p_labels = sub.add_parser("labels")

    args = parser.parse_args()
    cmds = {
        "lock": lambda: lock(args.label, args.file, args.password),
        "run": lambda: run(args.label, args.password),
        "delete": lambda: delete(args.label),
        "reset": lambda: reset(args.confirm),
        "export": lambda: export_sr(args.label, args.out),
        "import": lambda: import_sr(args.file, args.label),
        "labels": lambda: list_labels()
    }
    
    if args.cmd in MODS:
        run_mod(args.cmd, sys.argv[2:], MODS)
        return
            
    if args.cmd in cmds:
        cmds[args.cmd]()
    else:
        parser.print_help()