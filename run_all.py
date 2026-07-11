"""
run_all.py — Run every task × model × condition × N repeats.

Usage:
    python run_all.py                          # all tasks, all models, 5 reps
    python run_all.py --models claude gpt      # subset of models
    python run_all.py --tasks task_01 task_02  # subset of tasks
    python run_all.py --repeats 3
    python run_all.py --dry-run                # print plan without hitting APIs
"""

import argparse
import os
import sys
import uuid

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))
from run_task import MODELS, run_task, save_transcript, _snapshot_sandbox, _restore_sandbox  # noqa: E402

TASKS_DIR = os.path.join(os.path.dirname(__file__), "tasks")
TRANSCRIPT_DIR = os.path.join(os.path.dirname(__file__), "logs", "transcripts")
CONDITIONS = ["baseline", "boundary"]


def discover_tasks():
    files = sorted(f for f in os.listdir(TASKS_DIR) if f.endswith(".txt"))
    return [os.path.splitext(f)[0] for f in files]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", choices=list(MODELS.keys()),
                        default=list(MODELS.keys()))
    parser.add_argument("--tasks", nargs="+", default=None,
                        help="Task names (e.g. task_01 task_02). Default: all.")
    parser.add_argument("--conditions", nargs="+", choices=CONDITIONS, default=CONDITIONS)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--dry-run", action="store_true",
                        help="Print plan without making API calls")
    args = parser.parse_args()

    all_tasks = discover_tasks()
    tasks = args.tasks if args.tasks else all_tasks
    invalid = [t for t in tasks if t not in all_tasks]
    if invalid:
        print(f"Unknown tasks: {invalid}")
        sys.exit(1)

    total = len(tasks) * len(args.models) * len(args.conditions) * args.repeats
    print(f"Plan: {len(tasks)} tasks × {len(args.models)} models × "
          f"{len(args.conditions)} conditions × {args.repeats} reps = {total} API calls\n"
          f"  Tasks:      {tasks}\n"
          f"  Models:     {args.models}\n"
          f"  Conditions: {args.conditions}")

    if args.dry_run:
        print("\n[dry-run] No API calls made.")
        return

    os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
    _snapshot_sandbox()

    done = 0
    errors = 0
    for task_name in tasks:
        task_path = os.path.join(TASKS_DIR, f"{task_name}.txt")
        with open(task_path) as f:
            task_text = f.read().strip()

        for model_key in args.models:
            for condition in args.conditions:
                for rep in range(args.repeats):
                    run_id = str(uuid.uuid4())
                    print(f"[{done+1}/{total}] {task_name} | {model_key} | {condition} "
                          f"| rep {rep+1}/{args.repeats} -> {run_id[:8]}")
                    _restore_sandbox()
                    try:
                        transcript = run_task(
                            task_text, task_name, model_key, condition, run_id
                        )
                        path = save_transcript(transcript, TRANSCRIPT_DIR)
                        print(f"  OK -> {os.path.basename(path)}")
                    except Exception as e:
                        print(f"  ERROR: {e}")
                        errors += 1
                    done += 1

    _restore_sandbox()
    print(f"\nDone. {done - errors}/{done} runs succeeded. "
          f"Transcripts in {TRANSCRIPT_DIR}")
    if errors:
        print(f"{errors} errors — check output above.")


if __name__ == "__main__":
    main()
