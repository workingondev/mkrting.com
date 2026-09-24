"""Install the user-level systemd timer for this checkout (no root needed)."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNITS = Path.home() / ".config" / "systemd" / "user"


def main() -> None:
    if not shutil.which("systemctl"):
        raise SystemExit("systemd is unavailable on this Linux machine")
    UNITS.mkdir(parents=True, exist_ok=True)
    for name in ("mkrting-cycle.service", "mkrting-cycle.timer", "mkrting-dashboard.service"):
        text = (ROOT / "deploy" / "systemd" / name).read_text(encoding="utf-8")
        text = text.replace("__PROJECT_DIR__", str(ROOT)).replace("__PYTHON__", sys.executable)
        (UNITS / name).write_text(text, encoding="utf-8")
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "--user", "enable", "--now", "mkrting-cycle.timer"], check=True)
    subprocess.run(["systemctl", "--user", "enable", "--now", "mkrting-dashboard.service"], check=True)
    print("Installed timer. It collects every two hours and runs while your user session is active.")
    print("Installed local dashboard at http://127.0.0.1:8766/.")
    print("For runs after logout, your Linux admin must enable lingering for this user.")


if __name__ == "__main__":
    main()
