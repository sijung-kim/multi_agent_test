# M4 — Role Card (Manager + 5 Worker)

M4 모듈에서 학생이 작성한 Role Card의 정답 양식. M5에서 이 양식을 그대로 코드로 변환한다.

Role Card는 Agent 인스턴스의 사전 설계 단계로서, **role · goal · backstory** 3개 속성을 정형 양식으로 작성한 것이다.

## 폴더 구성

```
m4_role_cards/
├── README.md
├── build_manager.py        # Build Triage Manager
└── workers/
    ├── ui_worker.py        # UI Specialist
    ├── perf_worker.py      # Performance Specialist
    ├── compat_worker.py    # Compatibility Specialist
    ├── l10n_worker.py      # Localization Specialist
    └── knox_worker.py      # Knox Security Specialist
```

## Role Card 작성 원칙

| 속성 | 작성 원칙 |
|---|---|
| **role** | 1줄 직책명 — Specialist · Manager · Engineer 등 명사형 |
| **goal** | 1~3문장 목표 — "무엇을 산출하는가" 명확히 |
| **backstory** | 2~4문장 배경 — 의사결정 권위 + 우선 가치 명시 |
| **allow_delegation** | 위임 전용 Manager=True · Task 실행 Worker/Integrator=False (Hierarchical 패턴) |

## M5 연결

본 폴더의 Role Card는 M5의 `crew/manager.py` 및 `crew/workers/*.py` 에 대응된다. CrewAI 버전에 따라 manager가 실행자와 위임자를 동시에 맡으면 충돌할 수 있으므로, M5에서는 위임 전용 Coordinator와 실제 Task 실행 Agent를 분리한다.
