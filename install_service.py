"""Install the assistant as a Windows Scheduled Task that runs at login."""
import subprocess
import sys
import os
from pathlib import Path

TASK_NAME  = "PersonalAssistantBot"
BASE_DIR   = Path(__file__).parent.resolve()
SCRIPT     = BASE_DIR / "main.py"
PYTHON_EXE = Path(sys.executable)          # full path to python.exe
PYTHONW    = PYTHON_EXE.parent / "pythonw.exe"
LOG        = BASE_DIR / "bot.log"
LAUNCHER   = BASE_DIR / "_launcher.bat"


def _write_launcher():
    # Use pythonw.exe if available (no console window), else python.exe
    exe = PYTHONW if PYTHONW.exists() else PYTHON_EXE
    LAUNCHER.write_text(
        f'@echo off\n'
        f'cd /d "{BASE_DIR}"\n'
        f'"{exe}" "{SCRIPT}" >> "{LOG}" 2>&1\n',
        encoding="utf-8"
    )


def install():
    _write_launcher()
    cmd = [
        "schtasks", "/Create", "/F",
        "/TN", TASK_NAME,
        "/TR", f'"{LAUNCHER}"',
        "/SC", "ONLOGON",
        "/DELAY", "0000:30",
        "/RL", "HIGHEST",
    ]
    result = subprocess.run(" ".join(cmd), shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ تم التثبيت! البوت هيشتغل تلقائياً مع بدء Windows.")
        print(f"📄 الـ logs: {LOG}")
        start()
    else:
        print("❌ فشل:")
        print(result.stdout)
        print(result.stderr)


def start():
    _write_launcher()
    # Kill any existing instance first
    subprocess.run(["taskkill", "/F", "/IM", "pythonw.exe"], capture_output=True)
    subprocess.Popen(
        f'"{LAUNCHER}"',
        shell=True,
        creationflags=0x00000008,   # DETACHED_PROCESS
        cwd=str(BASE_DIR)
    )
    print("🚀 البوت اشتغل في الـ background.")
    print(f"📄 تابع الـ logs: {LOG}")


def stop():
    subprocess.run(["taskkill", "/F", "/IM", "pythonw.exe"], capture_output=True)
    subprocess.run(["taskkill", "/F", "/IM", "python.exe"], capture_output=True)
    print("⛔ البوت وقف.")


def remove():
    stop()
    subprocess.run(["schtasks", "/Delete", "/F", "/TN", TASK_NAME], capture_output=True)
    if LAUNCHER.exists():
        LAUNCHER.unlink()
    print("🗑️ تم الحذف.")


def status():
    log_tail = ""
    if LOG.exists():
        lines = LOG.read_text(encoding="utf-8", errors="ignore").splitlines()
        log_tail = "\n".join(lines[-10:])
    print("📄 آخر 10 سطور من الـ log:\n")
    print(log_tail or "(الـ log فاضي)")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "install"
    {"install": install, "start": start, "stop": stop,
     "remove": remove, "status": status}.get(arg, install)()
