from typing import Any
import tkinter as tk
from tkinter import ttk
import datetime
import time
import threading
import subprocess
import random
import os
import json

from quack_sleep_doctor.languages import get_string, set_language

# -----------------------------
# Configuration
# -----------------------------
MESSAGES_FILE = os.path.join(os.path.expanduser("~"), ".config", "quack-sleep", "messages.txt")
CONFIG_FILE = os.path.join(os.path.expanduser("~"), ".config", "quack-sleep", "config.json")


def load_config() -> dict[str, Any]:
    config = {
        "language": "en",
        "time_gentle_reminder": "22:30",
        "time_strict_reminder": "23:00",
        "gentle_spacing_minutes": 5,
        "strict_spacing_minutes": 1,
        "countdown_initial": 15,
        "countdown_reduction": 5,
        "countdown_minimum": 1,
    }
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config_file = json.load(f)
            config.update(config_file)
    print("Loaded config:", config)
    set_language(config["language"])
    return config


# -----------------------------
# Load messages
# -----------------------------
def load_messages() -> list[str]:
    if not os.path.exists(MESSAGES_FILE):
        return [
            get_string("sleep_message"),
            get_string("future_thanks"),
            get_string("go_to_sleep"),
        ]
    with open(MESSAGES_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    return lines or [get_string("sleep_message")]


# -----------------------------
# Shutdown function
# -----------------------------
def shutdown_computer() -> None:
    try:
        # Windows:
        subprocess.run(["shutdown", "/s", "/t", "0"])

        # macOS:
        # subprocess.run(["sudo", "shutdown", "-h", "now"])

        # Linux:
        # subprocess.run(["shutdown", "-h", "now"])
    except Exception as e:
        print(get_string("shutdown_failed"), e)


# -----------------------------
# Countdown window
# -----------------------------
class CountdownWindow:
    def __init__(self, countdown_seconds: int, message: str):
        self.countdown_seconds = countdown_seconds
        self.closed_by_user = False
        self.user_clicked_later = False
        self.user_clicked_shutdown = False

        self.root = tk.Tk()
        self.root.title(get_string("window_title"))
        self.root.attributes("-topmost", True)
        self.root.geometry("420x200")

        msg = message
        tk.Label(self.root, text=msg, font=("Arial", 12), wraplength=380).pack(pady=10)

        self.progress = ttk.Progressbar(self.root, maximum=self.countdown_seconds, length=380)
        self.progress.pack(pady=10)

        # Buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text=get_string("shutdown_now"), command=self.shutdown_now).pack(side="left", padx=10)
        tk.Button(button_frame, text=get_string("later"), command=self.later).pack(side="left", padx=10)

        self.root.protocol("WM_DELETE_WINDOW", self.later)

        threading.Thread(target=self.run_countdown, daemon=True).start()
        self.root.mainloop()

    def later(self):
        self.user_clicked_later = True
        self.closed_by_user = True
        self.root.destroy()

    def shutdown_now(self):
        self.user_clicked_shutdown = True
        self.root.destroy()
        shutdown_computer()

    def run_countdown(self):
        remaining = self.countdown_seconds
        while remaining > 0:
            if self.closed_by_user or self.user_clicked_later:
                return
            if self.user_clicked_shutdown:
                return

            self.progress["value"] = self.countdown_seconds - remaining
            time.sleep(1)
            remaining -= 1

        # Countdown expired → shutdown
        if not self.closed_by_user and not self.user_clicked_later:
            shutdown_computer()

        self.root.destroy()


# -----------------------------
# Main logic
# -----------------------------
def main() -> None:
    motivations = load_messages()
    config = load_config()
    next_countdown = config["countdown_initial"]

    gentle_hour, gentle_minute = map(int, config["time_gentle_reminder"].split(":"))
    strict_hour, strict_minute = map(int, config["time_strict_reminder"].split(":"))

    while True:
        now = datetime.datetime.now()
        hour = now.hour
        minute = now.minute

        if hour < gentle_hour or (hour == gentle_hour and minute < gentle_minute):
            time.sleep(300)
        elif hour < strict_hour or (hour == strict_hour and minute < strict_minute):
            window = CountdownWindow(next_countdown, random.choice(motivations))

            # Reduce countdown stages if the user cancels
            if window.user_clicked_later or window.closed_by_user:
                if next_countdown > config["countdown_minimum"]:
                    next_countdown -= config["countdown_reduction"]
                    if next_countdown < config["countdown_minimum"]:
                        next_countdown = config["countdown_minimum"]

            time.sleep(int(config["gentle_spacing_minutes"] * 60))
        else:
            window = CountdownWindow(config["countdown_minimum"], random.choice(motivations))
            time.sleep(int(config["strict_spacing_minutes"] * 60))


# -----------------------------
# Start
# -----------------------------
if __name__ == "__main__":
    main()
