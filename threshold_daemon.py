#!/usr/bin/env python3
"""
Threshold daemon — long-running process that listens for screen unlock
and shows the intention prompt instantly, no Python cold-start delay.

Architecture:
- A single Python process stays alive, holding the unlock observer.
- Trigger: com.apple.screenIsUnlocked from the distributed notification
  center (fires on every screen unlock, lid-open-with-lock, etc).
- On each unlock (or SIGUSR1 for manual trigger), spawn a fresh tk.Tk(),
  run a short-lived mainloop until the user submits, destroy the window.
- Per-event tk creation avoids tk-on-macOS issues with hide/show across
  Spaces and fullscreen toggles.
"""

import json
import signal
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path

import objc
from AppKit import NSObject, NSRunLoop, NSDate
from Foundation import NSDefaultRunLoopMode, NSDistributedNotificationCenter

LOG_PATH = Path(__file__).parent / "log.jsonl"


def log_entry(answer: str):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "answer": answer.strip(),
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def show_prompt():
    """Build a fresh tk window, run until submit, destroy. Blocking."""
    root = tk.Tk()
    root.title("Threshold")
    root.attributes("-fullscreen", True)
    root.attributes("-topmost", True)
    root.configure(bg="#1a1a1a")
    root.focus_force()

    frame = tk.Frame(root, bg="#1a1a1a")
    frame.place(relx=0.5, rely=0.5, anchor="center")

    tk.Label(
        frame,
        text="What are you here for?",
        font=("Georgia", 36),
        fg="#d4d0c8",
        bg="#1a1a1a",
        pady=24,
    ).pack()

    entry_var = tk.StringVar()
    entry = tk.Entry(
        frame,
        textvariable=entry_var,
        font=("Georgia", 22),
        fg="#d4d0c8",
        bg="#2a2a2a",
        insertbackground="#d4d0c8",
        bd=0,
        highlightthickness=1,
        highlightcolor="#555",
        highlightbackground="#333",
        width=36,
        justify="center",
    )
    entry.pack(ipady=12)
    entry.focus_set()

    tk.Label(
        frame,
        text="press enter to continue",
        font=("Georgia", 13),
        fg="#555",
        bg="#1a1a1a",
        pady=16,
    ).pack()

    def submit(event=None):
        answer = entry_var.get().strip()
        if not answer:
            return
        log_entry(answer)
        root.destroy()

    entry.bind("<Return>", submit)
    root.bind("<Escape>", lambda e: None)
    root.protocol("WM_DELETE_WINDOW", lambda: None)

    root.mainloop()


# Coordinate triggers from multiple sources (AppKit wake, SIGUSR1) into a
# single serialized prompt. tk must run on the main thread, so the AppKit
# observer and signal handler set a flag; the main loop polls and shows.
_show_lock = threading.Lock()
_show_pending = False


def request_show():
    global _show_pending
    with _show_lock:
        _show_pending = True


def consume_show_request() -> bool:
    global _show_pending
    with _show_lock:
        if _show_pending:
            _show_pending = False
            return True
        return False


class UnlockObserver(NSObject):
    def init(self):
        self = objc.super(UnlockObserver, self).init()
        return self

    def screenUnlocked_(self, notification):
        request_show()


def main():
    observer = UnlockObserver.alloc().init()
    nc = NSDistributedNotificationCenter.defaultCenter()
    nc.addObserver_selector_name_object_(
        observer,
        b"screenUnlocked:",
        "com.apple.screenIsUnlocked",
        None,
    )

    signal.signal(signal.SIGUSR1, lambda *_: request_show())

    runloop = NSRunLoop.currentRunLoop()
    while True:
        # Pump AppKit notifications for ~200ms, then check for show request.
        runloop.runMode_beforeDate_(
            NSDefaultRunLoopMode,
            NSDate.dateWithTimeIntervalSinceNow_(0.2),
        )
        if consume_show_request():
            show_prompt()  # blocks until submit


if __name__ == "__main__":
    main()
