"""
resume_gemini.py — Run only the Gemini transcripts that are missing after
a partial batch (quota exhaustion mid-run).

Counts existing Gemini transcripts per (task, condition), then fires off
exactly the missing reps in the same normalized format as run_all.py.

Usage:
    python resume_gemini.py           # run all missing
    python resume_gemini.py --dry-run # print plan without API calls
"""

import argparse
import glob
import json
import os
import sys
import uuid
from collections import defaultdict

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))
from run_task import run_task, save_transcript, _snapshot_sandbox, _restore_sandbox  # noqa: E402

TASKS_DIR = os.path.join(os.path.dirname(__file__), "tasks")
TRANSCRIPT_DIR = os.path.join(os.path.dirname(__file__), "logs", "transcripts")
TARGET_REPS = 5
MODEL_KEY = "gemini"
CONDITIONS = ["baseline", "boundary"]


def count_existing():
    counts = defaultdict(lambda: defaultdict(int))
    for path in glob.glob(os.path.join(TRANSCRIPT_DIR, "*.json")):
        with open(path) as f:
            t = json.load(f)
        if t.get("model") != MODEL_KEY:
            continue
        counts[t["task"]][t["condition"]] += 1
    return counts


def discover_tasks():
    files = sorted(f for f in os.listdir(TASKS_DIR) if f.endswith(".txt"))
    return [os.path.splitext(f)[0] for f in files]


def build_work_plan(counts, all_tasks):
    """Return list of (task_name, condition, reps_needed)."""
    plan = []
    for task_name in all_tasks:
        for cond in CONDITIONS:
            have = counts[task_name][cond]
            need = max(0, TARGET_REPS - have)
            if need > 0:
                plan.append((task_name, cond, need))
    return plan


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    all_tasks = discover_tasks()
    counts = count_existing()
    plan = build_work_plan(counts, all_tasks)

    total = sum(n for _, _, n in plan)
    print(f"Existing Gemini transcripts: {sum(v for d in counts.values() for v in d.values())}")
    print(f"Missing runs to fill: {total}\n")
    for task_name, cond, n in plan:
        have = counts[task_name][cond]
        print(f"  {task_name} [{cond}]: have {have}, running {n} more")

    if args.dry_run:
        print("\n[dry-run] No API calls made.")
        return

    os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
    _snapshot_sandbox()

    done = 0
    errors = 0
    for task_name, condition, reps_needed in plan:
        task_path = os.path.join(TASKS_DIR, f"{task_name}.txt")
        with open(task_path) as f:
            task_text = f.read().strip()

        for rep in range(reps_needed):
            run_id = str(uuid.uuid4())
            print(f"[{done+1}/{total}] {task_name} | {MODEL_KEY} | {condition} "
                  f"| rep {rep+1}/{reps_needed} -> {run_id[:8]}")
            _restore_sandbox()
            try:
                transcript = run_task(task_text, task_name, MODEL_KEY, condition, run_id)
                path = save_transcript(transcript, TRANSCRIPT_DIR)
                print(f"  OK -> {os.path.basename(path)}")
            except Exception as e:
                print(f"  ERROR: {e}")
                errors += 1
            done += 1

    _restore_sandbox()
    print(f"\nDone. {done - errors}/{done} runs succeeded.")
    if errors:
        print(f"{errors} errors — check output above.")


if __name__ == "__main__":
    main()
