"""Scenario 05 — Customer Care 시나리오 자동화.

고객 문의를 받아 Intent 분류 → Resolver 응답 작성 → Escalation 판정의 3단계로 처리한다.
README의 M6 시나리오 공통 패턴에 맞춰 Process.hierarchical 로 조립한다.
"""

from pydantic import BaseModel, Field
from typing import List, Literal
from crewai import Agent, Task
import sys
from pathlib import Path

SCENARIOS_ROOT = Path(__file__).resolve().parent.parent
if str(SCENARIOS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCENARIOS_ROOT))

from scenario_common import configure_runtime, create_hierarchical_crew, require_openai_key


IntentType = Literal[
    "BillingIssue", "TechSupport", "FeatureRequest",
    "AccountAccess", "Complaint", "GeneralInquiry"
]


class IntentClassification(BaseModel):
    customer_id: str
    raw_message: str
    detected_intent: IntentType
    confidence: float = Field(ge=0.0, le=1.0)
    extracted_entities: dict = Field(default_factory=dict)


class ResolverResponse(BaseModel):
    intent: IntentType
    response_draft: str = Field(min_length=30)
    suggested_actions: List[str] = Field(default_factory=list)
    knowledge_links: List[str] = Field(default_factory=list)


class EscalationDecision(BaseModel):
    needs_escalation: bool
    reason: str
    target_team: str = ""
    sla_hours: int = 24


class CustomerCareCase(BaseModel):
    case_id: str
    classification: IntentClassification
    response: ResolverResponse
    escalation: EscalationDecision


# === Agents ===
care_manager = Agent(
    role="Customer Care Manager",
    goal="고객 문의를 3개 Worker에 분배하고 최종 CustomerCareCase를 산출한다",
    backstory="CS 운영 자동화 7년차. 문의 유형별 응답 품질과 에스컬레이션 기준을 통합 관리.",
    allow_delegation=True,
    verbose=True,
)

intent_classifier = Agent(
    role="Intent Classifier",
    goal="고객 메시지에서 의도를 6종 중 1개로 분류하고 엔티티를 추출한다",
    backstory="고객 문의 NLU 5년차. 한국어 비격식체와 줄임말까지 정확 분류.",
    allow_delegation=False,
)

resolver = Agent(
    role="Resolver",
    goal="분류된 intent에 맞춰 고객 응답 초안과 후속 조치를 작성한다",
    backstory="CS 시니어 8년차. 친절도와 정확성의 균형을 잡는 표준 응대 패턴 보유.",
    allow_delegation=False,
)

escalator = Agent(
    role="Escalation Judge",
    goal="응답 초안과 intent를 검토하여 에스컬레이션 필요 여부를 결정한다",
    backstory="CS 운영 매니저 6년차. SLA 위반 가능성과 법적 리스크를 즉시 식별.",
    allow_delegation=False,
)


care_task = Task(
    description=(
        "고객 메시지: {message}\n"
        "customer_id: {customer_id}\n"
        "case_id={case_id}\n"
        "\n"
        "1) Intent Classifier Worker에게 의도 분류와 엔티티 추출을 위임한다.\n"
        "2) Resolver Worker에게 응답 초안과 후속 조치 작성을 위임한다.\n"
        "3) Escalation Judge Worker에게 에스컬레이션 필요 여부 판단을 위임한다.\n"
        "4) 세 결과를 CustomerCareCase 객체로 통합한다."
    ),
    expected_output="CustomerCareCase 객체",
    output_pydantic=CustomerCareCase,
    agent=care_manager,
)


care_crew = create_hierarchical_crew(
    manager=care_manager,
    workers=[intent_classifier, resolver, escalator],
    tasks=[care_task],
    manager_llm="gpt-4o",
)


if __name__ == "__main__":
    configure_runtime()
    if not require_openai_key():
        sys.exit(1)
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--message", required=True, help="고객 문의 메시지")
    parser.add_argument("--customer-id", required=True)
    parser.add_argument("--case-id", required=True)
    args = parser.parse_args()

    result = care_crew.kickoff(inputs={
        "message": args.message,
        "customer_id": args.customer_id,
        "case_id": args.case_id,
    })
    print(result)
