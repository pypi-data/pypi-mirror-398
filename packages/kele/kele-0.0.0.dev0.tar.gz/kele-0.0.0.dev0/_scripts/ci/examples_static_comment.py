#!/usr/bin/env python3
"""Generate a folded PR comment comparing examples/static.py outputs."""

from __future__ import annotations

import argparse
import pathlib
import re

MARKER = "<!-- examples-static-report -->"
SUMMARY_TEXT = "Comparison of examples run results between the current branch and main"

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

# Table parsing constants (avoid magic numbers)
MIN_TABLE_LINES = 3
TABLE_HEADER_LINES = 2
MIN_SPLIT_PARTS = 4
STATUS_INDEX = 3
FAIL_STATUS = "失败"


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from text."""
    return ANSI_RE.sub("", text)


def extract_table(log_text: str) -> str:
    """
    Extract only the table block from examples/static.py output.

    Start: line begins with '文件名' and contains '运行时间'
    End:   before '失败样例' (if present)
    """
    text = strip_ansi(log_text)
    lines = text.splitlines()

    start: int | None = None
    for i, line in enumerate(lines):
        if line.startswith("文件名") and ("运行时间" in line):
            start = i
            break

    if start is None:
        return "Table header not found in output."

    end = len(lines)
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("失败样例"):
            end = i
            break

    return "\n".join(lines[start:end]).rstrip()


def count_failures_from_table(table_text: str) -> tuple[int | None, int | None]:
    """
    Best-effort parse the extracted table.

    Returns:
      (total_rows, failed_rows) if it looks parseable, otherwise (None, None).
    """
    lines = table_text.splitlines()
    if len(lines) < MIN_TABLE_LINES:
        return (None, None)

    # header + dashed line + rows...
    rows = lines[TABLE_HEADER_LINES:]
    total = 0
    failed = 0

    for row in rows:
        row_str = row.strip()
        if not row_str:
            continue

        parts = row_str.split()
        if len(parts) < MIN_SPLIT_PARTS:
            continue

        total += 1
        if parts[STATUS_INDEX] == FAIL_STATUS:
            failed += 1

    return (total, failed)


def badge(exit_code: str, failed_count: int | None) -> str:
    """Return a simple PASS/FAIL badge for the PR summary."""
    if exit_code == "0" and (failed_count is None or failed_count == 0):
        return "✅ PASS"
    return "❌ FAIL"


def main() -> None:
    """CLI entrypoint: read logs, extract tables, and write pr_comment.md."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--curr-log", required=True)
    ap.add_argument("--base-log", required=True)
    ap.add_argument("--curr-sha", required=True)
    ap.add_argument("--base-sha", required=True)
    ap.add_argument("--base-ref", required=True)
    ap.add_argument("--curr-exit", required=True)
    ap.add_argument("--base-exit", required=True)
    ap.add_argument("--out", default="pr_comment.md")
    args = ap.parse_args()

    curr_log = pathlib.Path(args.curr_log).read_text(encoding="utf-8", errors="replace")
    base_log = pathlib.Path(args.base_log).read_text(encoding="utf-8", errors="replace")

    curr_table = extract_table(curr_log)
    base_table = extract_table(base_log)

    _, curr_failed = count_failures_from_table(curr_table)
    _, base_failed = count_failures_from_table(base_table)

    curr_badge = badge(args.curr_exit, curr_failed)
    base_badge = badge(args.base_exit, base_failed)

    md: list[str] = []

    # Keep marker at the very top so find-comment can reliably locate it.
    md.extend((MARKER, "<details>", f"<summary><b>{SUMMARY_TEXT}</b></summary>", "", "### Examples Static Report", "",
               f"- **Current (PR head)** `{args.curr_sha}` — {curr_badge}",
               f"- **Base ({args.base_ref})** `{args.base_sha}` — {base_badge}", "",
               "<details><summary><b>Current (PR head) table</b></summary>", "",
               "```text", curr_table, "```", "</details>", "", "<details><summary><b>Base table</b></summary>", "",
               "```text", base_table, "```", "</details>", "", "</details>", ""))

    pathlib.Path(args.out).write_text("\n".join(md), encoding="utf-8")


if __name__ == "__main__":
    main()
