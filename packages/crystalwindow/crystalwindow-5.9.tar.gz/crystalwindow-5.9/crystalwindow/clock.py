import time
from datetime import datetime
from collections import deque

# ============================================================
# Timer/Wait for a specific duration
# ============================================================
class CountdownTimer:
    def __init__(self):
        self.start_time = 0.0
        self.duration = 0.0
        self.running = False

    def start(self, duration: float):
        self.duration = duration
        self.start_time = time.perf_counter()
        self.running = True

    def reset(self):
        self.start_time = 0.0
        self.duration = 0.0
        self.running = False

    def is_finished(self):
        if not self.running:
            return True
        elapsed = time.perf_counter() - self.start_time
        return elapsed >= self.duration

    def get_remaining(self):
        if not self.running:
            return 0.0
        elapsed = time.perf_counter() - self.start_time
        remaining = self.duration - elapsed
        return max(0.0, remaining)


# ============================================================
# MAIN CLOCK
# ============================================================
class Clock:
    def __init__(self, target_fps: int = 60, smooth_fps: int = 30):
        self.last = time.perf_counter()
        self.delta = 0.0

        # FPS
        self.target_fps = target_fps
        self.timer = CountdownTimer()
        self.min_frame_time = 1 / target_fps if target_fps else 0
        self.frame_times = deque(maxlen=smooth_fps)

        self.paused = False

    # ----------------------------------------------------------
    # TICK + FPS
    # ----------------------------------------------------------
    def tick(self, fps: int | None = None):
        if fps:
            self.target_fps = fps
            self.min_frame_time = 1 / fps

        now = time.perf_counter()
        raw_delta = now - self.last
        self.last = now

        # Paused = no delta
        if self.paused:
            self.delta = 0.0
            return 0.0

        # FPS limiting
        sleep_time = self.min_frame_time - raw_delta
        if sleep_time > 0:
            time.sleep(sleep_time)
            now2 = time.perf_counter()
            raw_delta = now2 - (self.last - raw_delta)

        self.delta = raw_delta
        self.frame_times.append(raw_delta)

        return self.delta

    def get_fps(self):
        if not self.frame_times:
            return 0.0
        avg = sum(self.frame_times) / len(self.frame_times)
        return round(1 / avg, 2) if avg > 0 else 0

    # ----------------------------------------------------------
    # PAUSE / RESUME
    # ----------------------------------------------------------
    def pause(self):
        self.paused = True

    def resume(self):
        self.paused = False
        self.last = time.perf_counter()

    # ----------------------------------------------------------
    # TIME + DATE UTILITIES
    # ----------------------------------------------------------
    def time(self, milliseconds: bool = True, hour_12: bool = False):
        now = datetime.now()

        if hour_12:
            fmt = "%I:%M:%S" + (" %p" if not milliseconds else ".%f %p")
        else:
            fmt = "%H:%M:%S" + (".%f" if milliseconds else "")

        text = now.strftime(fmt)
        if milliseconds:
            # Trim microseconds to milliseconds
            if hour_12:
                # Example: "03:20:15.123000 PM" -> "03:20:15.123 PM"
                parts = text.split(".")
                ms = parts[1][:3] + parts[1][6:]  # keep .mmm, remove "000 PM"
                text = parts[0] + "." + parts[1][:3] + " " + now.strftime("%p")
            else:
                text = text[:-3]  # remove last 3 microseconds digits

        return text

    def date(self, format: str = "%m/%d/%Y"):
        return datetime.now().strftime(format)

    def time_date(self, order: str = "time_first", **kwargs):
        t = self.time(**kwargs)
        d = self.date()
        return f"{t}  |  {d}" if order == "time_first" else f"{d}  |  {t}"

    # ----------------------------------------------------------
    # CUSTOM FORMATTERS
    # ----------------------------------------------------------
    def format_time(self, fmt: str):
        return datetime.now().strftime(fmt)

    def format_date(self, fmt: str):
        return datetime.now().strftime(fmt)

    # ----------------------------------------------------------
    # MONOTONIC TIMESTAMP
    # ----------------------------------------------------------
    def timestamp(self):
        """High-precision monotonic timestamp."""
        return time.perf_counter()
    
    #TIMER
    def start_timer(self, seconds: float):
        self.timer.start(seconds)

    def timer_ended(self):
        return self.timer.is_finished()

    def timer_remaining(self):
        return self.timer.get_remaining()