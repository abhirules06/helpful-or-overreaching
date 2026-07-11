"""
resume_study2.py — Fill missing Study 2 transcripts for a given model.
Usage: python3 resume_study2.py <model>   e.g. gpt, claude
"""
import glob, json, os, uuid, sys
sys.path.insert(0, os.path.dirname(__file__))

from run_study2 import run_task, save_transcript, snapshot_task_sandbox, restore_task_sandbox, _task_sandbox_dir
import sandbox2.tools2 as sandbox_tools

MODEL = sys.argv[1] if len(sys.argv) > 1 else (print("Usage: resume_study2.py <model>") or sys.exit(1))
TARGET = 5
TASKS = [f"task_{i:02d}" for i in range(1, 13)]
CONDITIONS = ["baseline", "boundary"]
TRANSCRIPT_DIR = os.path.join(os.path.dirname(__file__), "logs2", "transcripts")
TASKS_DIR = os.path.join(os.path.dirname(__file__), "tasks2")

counts = {}
for p in glob.glob(os.path.join(TRANSCRIPT_DIR, "*.json")):
    with open(p) as f:
        try: t = json.load(f)
        except: continue
    if t.get("study") != 2 or t.get("model") != MODEL: continue
    key = (t["task"], t["condition"])
    counts[key] = counts.get(key, 0) + 1

total_needed = sum(max(0, TARGET - counts.get((task, cond), 0))
                   for task in TASKS for cond in CONDITIONS)
print(f"{MODEL} Study 2 — {total_needed} runs needed\n")

for task in TASKS:
    task_file = os.path.join(TASKS_DIR, f"{task}.txt")
    with open(task_file) as f:
        task_text = f.read().strip()
    task_sandbox = _task_sandbox_dir(task)
    sandbox_tools.set_sandbox_dir(task_sandbox)
    snapshot_task_sandbox(task)

    for cond in CONDITIONS:
        have = min(counts.get((task, cond), 0), TARGET)
        need = TARGET - have
        if need <= 0:
            continue
        for i in range(need):
            run_id = str(uuid.uuid4())
            print(f"[{MODEL}] {task} [{cond}] rep {have+i+1}/{TARGET} -> {run_id}")
            restore_task_sandbox(task)
            sandbox_tools.set_sandbox_dir(task_sandbox)
            try:
                transcript = run_task(task_text, task, MODEL, cond, run_id)
                path = save_transcript(transcript, TRANSCRIPT_DIR)
                print(f"  saved -> {path}")
            except Exception as e:
                print(f"  ERROR: {e}")

    restore_task_sandbox(task)

print("\nDone.")
