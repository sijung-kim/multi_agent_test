"""UI Worker — 손코딩 산출물 (M5 슬라이드 3~6).

본 Worker는 M5에서 학생이 직접 타이핑한다. 다른 4 Worker는 이 패턴을 참조하여 Codex가 가속 생성한다.
"""

from crewai import Agent, Task

from ..schemas import WorkerVerdict
from ..tools import diff_reader, module_lookup, severity_estimator
from ..manager import analyze_diff_task


# === UI Specialist Agent ===
ui_worker = Agent(
    role="UI Specialist",
    goal=(
        "build diff에서 UI 컴포넌트 변경을 식별하고, 각 변경의 회귀 위험을 1~5로 산정한다. "
        "특히 다크 모드 토글·다국어 정렬·접근성 위반·터치 영역 변경을 우선 확인한다. "
        "최종 산출물은 WorkerVerdict(domain='UI') 객체다."
    ),
    backstory=(
        "Galaxy UI/UX 5년 차 시니어 엔지니어다. "
        "다크 모드 회귀·다국어 정렬·접근성 위반·터치 영역 변경 등 "
        "엔드 유저 체감 회귀를 즉시 감지하는 패턴 라이브러리를 보유한다. "
        "사용자 신뢰를 최우선 가치로 두며, 디자인 시스템 일관성을 엄격히 검토한다."
    ),
    allow_delegation=False,
    tools=[diff_reader, module_lookup, severity_estimator],
    verbose=True,
    max_iter=4,
)


# === UI 영향 평가 Task ===
ui_task = Task(
    description=(
        "Manager가 분배한 UI 도메인 영향 모듈 목록을 기반으로 회귀 위험을 평가한다.\n"
        "\n"
        "평가 절차:\n"
        "1) module_lookup 으로 각 영향 모듈의 실제 존재와 규모를 확인한다.\n"
        "2) severity_estimator 로 1차 추정치를 받고, 도메인 컨텍스트와 결합해 조정한다.\n"
        "3) 다크 모드·다국어·접근성·터치 영역 4대 회귀 패턴에 대해 변경을 분석한다.\n"
        "4) rationale 에 발견된 위험과 근거를 20~500자로 서술한다.\n"
        "5) suggested_fix_hours 를 추정한다 (간단 0.5h ~ 복잡 24h).\n"
        "\n"
        "결과는 WorkerVerdict(domain='UI') 형식으로 산출한다."
    ),
    expected_output=(
        "WorkerVerdict 객체 — domain='UI', severity(1~5), affected_modules(list), "
        "rationale(20~500자), suggested_fix_hours(optional)."
    ),
    output_pydantic=WorkerVerdict,
    agent=ui_worker,
    context=[analyze_diff_task],   # ★ Manager Task에 의존 — 핸드오프 명시
)
