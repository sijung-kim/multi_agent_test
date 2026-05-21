"""Scenario 05 — Customer Care 시나리오 자동화.

고객 문의를 받아 Intent 분류 → Resolver 응답 작성 → Escalation 판정의 3단계로 처리한다.
Process.sequential 패턴 (분기가 거의 없으므로 직선적 의존이 적합).
"""

from pydantic import BaseModel, Field
from typing import List, Literal
from crewai import Agent, Task, Crew, Process


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


# === Tasks (Sequential) ===
classify_task = Task(
    description=(
        "고객 메시지: {message}\n"
        "customer_id: {customer_id}\n"
        "IntentClassification 객체로 분류·엔티티 추출 결과를 산출."
    ),
    expected_output="IntentClassification 객체",
    output_pydantic=IntentClassification,
    agent=intent_classifier,
)

resolve_task = Task(
    description=(
        "분류된 intent를 받아 응답 초안과 후속 조치를 작성한다. "
        "ResolverResponse 객체로 산출."
    ),
    expected_output="ResolverResponse 객체",
    output_pydantic=ResolverResponse,
    agent=resolver,
    context=[classify_task],
)

escalation_task = Task(
    description=(
        "응답 초안과 intent를 검토하여 에스컬레이션 필요 여부와 대상 팀을 결정한다. "
        "EscalationDecision 객체로 산출."
    ),
    expected_output="EscalationDecision 객체",
    output_pydantic=EscalationDecision,
    agent=escalator,
    context=[classify_task, resolve_task],
)


# === Crew (Sequential 패턴) ===
care_crew = Crew(
    agents=[intent_classifier, resolver, escalator],
    tasks=[classify_task, resolve_task, escalation_task],
    process=Process.sequential,   # ★ 직선적 의존이라 sequential 채택
    verbose=True,
)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--message", required=True, help="고객 문의 메시지")
    parser.add_argument("--customer-id", required=True)
    args = parser.parse_args()

    result = care_crew.kickoff(inputs={
        "message": args.message,
        "customer_id": args.customer_id,
    })
    print(result)
