#!/usr/bin/env bash
# run_study2_batch.sh — full Study 2 data collection for one model
# Usage: ./run_study2_batch.sh <model>   e.g. gpt, claude, gemini, grok
set -e

MODEL="$1"
if [[ -z "$MODEL" ]]; then
  echo "Usage: $0 <model>"; exit 1
fi

TASKS=(task_01 task_02 task_03 task_04 task_05 task_06
       task_07 task_08 task_09 task_10 task_11 task_12)
CONDITIONS=(baseline boundary)
REPEATS=5

cd "$(dirname "$0")"
source .venv/bin/activate

for TASK in "${TASKS[@]}"; do
  for COND in "${CONDITIONS[@]}"; do
    echo "[$(date '+%H:%M:%S')] $MODEL  $TASK  $COND"
    python3 run_study2.py \
      --task "tasks2/${TASK}.txt" \
      --condition "$COND" \
      --model "$MODEL" \
      --repeats "$REPEATS"
  done
done

echo "[$(date '+%H:%M:%S')] $MODEL COMPLETE"
