"""
extract_examples.py — Pull 4-6 concrete scope-creep transcripts for the report.

Picks the most illustrative runs where high-severity scope creep occurred,
formats them as readable Markdown, and saves to scoring/examples.md.

Usage:
    python extract_examples.py
    python extract_examples.py --max 6
"""

import argparse
import json
import os
import glob

from score import load_transcripts, score_run, tools_used_in_transcript, TASK_MINIMAL_TOOLS

SCORING_DIR = os.path.join(os.path.dirname(__file__), "scoring")


def format_transcript_for_report(transcript: dict, score: dict) -> str:
    task_name = transcript.get("task", "?")
    model = transcript.get("model", "?")
    condition = transcript.get("condition", "?")
    run_id = transcript.get("run_id", "?")[:8]

    lines = [
        f"### Example: `{task_name}` | model=`{model}` | condition=`{condition}` | run=`{run_id}`",
        "",
        f"**Task:**",
        f"> {transcript.get('task_text', '').strip()}",
        "",
        f"**Minimal tools needed:** `{sorted(TASK_MINIMAL_TOOLS.get(task_name, {})  )}`",
        f"**Tools actually used:** `{score['tools_used']}`",
        f"**Extra tools (scope creep):** `{score['extra_tools']}`",
        f"**High-severity creep:** {'YES — ' + str(score['high_severity_tools']) if score['has_high_severity_creep'] else 'no'}",
        "",
        "**Transcript (relevant turns):**",
        "",
    ]

    for turn in transcript.get("turns", []):
        role = turn.get("role", "?")
        content = turn.get("content", [])
        for block in content:
            btype = block.get("type", "")
            if btype == "text" and block.get("text", "").strip():
                lines.append(f"**{role.upper()}:** {block['text'].strip()}")
                lines.append("")
            elif btype == "tool_use":
                name = block.get("name", "?")
                inputs = block.get("input", {})
                lines.append(f"**{role.upper()} → tool call:** `{name}`")
                if inputs:
                    lines.append(f"```json\n{json.dumps(inputs, indent=2)}\n```")
                lines.append("")
            elif btype == "tool_result":
                content_text = block.get("content", "")
                snippet = content_text[:300] + ("..." if len(content_text) > 300 else "")
                lines.append(f"**TOOL RESULT:** `{snippet}`")
                lines.append("")

    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--max", type=int, default=6, help="Max examples to extract")
    args = parser.parse_args()

    transcripts = load_transcripts()
    if not transcripts:
        print("No transcripts found.")
        return

    # Score all transcripts that have a known task
    scored = []
    for t in transcripts:
        task_name = t.get("task", "unknown")
        if task_name not in TASK_MINIMAL_TOOLS:
            continue
        s = score_run(t, TASK_MINIMAL_TOOLS[task_name])
        scored.append((t, s))

    # Prefer: high-severity creep first, then any creep; prefer baseline (to show natural behavior)
    def priority(item):
        _, s = item
        return (
            -int(s["has_high_severity_creep"]),  # high-sev first
            -int(s["has_scope_creep"]),
            0 if s["condition"] == "baseline" else 1,
            -len(s["extra_tools"]),
        )

    scored.sort(key=priority)
    examples = [item for item in scored if item[1]["has_scope_creep"]][:args.max]

    if not examples:
        print("No scope creep found in transcripts — nothing to extract.")
        return

    os.makedirs(SCORING_DIR, exist_ok=True)
    out_path = os.path.join(SCORING_DIR, "examples.md")

    with open(out_path, "w") as f:
        f.write("# Scope Creep Examples\n\n")
        f.write(f"The following {len(examples)} runs show clear scope creep "
                f"(tools used beyond the task's minimal requirements).\n\n")
        f.write("---\n\n")
        for t, s in examples:
            f.write(format_transcript_for_report(t, s))

    print(f"Wrote {len(examples)} examples to {out_path}")


if __name__ == "__main__":
    main()
