#!/usr/bin/env python3
"""Audit a command-line program against the mechanically checkable clig.dev rules.

Only harmless invocations are made: --help, -h, --version, an unknown flag, and
no arguments with stdin closed. The real actions of the target are never run
on purpose, but a badly behaved program could still do something when invoked
with no arguments; use --skip-no-args for tools where that would be unsafe.

Usage:
  audit_cli.py [--json] [--timeout SECONDS] [--skip-no-args] -- COMMAND [ARGS...]

Examples:
  audit_cli.py -- mytool
  audit_cli.py -- mytool deploy
  audit_cli.py --json -- python -m myapp

Exit codes: 0 all checks passed (warnings allowed), 1 at least one check failed,
2 usage error or the command could not be started.
"""

import argparse
import json
import os
import re
import select
import shutil
import subprocess
import sys
import time

ANSI = re.compile(rb"\x1b\[[0-9;?]*[A-Za-z]")
BOGUS_FLAG = "--clig-audit-no-such-flag"


class Result:
    def __init__(self):
        self.checks = []

    def add(self, name, status, detail=""):
        self.checks.append({"check": name, "status": status, "detail": detail})


def run(cmd, extra, timeout, env=None, stdin=subprocess.DEVNULL):
    e = dict(os.environ)
    e.pop("FORCE_COLOR", None)
    e.pop("CLICOLOR_FORCE", None)
    if env:
        e.update(env)
    start = time.monotonic()
    try:
        p = subprocess.run(cmd + extra, stdin=stdin, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, timeout=timeout, env=e)
        return {"code": p.returncode, "out": p.stdout, "err": p.stderr,
                "timed_out": False, "secs": time.monotonic() - start}
    except subprocess.TimeoutExpired as t:
        return {"code": None, "out": t.stdout or b"", "err": t.stderr or b"",
                "timed_out": True, "secs": timeout}


def run_pty(cmd, extra, timeout, env):
    """Run with stdout/stderr attached to a pseudo-terminal; return combined bytes."""
    try:
        import pty
    except ImportError:
        return None
    e = dict(os.environ)
    e.pop("FORCE_COLOR", None)
    e.setdefault("TERM", "xterm-256color")
    if e.get("TERM") == "dumb":
        e["TERM"] = "xterm-256color"
    e.update(env)
    master, slave = pty.openpty()
    try:
        p = subprocess.Popen(cmd + extra, stdin=subprocess.DEVNULL, stdout=slave,
                             stderr=slave, env=e, close_fds=True)
    except OSError:
        os.close(master)
        os.close(slave)
        return None
    os.close(slave)
    buf = b""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        r, _, _ = select.select([master], [], [], 0.1)
        if r:
            try:
                chunk = os.read(master, 65536)
            except OSError:
                break
            if not chunk:
                break
            buf += chunk
        elif p.poll() is not None:
            break
    if p.poll() is None:
        p.kill()
    p.wait()
    os.close(master)
    return buf


def text(b):
    return b.decode("utf-8", "replace")


def audit(cmd, timeout, skip_no_args):
    res = Result()

    # 1. --help
    h = run(cmd, ["--help"], timeout)
    if h["timed_out"]:
        res.add("--help responds", "fail", f"timed out after {timeout}s")
        return res
    if h["code"] == 0 and h["out"].strip():
        res.add("--help exits 0 and prints to stdout", "pass")
    elif h["code"] == 0 and h["err"].strip():
        res.add("--help exits 0 and prints to stdout", "warn",
                "help went to stderr; requested help is output and belongs on stdout (so it can be piped to a pager or grep)")
    else:
        res.add("--help exits 0 and prints to stdout", "fail",
                f"exit code {h['code']}, stdout {len(h['out'])} bytes")
    help_text = text(h["out"] or h["err"])

    # 2. -h
    s = run(cmd, ["-h"], timeout)
    if s["code"] == 0 and (s["out"].strip() or s["err"].strip()):
        res.add("-h shows help", "pass")
    else:
        res.add("-h shows help", "fail", f"exit code {s['code']}; -h should mean help and nothing else")

    # 3. -h wins over other flags
    hb = run(cmd, [BOGUS_FLAG, "--help"], timeout)
    if hb["code"] == 0 and (hb["out"].strip() or hb["err"].strip()):
        res.add("--help works when appended to any command line", "pass")
    else:
        res.add("--help works when appended to any command line", "warn",
                f"'{BOGUS_FLAG} --help' exited {hb['code']}; users append -h to half-typed commands")

    # 4. Help content heuristics
    low = help_text.lower()
    res.add("help includes examples", "pass" if "example" in low else "warn",
            "" if "example" in low else "no 'example' section found; lead with examples")
    has_url = re.search(r"https?://", help_text) is not None
    res.add("help links to docs or issue tracker", "pass" if has_url else "warn",
            "" if has_url else "no URL found in help text")
    if ANSI.search(h["out"]):
        res.add("no ANSI escapes when stdout is piped", "fail",
                "--help output contains escape codes even though stdout is not a TTY")
    else:
        res.add("no ANSI escapes when stdout is piped", "pass")

    # 5. --version
    v = run(cmd, ["--version"], timeout)
    if v["code"] == 0 and (v["out"].strip() or v["err"].strip()):
        res.add("--version works", "pass", text(v["out"] or v["err"]).strip().splitlines()[0][:80])
    else:
        res.add("--version works", "warn", f"exit code {v['code']}")

    # 6. Unknown flag
    b = run(cmd, [BOGUS_FLAG], timeout)
    if b["timed_out"]:
        res.add("unknown flag fails fast", "fail", "hung on an unknown flag")
    else:
        if b["code"] == 0:
            res.add("unknown flag exits non-zero", "fail", "exited 0; scripts can't detect the mistake")
        else:
            res.add("unknown flag exits non-zero", "pass", f"exit code {b['code']}")
        if b["err"].strip() and not b["out"].strip():
            res.add("usage errors go to stderr, not stdout", "pass")
        elif b["out"].strip():
            res.add("usage errors go to stderr, not stdout", "fail",
                    "error text was written to stdout and would be piped into the next program")
        else:
            res.add("usage errors go to stderr, not stdout", "warn", "no error message at all")
        err = text(b["err"])
        if "Traceback (most recent call last)" in err or re.search(r"^\s+at .+:\d+:\d+\)?$", err, re.M) or "panicked at" in err:
            res.add("no stack trace for usage errors", "fail", "a raw stack trace was shown for a simple usage error")
        else:
            res.add("no stack trace for usage errors", "pass")

    # 7. No args, stdin closed
    if not skip_no_args:
        n = run(cmd, [], timeout)
        if n["timed_out"]:
            res.add("no args with no stdin doesn't hang", "fail",
                    f"still running after {timeout}s with stdin closed")
        else:
            res.add("no args with no stdin doesn't hang", "pass", f"exit code {n['code']}")
            if n["code"] != 0 and not (n["out"].strip() or n["err"].strip()):
                res.add("no-args failure explains itself", "fail", "failed silently")

    # 8. Color under a TTY with NO_COLOR
    if sys.platform != "win32":
        normal = run_pty(cmd, ["--help"], timeout, {})
        nc = run_pty(cmd, ["--help"], timeout, {"NO_COLOR": "1"})
        if nc is None:
            res.add("NO_COLOR honored", "skip", "pseudo-terminal unavailable")
        elif ANSI.search(nc):
            res.add("NO_COLOR honored", "fail", "escape codes emitted on a TTY with NO_COLOR=1")
        elif normal is not None and ANSI.search(normal):
            res.add("NO_COLOR honored", "pass", "colors on a TTY, none with NO_COLOR=1")
        else:
            res.add("NO_COLOR honored", "pass", "no color used in help at all")
    return res


def main():
    ap = argparse.ArgumentParser(
        prog="audit_cli.py",
        description="Audit a CLI against the checkable clig.dev rules.",
        epilog="Example: audit_cli.py -- mytool deploy",
    )
    ap.add_argument("--json", action="store_true", help="print results as JSON on stdout")
    ap.add_argument("--timeout", type=float, default=5.0, help="seconds per invocation (default: 5)")
    ap.add_argument("--skip-no-args", action="store_true",
                    help="don't run the command with no arguments (use if that would do real work)")
    ap.add_argument("command", nargs=argparse.REMAINDER, help="the command to audit, after --")
    a = ap.parse_args()
    cmd = a.command[1:] if a.command[:1] == ["--"] else a.command
    if not cmd:
        ap.print_usage(sys.stderr)
        print("audit_cli.py: error: give the command to audit after --, e.g. audit_cli.py -- mytool",
              file=sys.stderr)
        return 2
    if shutil.which(cmd[0]) is None and not os.path.exists(cmd[0]):
        print(f"audit_cli.py: error: command not found: {cmd[0]}", file=sys.stderr)
        return 2

    print(f"Auditing: {' '.join(cmd)}", file=sys.stderr)
    res = audit(cmd, a.timeout, a.skip_no_args)
    failed = any(c["status"] == "fail" for c in res.checks)

    if a.json:
        json.dump({"command": cmd, "passed": not failed, "checks": res.checks}, sys.stdout, indent=2)
        print()
    else:
        marks = {"pass": "PASS", "warn": "WARN", "fail": "FAIL", "skip": "SKIP"}
        for c in res.checks:
            line = f"{marks[c['status']]:4}  {c['check']}"
            if c["detail"]:
                line += f"  ({c['detail']})"
            print(line)
        counts = {k: sum(c["status"] == k for c in res.checks) for k in marks}
        print(f"\n{counts['pass']} passed, {counts['warn']} warnings, {counts['fail']} failed"
              + (f", {counts['skip']} skipped" if counts["skip"] else ""))
        print("Automated checks cover only externally visible behavior; review the code with the "
              "checklist in SKILL.md too.", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)
    except BrokenPipeError:
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        sys.exit(141)
