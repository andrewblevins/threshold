#!/usr/bin/env python3
"""
Short-lived Tk prompt subprocess.

Spawned by threshold_daemon.py on each screen unlock. Opens a fullscreen
Tk window, waits for the user to type and submit an answer, prints the
answer (a single line) to stdout, and exits.

Running Tk in a subprocess isolates it from the long-lived daemon, so
known Tk-on-macOS crashes during display-configuration changes
(TKContentView resetTkLayerBitmapContext) can't take down the observer.
"""

import sys
import tkinter as tk


def main() -> int:
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

    answer_holder: dict[str, str] = {}

    def submit(event=None):
        answer = entry_var.get().strip()
        if not answer:
            return
        answer_holder["answer"] = answer
        root.destroy()

    entry.bind("<Return>", submit)
    root.bind("<Escape>", lambda e: None)
    root.protocol("WM_DELETE_WINDOW", lambda: None)

    root.mainloop()

    answer = answer_holder.get("answer", "")
    if not answer:
        return 1
    sys.stdout.write(answer + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
