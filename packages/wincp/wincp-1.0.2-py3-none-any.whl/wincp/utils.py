import os
import pickle
import lzma
import secrets
import os
import json

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


CONFIG_PATH = "config.json"

def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"WinCP Error: Failed to load config: {e}")
            return {"recent_folders": [], "recent_files": []}
    return {"recent_folders": [], "recent_files": []}

def save_config(config):
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"WinCP Error: Failed to save config: {e}")

def add_recent(config, key, path):
    if path in config[key]:
        config[key].remove(path)
    config[key].insert(0, path)
    config[key] = config[key][:10]



# ---------------- FILE TREE ----------------

def build_tree_raw(path):
    if os.path.isfile(path):
        with open(path, "rb") as f:
            return {
                "name": os.path.basename(path),
                "type": "file",
                "content": f.read()
            }

    children = []
    for entry in os.listdir(path):
        full = os.path.join(path, entry)
        children.append(build_tree_raw(full))

    return {
        "name": os.path.basename(path),
        "type": "dir",
        "children": children
    }


# ---------------- COMPRESSION / ENCRYPTION ----------------

def _derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100_000,
        backend=default_backend()
    )
    return kdf.derive(password.encode("utf-8"))


def compress_encrypt(data: bytes, password: str | None, level: int) -> bytes:
    compressed = lzma.compress(data, preset=level)

    if not password:
        return compressed

    salt = secrets.token_bytes(16)
    key = _derive_key(password, salt)
    nonce = secrets.token_bytes(12)

    aes = AESGCM(key)
    encrypted = aes.encrypt(nonce, compressed, None)

    return salt + nonce + encrypted


def decrypt_decompress(data: bytes, password: str | None) -> bytes:
    if not password:
        return lzma.decompress(data)

    salt = data[:16]
    nonce = data[16:28]
    encrypted = data[28:]

    key = _derive_key(password, salt)
    aes = AESGCM(key)

    compressed = aes.decrypt(nonce, encrypted, None)
    return lzma.decompress(compressed)


# ---------------- ARCHIVE ----------------

def save_archive(
    tree: dict,
    output: str,
    password: str | None = None,
    compress_level: int = 9,
    icon_path: str | None = None,
    icon_enable: bool = True
):
    archive = {"tree": tree}

    if icon_enable and icon_path and os.path.isfile(icon_path):
        with open(icon_path, "rb") as f:
            archive["icon"] = f.read()

    raw = pickle.dumps(archive)
    final = compress_encrypt(raw, password, compress_level)

    os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)
    with open(output, "wb") as f:
        f.write(final)


def load_archive(path: str, password: str | None = None) -> dict:
    with open(path, "rb") as f:
        data = f.read()

    raw = decrypt_decompress(data, password)
    return pickle.loads(raw)
