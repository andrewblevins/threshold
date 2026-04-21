#!/usr/bin/env python3
"""
Threshold — a wake-from-sleep intention prompt.

On each wake, shows a full-screen window asking "What are you here for?"
The answer is logged to log.jsonl and the window dismisses.
"""

import json
import os
import subprocess
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path

LOG_PATH = Path(__file__).parent / "log.jsonl"


def log_entry(answer: str):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "answer": answer.strip(),
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def show_prompt():
    root = tk.Tk()
    root.title("Threshold")

    # Full-screen, above everything
    root.attributes("-fullscreen", True)
    root.attributes("-topmost", True)
    root.configure(bg="#1a1a1a")
    root.focus_force()

    # Layout: centered column
    frame = tk.Frame(root, bg="#1a1a1a")
    frame.place(relx=0.5, rely=0.5, anchor="center")

    prompt = tk.Label(
        frame,
        text="What are you here for?",
        font=("Georgia", 36),
        fg="#d4d0c8",
        bg="#1a1a1a",
        pady=24,
    )
    prompt.pack()

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

    hint = tk.Label(
        frame,
        text="press enter to continue",
        font=("Georgia", 13),
        fg="#555",
        bg="#1a1a1a",
        pady=16,
    )
    hint.pack()

    def submit(event=None):
        answer = entry_var.get().strip()
        if not answer:
            return
        log_entry(answer)
        root.destroy()

    entry.bind("<Return>", submit)

    # Escape does nothing — you have to answer
    root.bind("<Escape>", lambda e: None)

    root.mainloop()


if __name__ == "__main__":
    import time
    while True:
        try:
            show_prompt()
            break
        except Exception:
            time.sleep(1)
