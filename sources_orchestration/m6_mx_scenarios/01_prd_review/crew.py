"""Scenario 01 — Galaxy AI 신기능 PRD 리뷰.

PM이 작성한 PRD 문서를 받아 4개 도메인 Worker(Spec·Feasibility·UX·Risk)가 평가하고
Manager가 통합 리뷰 리포트를 산출한다.
"""

from pydantic import BaseModel, Field
from typing import List, Literal
from crewai import Agent, Task
import sys
from pathlib import Path

SCENARIOS_ROOT = Path(__file__).resolve().parent.parent
if str(SCENARIOS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCENARIOS_ROOT))

from scenario_common import (
    configure_runtime,
    create_hierarchical_crew,
    require_openai_key,
    text_file_reader,
)


# === 출력 스키마 ===
class PRDFindingItem(BaseModel):
    domain: Literal["Spec", "Feasibility", "UX", "Risk"]
    severity: int = Field(ge=1, le=5)
    issue: str
    recommendation: str


class PRDReviewReport(BaseModel):
    prd_id: str
    overall_score: int = Field(ge=1, le=10)
    findings: List[PRDFindingItem]
    summary: str


# === Manager ===
prd_manager = Agent(
    role="PRD Review Manager",
    goal="PRD 문서를 4개 도메인 Worker에 분배하고 통합 리뷰 리포트를 산출한다",
    backstory=(
        "Galaxy AI 신기능 PRD 리뷰 6년 차 시니어 PM. "
        "Spec·Feasibility·UX·Risk의 4대 차원에서 PRD 결함을 사전 식별하는 데 특화."
    ),
    allow_delegation=True,
    verbose=True,
)


# === Workers ===
spec_worker = Agent(
    role="Spec Reviewer",
    goal="PRD의 요구사항 명확성·완결성·테스트 가능성을 평가한다",
    backstory="요구사항 분석 8년 경력. 모호한 spec과 누락된 엣지 케이스를 즉시 식별.",
    allow_delegation=False,
    tools=[text_file_reader],
)

feasibility_worker = Agent(
    role="Feasibility Assessor",
    goal="PRD의 기술적 실현 가능성·일정·자원 적정성을 평가한다",
    backstory="Android 플랫폼 10년차 시니어. 기술 부채와 인프라 제약을 우선 검토.",
    allow_delegation=False,
    tools=[text_file_reader],
)

ux_worker = Agent(
    role="UX Reviewer",
    goal="PRD의 사용자 시나리오·접근성·일관성을 평가한다",
    backstory="UX 디자이너 7년차. 사용자 여정의 단절과 디자인 시스템 위반을 식별.",
    allow_delegation=False,
    tools=[text_file_reader],
)

risk_worker = Agent(
    role="Risk Assessor",
    goal="PRD의 비즈니스·법적·보안 리스크를 식별한다",
    backstory="제품 리스크 관리 9년차. GDPR·접근성 법규·경쟁사 IP를 우선 검토.",
    allow_delegation=False,
    tools=[text_file_reader],
)


# === Tasks ===
prd_review_task = Task(
    description=(
        "text_file_reader 로 {prd_path} 의 PRD 문서를 읽고 4개 도메인 Worker에 분배한다. "
        "각 Worker의 결과를 통합하여 PRDReviewReport 를 산출한다."
    ),
    expected_output="PRDReviewReport 객체",
    output_pydantic=PRDReviewReport,
    agent=prd_manager,
)


prd_review_crew = create_hierarchical_crew(
    manager=prd_manager,
    workers=[spec_worker, feasibility_worker, ux_worker, risk_worker],
    tasks=[prd_review_task],
    manager_llm="gpt-4o",
)


if __name__ == "__main__":
    configure_runtime()
    if not require_openai_key():
        sys.exit(1)
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--prd", required=True, help="PRD 문서 경로")
    parser.add_argument("--prd-id", required=True)
    args = parser.parse_args()

    result = prd_review_crew.kickoff(
        inputs={"prd_path": args.prd, "prd_id": args.prd_id}
    )
    print(result)
