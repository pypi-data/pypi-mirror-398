import sys
import os
import time
import platform
import atexit


class System:
    def __init__(self):
        # ---------- BASIC INFO ----------
        self.system_name = self._get_os_name()
        self.python_version = sys.version
        self.platform = sys.platform
        self.executable = sys.executable
        self.cwd = os.getcwd()

        # ---------- RUNTIME ----------
        self.start_time = time.time()
        self.logs = []

        # ---------- CRASH DETECTION ----------
        self.flag_file = ".cw_running.flag"
        self.last_run_crashed = os.path.exists(self.flag_file)

        # mark app as running
        with open(self.flag_file, "w") as f:
            f.write("running")

        # cleanup on clean exit
        atexit.register(self._clean_exit)

        self.log("System initialized")
        if self.last_run_crashed:
            self.log("WARNING: last run did not exit cleanly")

    # ==============================
    # OS NAME (WINDOWS 11 ETC)
    # ==============================
    def _get_os_name(self):
        system = platform.system()

        if system == "Windows":
            # returns 10 or 11
            return f"Windows {platform.release()}"
        elif system == "Linux":
            return "Linux"
        elif system == "Darwin":
            return "macOS"
        else:
            return system

    # ==============================
    # CRASH / STATUS
    # ==============================
    def crashed_before(self):
        return self.last_run_crashed

    def _clean_exit(self):
        if os.path.exists(self.flag_file):
            os.remove(self.flag_file)
        self.log("Clean exit")

    # ==============================
    # TIME
    # ==============================
    def uptime_seconds(self):
        return int(time.time() - self.start_time)

    def uptime_formatted(self):
        s = self.uptime_seconds()
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        return f"{h:02}:{m:02}:{s:02}"

    # ==============================
    # LOGGING
    # ==============================
    def log(self, msg):
        timestamp = time.strftime("%H:%M:%S")
        entry = f"[{timestamp}] {msg}"
        self.logs.append(entry)

    def save_logs(self, path="system.log"):
        with open(path, "a", encoding="utf-8") as f:
            for line in self.logs:
                f.write(line + "\n")
        self.logs.clear()

    # ==============================
    # INFO DUMP
    # ==============================
    def get_system_info(self):
        return {
            "system": self.system_name,
            "platform": self.platform,
            "python": self.python_version,
            "executable": self.executable,
            "cwd": self.cwd,
            "uptime": self.uptime_formatted(),
            "last_run_crashed": self.last_run_crashed
        }

    def delete_file(self, path):
        try:
            if os.path.exists(path):
                os.remove(path)
                self.log(f"Deleted file: {path}")
                return True
            else:
                self.log(f"File not found for deletion: {path}")
                return False
        except Exception as e:
            self.log(f"Error deleting file {path}: {e}")
            return False

    def create_file(name, filetype):
        full_name = f"{name}.{filetype}"
        try:
            with open(full_name, "w") as f:
                f.write("")  # create empty file
            return True
        except Exception as e:
            return False

# ==============================
# WATCHDOG (FREEZE DETECTOR)
# ==============================
class Watchdog:
    def __init__(self, timeout=3):
        self.timeout = timeout
        self.last_ping = time.time()

    def ping(self):
        self.last_ping = time.time()

    def frozen(self):
        return (time.time() - self.last_ping) > self.timeout
