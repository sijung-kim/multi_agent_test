# M6 — Production 통합 (Pydantic + Tool + Hook + MCP + LangSmith)

M5의 Build Triage Crew를 운영(production) 수준으로 끌어올린 통합본. 외부 도구 통합·MCP 연동·관찰성·알림이 모두 결합되어 있다.

## 폴더 구조

```
m6_integration/
├── crew/
│   ├── tools/
│   │   ├── standard_tools.py     # @tool 다중 (diff_reader·area_classifier·slack_notifier)
│   │   └── mcp_tools.py          # MCP 통합 (filesystem 등)
│   └── production_setup.py       # 모든 요소를 묶는 진입 모듈
├── run_with_tracing.py           # LangSmith 통합 실행
├── mcp_config.json               # MCP 서버 등록 양식
└── README.md
```

## 사전 준비

### 1. MCP 서버 설치

```bash
# Filesystem MCP 서버 설치 (npm 필요)
npm install -g @modelcontextprotocol/server-filesystem
```

### 2. mcp_config.json 위치

본 폴더의 `mcp_config.json` 을 Codex CLI 설정 디렉터리에 복사:

```bash
copy mcp_config.json %USERPROFILE%\.codex\config.json   # Windows
# cp mcp_config.json ~/.codex/config.json               # macOS/Linux
```

### 3. 환경변수

`sources/.env` 에 다음이 채워져 있어야 한다:
- `OPENAI_API_KEY` (필수)
- `LANGCHAIN_API_KEY` (LangSmith 추적용)
- `SLACK_BOT_TOKEN` (Slack 알림용, 선택)

## 실행

```bash
# 1) M5 Crew 가 sys.path 에서 import 가능해야 한다 (또는 m6에 복사)
# 2) Production 통합본 실행
python run_with_tracing.py --diff ../m5_build_triage_crew/sample_diff.txt --build-id GA-2026-05-20
```

## 학습 포인트

1. **@tool 다중 정의** — 외부 시스템 호출(파일·API·Slack)을 표준 인터페이스로 통합
2. **MCP 통합** — Filesystem MCP 서버를 Worker가 호출 가능한 도구로 흡수
3. **production_crew** — M5의 Crew + 모든 도구를 결합한 운영 진입점
4. **run_with_tracing.py** — LangSmith 환경변수 + 추적 ID + 대시보드 URL 출력

## 운영 환경 적용 시 추가 고려사항

| 항목 | 대응 |
|---|---|
| API 키 관리 | secrets manager(HashiCorp Vault 등) 연동 |
| 비용 통제 | `manager_llm` 을 gpt-4o-mini 로 변경하여 비용 절감 |
| 동시성 | 여러 빌드를 병렬 평가 시 Crew 인스턴스 분리 |
| 알림 채널 | Slack 외 PagerDuty·이메일·웹훅 추가 가능 |
| 감사 로그 | `hooks.py` 의 JSON 로그를 ELK·CloudWatch 등에 전송 |
