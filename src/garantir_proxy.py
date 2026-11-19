"""
Garante que o proxy CVM (`proxy_cvm.py`) esteja ativo antes de executar o `ollama`.
Se já estiver respondendo em /health, retorna imediatamente (< 50 ms).
Se estiver desligado, inicia `proxy_cvm.py` em segundo plano e aguarda ficar pronto.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
import urllib.request


def _ativo(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=0.8) as r:
            return r.status == 200
    except Exception:
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=11435)
    ap.add_argument("--num-gpu", type=int, default=16)
    args = ap.parse_args()

    if _ativo(args.port):
        return 0

    pythonw = shutil.which("pythonw.exe") or sys.executable
    proxy_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "proxy_cvm.py")
    flags = (
        getattr(subprocess, "CREATE_NO_WINDOW", 0)
        | getattr(subprocess, "DETACHED_PROCESS", 0)
        | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    )
    subprocess.Popen(
        [pythonw, proxy_script, "--port", str(args.port), "--num-gpu", str(args.num_gpu)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        creationflags=flags,
        close_fds=True,
    )

    limite = time.time() + 8.0
    while time.time() < limite:
        if _ativo(args.port):
            return 0
        time.sleep(0.25)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
