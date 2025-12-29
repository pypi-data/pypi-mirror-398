"""
╔════════════════════════════════════════════╗
║ BBS Client v0.2                            ║
║ - ANSI-friendly (no Windows telnet.exe)    ║
║ - Remembers a Vault cache folder           ║
╚════════════════════════════════════════════╝
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import threading
from pathlib import Path


def _config_path() -> Path:
    return Path.home() / ".bbs_client.json"


def _load_config() -> dict:
    try:
        return json.loads(_config_path().read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_config(cfg: dict) -> None:
    p = _config_path()
    try:
        p.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    except Exception:
        pass


def _reader(sock: socket.socket) -> None:
    import tempfile
    import urllib.request
    import zipfile
    import subprocess
    import shlex

    buf = ""

    def _open_path(p: Path) -> None:
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(p))  # type: ignore[attr-defined]
                return
            if sys.platform == "darwin":
                subprocess.Popen(["open", str(p)])
                return
            subprocess.Popen(["xdg-open", str(p)])
        except Exception:
            print(f"\n[client] extracted to: {p}\n")

    def _handle_opencol(parts: list[str]) -> None:
        # /opencol <url> <cid> <home_relpath>
        if len(parts) < 3:
            return
        url = parts[1]
        cid = parts[2]
        home_rel = ""
        if len(parts) >= 4:
            home_rel = " ".join(parts[3:]).strip()

        cache_dir = os.environ.get("BBS_CACHE_DIR", "").strip()
        if not cache_dir:
            # fallback
            cache_dir = str((Path.home() / ".mybbs_cache").resolve())
            Path(cache_dir).mkdir(parents=True, exist_ok=True)

        target_root = Path(cache_dir) / f"collection_{cid}"
        target_root.mkdir(parents=True, exist_ok=True)

        fd, tmp_zip = tempfile.mkstemp(prefix=f"collection_{cid}_", suffix=".zip")
        os.close(fd)

        try:
            print(f"\n[client] downloading collection {cid}...\n")
            urllib.request.urlretrieve(url, tmp_zip)

            print(f"[client] extracting to {target_root}...\n")
            with zipfile.ZipFile(tmp_zip, "r") as z:
                z.extractall(target_root)

            if home_rel:
                home_path = (target_root / home_rel).resolve()
                print(f"[client] opening {home_path}\n")
                _open_path(home_path)
            else:
                print(f"[client] done (no home path)\n")
        except Exception:
            print("\n[client] opencol failed\n")
        finally:
            try:
                os.remove(tmp_zip)
            except Exception:
                pass

    try:
        while True:
            data = sock.recv(4096)
            if not data:
                return
            chunk = data.decode("utf-8", errors="replace")
            buf += chunk

            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                if line.startswith("/opencol "):
                    parts = line.strip().split()
                    _handle_opencol(parts)
                    continue

                sys.stdout.write(line + "\n")
                sys.stdout.flush()
    except Exception:
        return



def _writer(sock: socket.socket) -> None:
    try:
        for line in sys.stdin:
            if not line:
                break
            sock.sendall(line.encode("utf-8", errors="replace"))
    except Exception:
        return


def _normalize_cache_dir(raw: str) -> str:
    p = Path(raw).expanduser().resolve()
    p.mkdir(parents=True, exist_ok=True)
    return str(p)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("host")
    ap.add_argument("port", type=int)

    ap.add_argument("--set-cache", default="", help="Set and remember the Vault cache directory for this machine")
    ap.add_argument("--cache-dir", default="", help="One-shot cache dir (does not save). Overrides saved config.")
    ap.add_argument("--show-cache", action="store_true", help="Print the current saved cache dir and exit")
    ap.add_argument("--clear-cache", action="store_true", help="Forget the saved cache dir and exit")

    args = ap.parse_args()

    cfg = _load_config()

    if args.clear_cache:
        cfg.pop("cache_dir", None)
        _save_config(cfg)
        print("Cleared saved cache.")
        return

    if args.set_cache:
        cfg["cache_dir"] = _normalize_cache_dir(args.set_cache)
        _save_config(cfg)

    if args.show_cache:
        print(cfg.get("cache_dir", ""))
        return

    cache_dir = ""
    if args.cache_dir:
        cache_dir = _normalize_cache_dir(args.cache_dir)
    elif cfg.get("cache_dir"):
        cache_dir = str(cfg["cache_dir"])

    if cache_dir:
        os.environ["BBS_CACHE_DIR"] = cache_dir

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((args.host, args.port))

    hello = "/hello ansi=1"
    if cache_dir:
        hello += f" cache={cache_dir}"
    hello += "\n"
    sock.sendall(hello.encode("utf-8", errors="replace"))

    t = threading.Thread(target=_reader, args=(sock,), daemon=True)
    t.start()

    _writer(sock)

    try:
        sock.close()
    except Exception:
        pass


if __name__ == "__main__":
    main()
