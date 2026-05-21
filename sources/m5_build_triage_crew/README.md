# M5 — Build Triage Crew (본 교육 핵심 산출물)

Galaxy nightly build diff를 받아 5개 도메인 Worker가 영향을 분석하고, Manager가 통합해 GO/NO_GO 판정을 산출하는 멀티에이전트 시스템.

## 폴더 구조

```
m5_build_triage_crew/
├── crew/
│   ├── __init__.py
│   ├── schemas.py          # Pydantic 출력 스키마
│   ├── manager.py          # 위임 전용 Coordinator + 실행 Agent
│   ├── workers/
│   │   ├── __init__.py
│   │   ├── ui_worker.py
│   │   ├── perf_worker.py
│   │   ├── compat_worker.py
│   │   ├── l10n_worker.py
│   │   └── knox_worker.py
│   ├── tools.py            # @tool 도구 (diff_reader 등)
│   ├── hooks.py            # 실행 전/후 콜백
│   └── main_crew.py        # Crew 조립
├── main.py                 # 실행 엔트리
└── sample_diff.txt         # 테스트용 샘플 입력
```

## 실행

```bash
# 1) 가상환경 진입 + 의존성 설치 (sources/README.md 참고)

# 2) 환경변수 설정 (.env 파일)
#    OPENAI_API_KEY 필수

# 3) Build Triage Crew 실행
python -m crew.main --diff ./sample_diff.txt --build-id GA-2026-05-20

# 또는 main.py 직접 실행
python main.py --diff ./sample_diff.txt --build-id GA-2026-05-20
```

## 산출물

실행 종료 시 다음이 출력된다:

```
[trace_id] build-20260520-153201-a1b2c3
[task_start] Build Scope Analyzer
[task_end]   ok · tokens=2,140 · duration_s=8.3
[task_start] UI Specialist
[task_end]   ok · tokens=1,820 · duration_s=6.1
...
[decision] GO (P2)
```

## 학습 포인트

1. **Pydantic 스키마** — 자유 텍스트 출력을 정형 객체로 강제 (schemas.py)
2. **Manager/Executor 분리** — 위임 전용 `build_coordinator`만 `allow_delegation=True`, 실제 Task 실행 Agent는 `allow_delegation=False` (manager.py)
3. **Worker의 의존성** — `context=[parent_task]`로 핸드오프 명시 (workers/*.py)
4. **Hook 콜백** — `on_task_start`/`on_task_end`로 실행 흐름 관찰 (hooks.py)
5. **5 Worker 일괄 통합** — Worker 결과를 `Build Triage Integrator`가 최종 `BuildTriageReport`로 통합 (main_crew.py)
