"""Open the local editorial desk from a desktop application launcher."""

from __future__ import annotations

import socket
import os
import signal
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = "http://127.0.0.1:8766/"


def older_dashboard_pid() -> int | None:
    """Find our stale desk so the app shortcut loads updated code."""
    target = str(ROOT / "tools" / "editor_dashboard.py")
    newest_source = max((ROOT / "tools" / name).stat().st_mtime for name in
                        ("editor_dashboard.py", "editor_ui.html", "auto_draft.py", "engine.py"))
    try:
        boot = next(float(line.split()[1]) for line in Path("/proc/stat").read_text().splitlines() if line.startswith("btime "))
        ticks = os.sysconf("SC_CLK_TCK")
    except (OSError, StopIteration, ValueError):
        return None
    for proc in Path("/proc").iterdir():
        if not proc.name.isdigit() or int(proc.name) == os.getpid():
            continue
        try:
            args = (proc / "cmdline").read_bytes().split(b"\0")
            if target.encode() not in args:
                continue
            fields = (proc / "stat").read_text().rsplit(") ", 1)[1].split()
            started = boot + int(fields[19]) / ticks
            if newest_source > started + 1:
                return int(proc.name)
        except (OSError, ValueError, IndexError):
            continue
    return None


def listening() -> bool:
    try:
        with socket.create_connection(("127.0.0.1", 8766), timeout=1):
            return True
    except OSError:
        return False


def main() -> None:
    stale = older_dashboard_pid()
    if stale is not None:
        try:
            os.kill(stale, signal.SIGTERM)
            for _ in range(30):
                if not listening():
                    break
                time.sleep(0.2)
        except OSError:
            pass
    if not listening():
        local = ROOT / ".local"
        local.mkdir(exist_ok=True)
        with (local / "dashboard.log").open("a", encoding="utf-8") as log:
            subprocess.Popen([sys.executable, str(ROOT / "tools" / "editor_dashboard.py")],
                             cwd=ROOT, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                             start_new_session=True)
        for _ in range(30):
            if listening():
                break
            time.sleep(0.2)
    webbrowser.open(URL)


if __name__ == "__main__":
    main()
