import requests, random, hashlib, os, numpy as np, json, re, socket, datetime
from PIL import Image, ImageOps, ImageDraw, ImageFilter, ImageChops
import urllib3.util.connection as urllib3_cn

# Force IPv4 to prevent some API timeout issues
def allowed_gai_family(): return socket.AF_INET
urllib3_cn.allowed_gai_family = allowed_gai_family

# --- ｧ MEMORY ---
MEMORY_FILE = "factory_memory.json"

def _default_memory():
    return {"generation": 1, "old_seed": 442, "word_pool": ["MECHANICAL"]}

def load_memory():
    """
    Loads memory from MEMORY_FILE with resilience to corrupted JSON.
    If the file is corrupt it will attempt to salvage the first JSON object,
    otherwise it will back up the broken file and return defaults.
    """
    if not os.path.exists(MEMORY_FILE):
        return _default_memory()

    try:
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        # Attempt to salvage the first JSON value in the file
        try:
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                s = f.read()
            decoder = json.JSONDecoder()
            obj, idx = decoder.raw_decode(s)
            return obj
        except Exception:
            # Backup corrupt file so you can inspect it later
            try:
                ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
                corrupt_name = f"{MEMORY_FILE}.corrupt.{ts}"
                os.replace(MEMORY_FILE, corrupt_name)
                print(f"Warning: {MEMORY_FILE} was corrupt, moved to {corrupt_name}. Using defaults.")
            except Exception as ex:
                print(f"Warning: failed to back up corrupt memory file: {ex}")
            return _default_memory()
    except Exception as e:
        print(f"Warning: unexpected error reading {MEMORY_FILE}: {e}")
        return _default_memory()

def save_memory(gen, seed, pool):
    """
    Atomically write memory to disk to avoid partial writes / corruption.
    """
    data = {"generation": gen, "old_seed": seed, "word_pool": pool[-50:]}
    tmp = MEMORY_FILE + ".tmp"
    try:
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, MEMORY_FILE)
    except Exception as e:
        print(f"Error saving memory to {MEMORY_FILE}: {e}")
        # If tmp exists, try to remove it to avoid confusion on next run
        try:
            if os.path.exists(tmp):
                os.remove(tmp)
        except:
            pass