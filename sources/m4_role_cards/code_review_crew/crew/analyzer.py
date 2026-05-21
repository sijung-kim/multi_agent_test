"""Analyzer Agent — 지침서를 읽고 소스코드의 변경 범위를 파악한다.

migration_worksheet.md 예시 1 · TO-BE Agent 1.
"""

from crewai import Agent, Task

from .schemas import AnalysisResult
from .tools import code_diff_reader, guideline_reader
from .manager import CLAUDE


# === Analyzer Agent ===
analyzer_agent = Agent(
    role="Code Change Analyzer",
    goal=(
        "개발 가이드라인을 숙지한 뒤, 소스코드 diff를 읽어 변경 범위를 정확히 파악한다. "
        "변경된 파일 목록, 영향받는 기능 영역, 가이드라인 위반 여부를 산출한다. "
        "최종 산출물은 AnalysisResult 객체다."
    ),
    backstory=(
        "Galaxy 앱 개발팀에서 5년간 코드 아키텍처를 담당해 온 시니어 엔지니어다. "
        "팀의 코딩 컨벤션과 보안·성능 가이드라인을 누구보다 깊이 이해하고 있으며, "
        "변경 사항이 전체 시스템에 미치는 영향을 빠르게 식별하는 데 탁월하다. "
        "가이드라인 준수를 팀 문화의 핵심으로 여긴다."
    ),
    allow_delegation=False,
    tools=[code_diff_reader, guideline_reader],
    llm=CLAUDE,
    verbose=True,
    max_iter=4,
)


# === 변경 범위 분석 Task ===
analyze_task = Task(
    description=(
        "PR/빌드의 소스코드 변경 범위를 분석한다.\n"
        "\n"
        "분석 절차:\n"
        "1) guideline_reader 로 {guideline_path} 의 개발 가이드라인을 읽고 핵심 체크리스트를 파악한다.\n"
        "   (파일이 없으면 도구가 기본 Galaxy 가이드라인을 반환한다.)\n"
        "2) code_diff_reader 로 {diff_path} 의 소스코드 diff를 읽는다.\n"
        "3) 변경된 파일 목록을 추출하고, 각 파일의 change_type(added/modified/deleted)과 변경 라인 수를 파악한다.\n"
        "4) 변경이 영향을 미치는 기능 영역(예: Auth, UI, Network, DB, Security)을 식별한다.\n"
        "5) 가이드라인 위반 사항(하드코딩 문자열, 명명 규칙 위반 등)을 기록한다.\n"
        "6) 변경 범위 전체를 20자 이상으로 요약한다.\n"
        "\n"
        "pr_id={pr_id} 컨텍스트를 summary에 포함한다."
    ),
    expected_output=(
        "AnalysisResult 객체 — changed_files(목록), total_changes(라인 수), "
        "affected_areas(영역 목록), guideline_violations(위반 목록), summary(20자 이상)."
    ),
    output_pydantic=AnalysisResult,
    agent=analyzer_agent,
)
