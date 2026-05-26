"""Build Triage coordination agents.

CrewAI 버전에 따라 hierarchical manager가 task executor까지 겸하면 충돌이 날 수
있으므로, 위임 전용 coordinator와 실제 실행 agent를 분리한다.
"""

from crewai import Agent, Task

from .schemas import BuildImpactScope, BuildTriageReport
from .tools import diff_reader, area_classifier


# === Delegation-only Manager Agent ===
build_coordinator = Agent(
    role="Build Triage Coordinator",
    goal=(
        "Galaxy nightly build diff를 분석해 5개 도메인 Worker(UI·Perf·Compat·L10n·Knox)에 "
        "작업을 위임하고, 실행 agent들이 산출물을 순서대로 만들도록 조율한다. "
        "직접 도구를 실행하거나 Task 산출물을 작성하지 않는다."
    ),
    backstory=(
        "MX 사업부 빌드 안정성을 책임지는 10년 차 시니어 매니저다. "
        "Galaxy 시리즈의 nightly build 리스크를 매일 평가해 왔으며, "
        "5개 도메인 전문가의 평가를 통합해 비즈니스 영향을 판단하는 데 특화되어 있다. "
        "보수적 판단보다 근거 기반 의사결정을 우선한다."
    ),
    allow_delegation=True,
    verbose=True,
    tools=[],
    max_iter=8,
)


# === Scope Analyzer Agent ===
build_scope_analyzer = Agent(
    role="Build Scope Analyzer",
    goal=(
        "Galaxy nightly build diff를 읽어 변경 범위와 도메인별 영향 모듈을 분류한다. "
        "최종 산출물은 Worker 위임에 필요한 BuildImpactScope 객체다."
    ),
    backstory=(
        "Galaxy nightly build diff를 매일 읽는 빌드 분석 전문가다. "
        "변경 파일을 UI·Perf·Compat·L10n·Knox 관점으로 빠르게 분류하고, "
        "각 Worker가 검토할 입력을 과하거나 부족하지 않게 정리한다."
    ),
    allow_delegation=False,
    verbose=True,
    tools=[diff_reader, area_classifier],
    max_iter=4,
)


# === Report Integrator Agent ===
build_integrator = Agent(
    role="Build Triage Integrator",
    goal=(
        "5개 도메인 Worker의 평가를 통합하여 GO/NO_GO 판정과 우선순위를 산출한다. "
        "최종 산출물은 임원 보고가 가능한 수준의 정형 리포트(BuildTriageReport)다."
    ),
    backstory=(
        "MX 사업부 빌드 안정성을 책임지는 10년 차 시니어 리뷰어다. "
        "도메인별 위험을 비즈니스 영향과 릴리스 차단 여부로 번역하는 데 특화되어 있다."
    ),
    allow_delegation=False,
    verbose=True,
    tools=[],
    max_iter=4,
)


# Backward-compatible name for older examples that import build_manager.
build_manager = build_coordinator


# === Task — 변경 영역 분석 ===
analyze_diff_task = Task(
    description=(
        "1) diff_reader 로 {diff_path} 의 nightly build diff 전체를 읽는다.\n"
        "2) area_classifier 로 변경 영역을 5개 도메인(UI·Perf·Compat·L10n·Knox)에 분류한다.\n"
        "3) 각 도메인의 영향 모듈 목록과 분류 근거를 정리한다.\n"
        "4) Worker들이 참조할 BuildImpactScope 스키마로 산출한다.\n"
        "\n"
        "build_id={build_id} 를 그대로 포함한다."
    ),
    expected_output=(
        "BuildImpactScope 객체 — build_id, total_changed_files, domains_to_review, summary."
    ),
    output_pydantic=BuildImpactScope,
    agent=build_scope_analyzer,
)


# === Task — Worker 평가 통합 ===
integrate_triage_task = Task(
    description=(
        "BuildImpactScope와 5개 WorkerVerdict 결과를 통합해 최종 빌드 판정을 작성한다.\n"
        "\n"
        "통합 절차:\n"
        "1) UI·Perf·Compat·L10n·Knox WorkerVerdict의 severity와 rationale을 비교한다.\n"
        "2) severity 4 이상 도메인이 있으면 NO_GO 또는 HOLD 가능성을 우선 검토한다.\n"
        "3) 비즈니스 영향과 수정 예상 시간을 종합해 priority(P1~P5)를 결정한다.\n"
        "4) Worker별 suggested_fix_hours를 합산해 estimated_fix_hours를 추정한다.\n"
        "5) Worker 간 근거가 일관되면 confidence='high', 불충분하면 'low'로 둔다.\n"
        "\n"
        "build_id={build_id} 를 그대로 리포트에 포함한다."
    ),
    expected_output=(
        "BuildTriageReport 객체 — build_id, decision(GO/NO_GO/HOLD), priority(1~5), "
        "worker_verdicts(5개), summary(50자 이상), estimated_fix_hours, confidence."
    ),
    output_pydantic=BuildTriageReport,
    agent=build_integrator,
)
