# OneDay Curriculum v3.1 — 정답 코드 모음

본 디렉터리는 "Codex × Claude Code: 차세대 개발 파이프라인 — 에이전틱 코딩 1일 집중 실전" 교육의 모듈별 정답 코드와 사후 학습 자료다.

## 폴더 구성

| 폴더 | 모듈 | 산출물 |
|---|---|---|
| `m2_harness_demo/` | M2 하네스 엔지니어링 | Skill MD + sample 코드 + 검토 리포트 양식 |
| `m4_role_cards/` | M4 CrewAI + 설계 | Manager + 5 Worker Role Card 완전체 |
| `m5_build_triage_crew/` | M5 라이브 구현 ★ | 동작하는 Build Triage Crew 완전체 |
| `m6_integration/` | M6 통합 + MCP | Production 수준 통합본 (Pydantic·Tool·Hook·MCP·LangSmith) |
| `m6_mx_scenarios/` | M6 미니 핸즈온 | MX 5종 시나리오 예시 답안 |
| `skills_templates/` | 사후 자료 | 본인 업무에 즉시 적용 가능한 Skill 템플릿 3종 |

## 사전 준비

### 1. Python 환경

```bash
python --version       # 3.10 이상 권장
python -m venv .venv
.venv\Scripts\activate # Windows
# source .venv/bin/activate  # macOS/Linux
```

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 환경변수 설정

`.env.example` 을 `.env` 로 복사하고 본인 키 값을 채운다.

```bash
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux
```

필수 환경변수:
- `OPENAI_API_KEY` — CrewAI의 LLM 호출에 사용
- `LANGCHAIN_API_KEY` — LangSmith 추적 (M6에서 사용, 선택)
- `ANTHROPIC_API_KEY` — Claude Code 호출 (선택)

## 실행 순서

각 폴더의 `README.md` 에 모듈별 실행 절차가 명시되어 있다.

```bash
# 본 교육 핵심 산출물 — Build Triage Crew 실행
cd m5_build_triage_crew
python -m crew.main --diff ./sample_diff.txt --build-id GA-2026-05-20

# Production 통합본 실행
cd ../m6_integration
python run_with_tracing.py
```

## 라이선스

본 코드는 교육 목적으로 작성되었다. 운영 환경 적용 전 다음을 확인한다:
- 사내 보안 정책 (외부 LLM 호출 가능 여부)
- API 키 관리 (절대 코드에 평문 노출 금지)
- 비용 모니터링 (LangSmith 대시보드 활용)

## 변경 이력

| 버전 | 일자 | 내용 |
|---|---|---|
| v3.1 | 2026-05-20 | 초안 — 2차수 VOC + 1차 협의 반영 |
