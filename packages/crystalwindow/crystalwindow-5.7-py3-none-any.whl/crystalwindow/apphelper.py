import os
import sys
import subprocess

class GameAppHelper:
    DEFAULT_APPS = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "explorer": "explorer.exe",
        "cmd": "cmd.exe",
        "powershell": "powershell.exe",
        "taskmgr": "taskmgr.exe",
        "paint": "mspaint.exe"
    }

    def __init__(self):
        # exe_name -> list of processes
        self.running_apps = {}

    # -------------------------------
    # OPEN DEFAULT WINDOWS APP
    # -------------------------------
    def open_default_app(self, app_name):
        app = self.DEFAULT_APPS.get(app_name.lower())
        if not app:
            print(f"[AppHelper] Unknown default app: {app_name}")
            return

        self._launch_process(app)

    # -------------------------------
    # OPEN ANY APP BY PATH OR EXE
    # -------------------------------
    def open_app(self, app_path):
        exe = os.path.basename(app_path)
        self._launch_process(app_path, exe)

    # -------------------------------
    # INTERNAL LAUNCH
    # -------------------------------
    def _launch_process(self, command, exe_name=None):
        try:
            proc = subprocess.Popen(command)

            exe = exe_name or os.path.basename(command)
            exe = exe.lower()

            self.running_apps.setdefault(exe, []).append(proc)

            print(f"[AppHelper] Opened {exe}")

        except Exception as e:
            print(f"[AppHelper] Failed to open app: {e}")

    # -------------------------------
    # CLOSE / KILL BY EXE NAME
    # -------------------------------
    def close_app(self, exe_name):
        exe = exe_name.lower()
        procs = self.running_apps.get(exe)

        if not procs:
            print(f"[AppHelper] No running app named {exe}")
            return

        for proc in procs:
            try:
                proc.kill()  # HARD kill
            except Exception:
                os.system(f"taskkill /PID {proc.pid} /F")

        del self.running_apps[exe]
        print(f"[AppHelper] Closed all instances of {exe}")

    # -------------------------------
    # CLOSE ONLY ONE INSTANCE (OPTIONAL)
    # -------------------------------
    def close_one(self, exe_name):
        exe = exe_name.lower()
        procs = self.running_apps.get(exe)

        if not procs:
            print(f"[AppHelper] No running app named {exe}")
            return

        proc = procs.pop()
        try:
            proc.kill()
        except:
            os.system(f"taskkill /PID {proc.pid} /F")

        if not procs:
            del self.running_apps[exe]

        print(f"[AppHelper] Closed one instance of {exe}")

    # -------------------------------
    # CLOSE PYTHON APP
    # -------------------------------
    def close_current_app(self):
        sys.exit()
