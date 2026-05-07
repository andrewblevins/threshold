# threshold

A small macOS background app that asks you a single question every time you unlock your Mac:

> **What are you here for?**

You type a one-line answer, press Enter, and get on with your day. The window goes away. Your answer is appended to a local JSONL log so you can read back later what you've been showing up for.

---

## What it actually is

- **macOS only.** It uses the system's "screen unlocked" notification, so it won't run on Linux or Windows.
- A long-running Python process (a "launch agent") that sits idle in the background and listens for unlocks.
- When you unlock, it spawns a fullscreen prompt. When you submit, it logs and disappears.
- Everything is local. No network, no telemetry. The log file is `log.jsonl` next to the script.

A *launch agent* is just macOS's way of running a small program in the background for your user account. You install one by dropping a `.plist` file into `~/Library/LaunchAgents/` and asking macOS to load it.

---

## Install

You'll need Python 3.13 (or change the version in the plist below) and the Xcode Command Line Tools.

```bash
git clone https://github.com/andrewblevins/threshold.git ~/threshold
cd ~/threshold
python3.13 -m venv .venv
.venv/bin/pip install pyobjc
```

Then create `~/Library/LaunchAgents/threshold.plist` with the following contents (replace `<YOUR_USERNAME>` with your macOS username — `whoami` will tell you):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>threshold</string>

    <key>ProgramArguments</key>
    <array>
        <string>/Users/<YOUR_USERNAME>/threshold/.venv/bin/python3.13</string>
        <string>/Users/<YOUR_USERNAME>/threshold/threshold_daemon.py</string>
    </array>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/Users/<YOUR_USERNAME>/threshold/daemon.log</string>

    <key>StandardErrorPath</key>
    <string>/Users/<YOUR_USERNAME>/threshold/daemon.log</string>

    <key>ProcessType</key>
    <string>Interactive</string>
</dict>
</plist>
```

Load it:

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/threshold.plist
```

Lock your screen (Ctrl+Cmd+Q) and unlock — the prompt should appear.

To trigger it manually without locking:

```bash
kill -USR1 $(launchctl list | awk '/threshold/ {print $1}')
```

To uninstall:

```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/threshold.plist
rm ~/Library/LaunchAgents/threshold.plist
```

---

## Reading your log

Each answer becomes one line of JSON in `log.jsonl`:

```json
{"timestamp": "2026-05-07T10:03:17.123456", "answer": "finish the draft"}
```

Open it in any editor, or:

```bash
jq -r '"\(.timestamp)  \(.answer)"' ~/threshold/log.jsonl | tail -20
```

---

## License

Public domain (Unlicense). See `LICENSE`.
