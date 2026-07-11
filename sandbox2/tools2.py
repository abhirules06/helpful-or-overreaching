"""
Sandbox tools for Study 2.

Identical contract to Study 1's tools.py but with a configurable per-task
sandbox directory instead of a single global one. Call set_sandbox_dir()
before each task run; the runner handles this automatically.
"""

import json
import os
from datetime import datetime, timezone

_sandbox_dir: str = ""

LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "logs2", "tool_calls.jsonl")


def set_sandbox_dir(path: str):
    global _sandbox_dir
    _sandbox_dir = os.path.abspath(path)


def get_sandbox_dir() -> str:
    return _sandbox_dir


def _log_call(run_id: str, tool_name: str, arguments: dict, result_summary: str):
    entry = {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool": tool_name,
        "arguments": arguments,
        "result_summary": result_summary,
    }
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def _safe_path(filename: str) -> str:
    path = os.path.normpath(os.path.join(_sandbox_dir, filename))
    if not path.startswith(_sandbox_dir):
        raise ValueError("Path escapes sandbox")
    return path


def list_files(run_id: str) -> str:
    files = sorted(os.listdir(_sandbox_dir))
    result = "\n".join(files) if files else "(empty)"
    _log_call(run_id, "list_files", {}, result)
    return result


def read_file(run_id: str, filename: str) -> str:
    path = _safe_path(filename)
    if not os.path.exists(path):
        result = f"ERROR: {filename} does not exist"
    else:
        with open(path) as f:
            result = f.read()
    _log_call(run_id, "read_file", {"filename": filename}, result[:200])
    return result


def write_file(run_id: str, filename: str, content: str) -> str:
    path = _safe_path(filename)
    with open(path, "w") as f:
        f.write(content)
    result = f"Wrote {len(content)} chars to {filename}"
    _log_call(run_id, "write_file", {"filename": filename, "content_preview": content[:200]}, result)
    return result


def delete_file(run_id: str, filename: str) -> str:
    path = _safe_path(filename)
    if os.path.exists(path):
        os.remove(path)
        result = f"Deleted {filename}"
    else:
        result = f"ERROR: {filename} does not exist"
    _log_call(run_id, "delete_file", {"filename": filename}, result)
    return result


def rename_file(run_id: str, old_filename: str, new_filename: str) -> str:
    old_path = _safe_path(old_filename)
    new_path = _safe_path(new_filename)
    if os.path.exists(old_path):
        os.rename(old_path, new_path)
        result = f"Renamed {old_filename} -> {new_filename}"
    else:
        result = f"ERROR: {old_filename} does not exist"
    _log_call(run_id, "rename_file",
              {"old_filename": old_filename, "new_filename": new_filename}, result)
    return result


def send_email(run_id: str, to: str, subject: str, body: str) -> str:
    result = f"[MOCK] Email logged (not sent) to {to}: '{subject}'"
    _log_call(run_id, "send_email",
              {"to": to, "subject": subject, "body_preview": body[:200]}, result)
    return result


def create_calendar_event(run_id: str, title: str, datetime_str: str, attendees: str = "") -> str:
    result = f"[MOCK] Calendar event logged (not created): '{title}' at {datetime_str}"
    _log_call(run_id, "create_calendar_event",
              {"title": title, "datetime": datetime_str, "attendees": attendees}, result)
    return result


def delete_calendar_event(run_id: str, title: str) -> str:
    result = f"[MOCK] Calendar event deletion logged (not executed): '{title}'"
    _log_call(run_id, "delete_calendar_event", {"title": title}, result)
    return result
