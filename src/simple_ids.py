#!/usr/bin/env python3
"""
simple_ids.py

Small educational IDS prototype that tails a log file and raises alerts
when repeated failed login attempts from the same IP exceed a threshold.

Usage:
  python src/simple_ids.py /path/to/logfile

If no logfile is provided it will watch `boss/ids_sample.log` in the repo.

This is a light, local prototype for learning/demonstration purposes only.
"""

import sys
import re
import time
from collections import deque, defaultdict

# Parameters
THRESHOLD = 5       # failed attempts
WINDOW = 60         # seconds
SLEEP = 1.0         # poll interval seconds

FAILED_PATTERNS = [
    r"Failed password",
    r"Failed login",
    r"authentication failure",
    r"Invalid user",
    r"login failed",
]

IP_RE = re.compile(r"(\d{1,3}(?:\.\d{1,3}){3})")


def tail_f(filename):
    """Yield new lines appended to filename (like tail -f)."""
    with open(filename, "r", encoding="utf-8", errors="ignore") as f:
        # Go to end of file
        f.seek(0, 2)
        while True:
            line = f.readline()
            if not line:
                time.sleep(SLEEP)
                continue
            yield line.rstrip("\n")


def is_failed_login(line):
    lower = line.lower()
    for p in FAILED_PATTERNS:
        if p.lower() in lower:
            return True
    return False


def extract_ip(line):
    m = IP_RE.search(line)
    return m.group(1) if m else None


def run(logfile):
    attempts = defaultdict(lambda: deque())  # ip -> deque[timestamps]

    print(f"Watching {logfile} (threshold={THRESHOLD} in {WINDOW}s)")
    for line in tail_f(logfile):
        if not is_failed_login(line):
            continue
        ip = extract_ip(line) or "unknown"
        now = time.time()
        q = attempts[ip]
        q.append(now)
        # drop old entries
        while q and (now - q[0] > WINDOW):
            q.popleft()
        if len(q) >= THRESHOLD:
            print(f"[ALERT] {len(q)} failed logins from {ip} within {WINDOW}s")
            # optional: reset counters for that IP to avoid spamming
            q.clear()


if __name__ == "__main__":
    logfile = sys.argv[1] if len(sys.argv) > 1 else "boss/ids_sample.log"
    try:
        run(logfile)
    except FileNotFoundError:
        print(f"Log file not found: {logfile}")
        print("Create the file and append lines matching failed login patterns to test.")
    except KeyboardInterrupt:
        print("\nExiting")
