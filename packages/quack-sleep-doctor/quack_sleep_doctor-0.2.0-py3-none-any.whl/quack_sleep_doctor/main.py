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
import sys

from quack_sleep_doctor.languages import get_string, set_language

# -----------------------------
# Configuration
# -----------------------------
MESSAGES_FILE = os.path.join(
    os.path.expanduser("~"), ".config", "quack-sleep", "messages.txt"
)
CONFIG_FILE = os.path.join(
    os.path.expanduser("~"), ".config", "quack-sleep", "config.json"
)


def load_config() -> dict[str, Any]:
    config = {
        "language": "en",
        "reminder_time": "22:10",
        "countdown_initial": 20,  # 20, 15, 10, 5 -> 50 minutes then minimum
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
        if os.name == "nt":
            # Windows:
            subprocess.run(["shutdown", "/s", "/t", "0"])
        elif os.name == "posix":
            # Unix/Linux/MacOS:
            subprocess.run(["shutdown", "-h", "now"])
        else:
            raise NotImplementedError("Shutdown not implemented for this OS")
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

        self.progress = ttk.Progressbar(
            self.root, maximum=self.countdown_seconds, length=380
        )
        self.progress.pack(pady=10)

        self.time_label = tk.Label(
            self.root,
            text=self._remaining_time_str(self.countdown_seconds),
            font=("Arial", 12),
            wraplength=380,
        )
        self.time_label.pack(pady=10)

        # Buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        tk.Button(
            button_frame, text=get_string("shutdown_now"), command=self.shutdown_now
        ).pack(side="left", padx=10)
        tk.Button(button_frame, text=get_string("later"), command=self.later).pack(
            side="left", padx=10
        )

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
        while self.countdown_seconds > 0:
            if self.closed_by_user or self.user_clicked_later:
                return
            if self.user_clicked_shutdown:
                return

            self.progress["value"] = self.countdown_seconds - self.countdown_seconds
            self.time_label.config(
                text=self._remaining_time_str(self.countdown_seconds)
            )
            self.root.update_idletasks()
            time.sleep(1)
            self.countdown_seconds -= 1

        # Countdown expired → shutdown
        if not self.closed_by_user and not self.user_clicked_later:
            shutdown_computer()

        self.root.destroy()

    def _remaining_time_str(self, remaining):
        mins, secs = divmod(remaining, 60)
        return f"{mins:02}:{secs:02} {get_string('remaining')}"


def _compute_offset_for_time(target_time_str: str) -> datetime.timedelta:
    now = datetime.datetime.now()
    target_hour, target_minute = map(int, target_time_str.split(":"))
    target_time = now.replace(
        hour=target_hour, minute=target_minute, second=0, microsecond=0
    )
    if target_time < now:
        target_time += datetime.timedelta(days=1)
    offset = (target_time - now).total_seconds()
    return datetime.timedelta(seconds=int(offset + 1))


# -----------------------------
# Main logic
# -----------------------------
def countdown_loop() -> None:
    motivations = load_messages()
    config = load_config()

    debug = False
    time_offset = datetime.timedelta(seconds=0)
    if sys.argv[-1] == "--debug":
        print("Setting time to first reminder time")
        debug = True
        time_offset = _compute_offset_for_time(config["reminder_time"])

    next_countdown = config["countdown_initial"]
    reminder_hour, reminder_minute = map(int, config["reminder_time"].split(":"))
    while True:
        now = datetime.datetime.now() + time_offset
        hour = now.hour
        minute = now.minute
        if debug:
            print(f"Current time: {hour:02}:{minute:02}")

        if hour < reminder_hour or (hour == reminder_hour and minute < reminder_minute):
            # Sleep until reminder time
            time.sleep(
                _compute_offset_for_time(config["reminder_time"]).total_seconds()
            )
        else:
            window = CountdownWindow(
                int(next_countdown * 60), random.choice(motivations)
            )
            if window.user_clicked_shutdown:
                break

            if next_countdown > config["countdown_minimum"]:
                next_countdown -= config["countdown_reduction"]
                if next_countdown < config["countdown_minimum"]:
                    next_countdown = config["countdown_minimum"]

            # Sleep remaining time of countdown until we restart it
            if debug:
                print(
                    f"Gentle reminder shown. Waiting: {window.countdown_seconds} seconds"
                )
            time.sleep(window.countdown_seconds)


# -----------------------------
# Main entry point
# -----------------------------
def main() -> None:
    try:
        countdown_loop()
    except KeyboardInterrupt:
        print("\nExiting on user request.")


# -----------------------------
# Start
# -----------------------------
if __name__ == "__main__":
    main()
