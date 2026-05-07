#!/usr/bin/env python3
"""
Threshold daemon — long-running process that listens for screen unlock
and shows the intention prompt by spawning a short-lived subprocess.

Architecture:
- A single Python process stays alive, holding the unlock observer.
- Trigger: com.apple.screenIsUnlocked from the distributed notification
  center (fires on every screen unlock, lid-open-with-lock, etc).
- On each unlock (or SIGUSR1 for manual trigger), spawn threshold_prompt.py
  as a child process. The child runs Tk, blocks until submit, prints the
  answer to stdout, and exits. The daemon writes the logged entry.
- Subprocess isolation: Tk on macOS occasionally crashes in
  TKContentView::resetTkLayerBitmapContext during display-configuration
  changes (sleep/wake, color profile shifts, monitor changes). Keeping
  Tk out of the daemon process means those crashes can't take down the
  unlock observer.
"""

import json
import signal
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path

import objc
from AppKit import NSObject, NSRunLoop, NSDate
from Foundation import NSDefaultRunLoopMode, NSDistributedNotificationCenter

HERE = Path(__file__).parent
LOG_PATH = HERE / "log.jsonl"
PROMPT_SCRIPT = HERE / "threshold_prompt.py"


def log_entry(answer: str):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "answer": answer.strip(),
    }
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def show_prompt():
    """Spawn the Tk prompt subprocess; log whatever answer it returns."""
    try:
        result = subprocess.run(
            [sys.executable, str(PROMPT_SCRIPT)],
            capture_output=True,
            text=True,
        )
    except Exception as exc:
        print(f"threshold: failed to spawn prompt: {exc}", file=sys.stderr)
        return

    if result.returncode != 0:
        # Non-zero means the user closed without submitting, or the child
        # crashed. Either way: don't log, don't retry.
        if result.stderr:
            print(result.stderr, file=sys.stderr, end="")
        return

    answer = result.stdout.strip()
    if answer:
        log_entry(answer)


# Coordinate triggers from multiple sources (AppKit unlock, SIGUSR1) into
# a single serialized prompt. The main loop polls the flag.
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
            show_prompt()  # blocks until child exits


if __name__ == "__main__":
    main()
