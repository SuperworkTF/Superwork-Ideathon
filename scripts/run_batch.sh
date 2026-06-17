#!/usr/bin/env bash
# 아이디어톤 심사 배치 — cron 래퍼.
# 예) 10분마다:  */10 * * * * /path/scripts/run_batch.sh >> /path/logs/cron.log 2>&1
set -euo pipefail

# 스크립트 위치 기준으로 프로젝트 루트 해석 (cron의 임의 CWD 대응)
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# cron 의 최소 PATH 대응 — claude CLI(구독 백엔드) 탐색 경로 보강
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

PY="$ROOT/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  echo "[$(date '+%F %T')] ERROR: venv 없음 ($PY). 먼저 'python3 -m venv .venv && .venv/bin/pip install -r requirements.txt'" >&2
  exit 1
fi

mkdir -p "$ROOT/logs"
echo "[$(date '+%F %T')] 배치 시작"
"$PY" -m ideathon_judge run "$@"
echo "[$(date '+%F %T')] 배치 종료"
