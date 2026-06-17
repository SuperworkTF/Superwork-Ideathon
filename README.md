# 사내 아이디어톤 심사 시스템 (ideathon-judge)

구글폼 연동 시트에서 신규 아이디어를 **배치로 수집** → Claude 기반 **다관점·비판적 심사**
(+ 시장반응 시뮬레이션) → **정량 점수 0~100** → **파일로 기록**.

```
구글폼 ──> 연동 시트(CSV export) ──> [배치] 신규 diff ──> 심사 에이전트 ──> results/
                                          │                   │
                                    state.json(멱등)     ┌────┴─────┐
                                                    패널 5인 채점   시장반응 시뮬
                                                         └────┬─────┘
                                              차원 가중합 + 시장 blend = 최종점수
```

---

## 1. 빠른 시작

```bash
# 1) 가상환경 + 의존성
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt

# 2) (선택) 설정 — API 키 없이 바로 동작 (Claude 구독 사용)
cp .env.example .env        # 값 안 채워도 됨

# 3) 시트 아이디어 + 심사 상태 확인
.venv/bin/python -m ideathon_judge list

# 4) 신규 아이디어 배치 심사 (이미 심사한 건 자동 스킵)
.venv/bin/python -m ideathon_judge run

# 구조만 점검 (LLM 미호출, mock 점수)
.venv/bin/python -m ideathon_judge run --dry-run
```

### 심사 백엔드 (기본 `auto`)

| 조건 | 백엔드 | 설명 |
|---|---|---|
| **기본 (키 없음)** | **claude CLI** | 로그인된 **Claude 구독을 공유**해 실심사 — API 키 불필요 |
| `ANTHROPIC_API_KEY` 설정 | API | Anthropic API 직접 호출 (속도·병렬 유리) |
| `--dry-run` | mock | LLM 미호출, 구조 점검용 가짜 점수 |

> 강제 전환: `JUDGE_BACKEND=cli|api|mock`. 구독 모드는 `claude` CLI 로그인 상태(설치된 Claude Code) 필요.
> 구독 모드는 호출당 수초~수십초(아이디어당 6호출) — cron 배치엔 충분.

---

## 2. 명령어

| 명령 | 설명 |
|---|---|
| `run` | 신규 아이디어 배치 심사 → 리포트/리더보드 기록 |
| `run --dry-run` | mock LLM (API 키 불필요, 구조 점검) |
| `run --limit N` | 이번 실행 최대 N건만 |
| `run --force` | 이미 심사한 것도 재심사 |
| `run --no-market` | 시장반응 시뮬레이션 생략 (비용↓) |
| `list` | 시트 아이디어 + 심사 여부 목록 |
| `show <idea_id>` | 해당 아이디어 심사 리포트 출력 |
| `leaderboard` | 리더보드 출력 |
| `reset --yes` | 심사 상태 초기화(전체 재심사 대상화) |

---

## 3. 심사 설계 (다관점·정량)

### 평가 차원 8 (가중치 합 1.0) — `config/rubric.yaml`
문제정의·심각도(0.16) · 타겟명확성(0.10) · 시장성/수요(0.15) · 차별성/해자(0.15) ·
실현가능성(0.14) · 사업성/수익모델(0.10) · 기대효과/임팩트(0.10) · 리스크통제(0.10)

각 차원 **0~10 정수**, 점수 인플레 방지용 **앵커**를 프롬프트에 주입.

### 심사 패널 5인 (독립 채점 후 가중 집계)
- **VC 투자자**(0.25) — 수익률·확장성·해자, 기각 사유부터
- **타겟 유저**(0.25) — 내가 쓰고 돈 낼까, 10x인가
- **기술 리드**(0.20) — 구현 복잡도·의존성·운영비
- **비판가/레드팀**(0.15) — 실패 이유 적극 발굴(점수 인플레 억제)
- **PM/디자이너**(0.15) — 온보딩·채택장벽·리텐션

### 최종 점수
```
panel100   = Σ(차원점수 × 차원가중) × 10            # 패널 가중합, 0~100
final      = 0.20 × 시장반응점수 + 0.80 × panel100  # market_blend=0.20
```
판정 밴드: **STRONG PASS**(≥80) · **PASS**(≥66) · **REVISE**(≥50) · **REJECT**(<50)

> 모든 가중치·앵커·밴드·blend 비율은 `config/rubric.yaml` 에서 조정 가능(코드 수정 불필요).

---

## 4. 시장반응 시뮬레이션 (`market_sim.py`)

`config/personas.yaml` 의 다양성 축(연령/기술친숙도/가격민감도/현재대안/사용맥락/회의성향)으로
타겟 유저 설명에서 **합성 소비자 N명(기본 10)**을 생성하고 각자의 반응을 정량화:

- `adopt_probability` (시도확률), `pay_probability` (유료전환), `willingness_to_pay` (월 지불의향 KRW),
  `excitement` (0~10), `top_objection`, `switching_barrier`
- 집계 → **수요 점수 0~100** + 채택률/지불의향 중앙값/주요 거부이유 분포

> **왜 직접 구현?** 요청하신 `MiroFish-Offline` 적용성은 [`docs/MIROFISH_REVIEW.md`](docs/MIROFISH_REVIEW.md) 참고.
> 결론: **직접 적용 부적합**(Neo4j+Ollama+GPU 과중, 짧은 아이디어 입력 불가, 점수 미산출, AGPL 라이선스).
> 핵심 아이디어(합성 페르소나 패널)만 차용해 경량·정량 버전으로 자체 구현.

---

## 5. 배치 자동화 (cron)

`scripts/run_batch.sh` 가 venv 활성화 + 실행 + 로그를 처리. 예) **10분마다 신규 확인·심사**:

```cron
*/10 * * * * /Users/hosoo/working/projects/superwork_idea/scripts/run_batch.sh >> /Users/hosoo/working/projects/superwork_idea/logs/cron.log 2>&1
```

멱등 설계라 매번 돌려도 **신규 제출만** 심사합니다(`results/state.json` 기준).

---

## 6. 산출물 (`results/`)

| 파일 | 내용 |
|---|---|
| `reports/<점수>_<id>_<서비스명>.md` | 아이디어별 상세 심사 리포트 |
| `leaderboard.md` | 점수순 순위표 |
| `scores.csv` | 평탄화 표(엑셀용, 차원별 점수 포함) |
| `scores.json` | 전체 구조화 데이터(패널/시장/결함 포함) |
| `state.json` | 심사 완료 추적(멱등 키) |

---

## 7. 시트 접근

연동 시트는 **"링크가 있는 모든 사용자 = 뷰어"** 공유 상태여야 CSV export 로 읽힙니다(현재 가능 확인됨).
URL 은 `.env` 의 `SHEET_CSV_URL` 로 교체 가능. 컬럼 순서는 구글폼 고정 순서(9열)를 위치 기반 매핑합니다.

## 8. 테스트

```bash
.venv/bin/python -m unittest discover -s tests -t .
```

## 9. 운영 권장

- **재현성**: API 모드는 temperature(0.2) 고정으로 안정적. 구독(CLI) 모드는 temperature 미적용이라 실행 간 약간의 변동 가능 — 최종 판정 밴드는 견고.
- **캘리브레이션**: 사람이 미리 순위 매긴 5~10건으로 가중치 보정 후 본 심사 권장.
- **비용/속도**: 아이디어당 LLM 호출 ≈ 패널 5 + 시장 1 = 6회. 구독(CLI) 모드는 호출당 수초~수십초. `--no-market` 으로 호출 5회로 절감.
