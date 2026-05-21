"""Code Review Coordinator — 위임 전용 매니저.

실행자(executor)와 위임자(delegator)를 분리하는 패턴.
- code_review_coordinator : allow_delegation=True, tools=[], Task 없음
  → Crew(manager_agent=...) 로만 전달; agents 목록에는 포함하지 않는다.
- 4개 Worker(Analyzer·Risk·Reviewer·Notifier) 가 실제 Task를 실행한다.
"""

from crewai import Agent, LLM

# 전체 Crew에서 공유하는 LLM 인스턴스 — 파일을 import 해서 재사용한다.
CLAUDE = LLM(model="anthropic/claude-sonnet-4-5-20250929")


# === Delegation-only Coordinator ===
code_review_coordinator = Agent(
    role="Code Review Coordinator",
    goal=(
        "Galaxy 앱 소스코드 diff를 분석하는 4개 Worker(Analyzer·Risk·Reviewer·Notifier)에 "
        "작업을 위임하고, 각 Worker가 순서대로 산출물을 만들도록 조율한다. "
        "직접 도구를 실행하거나 Task 산출물을 작성하지 않는다."
    ),
    backstory=(
        "Galaxy 앱 개발팀의 10년 차 수석 리뷰 매니저다. "
        "소스코드 변경 분석·위험 탐지·리뷰 코멘트·티켓 발행까지 "
        "4단계 리뷰 파이프라인 전체를 설계하고 운영해 왔다. "
        "각 전문가 Worker가 자기 역할에 집중할 수 있도록 명확히 위임하는 것을 "
        "최우선 가치로 삼는다."
    ),
    allow_delegation=True,   # ★ Coordinator만 True
    verbose=True,
    tools=[],                # ★ 직접 실행 없음 — 위임 전용
    llm=CLAUDE,
    max_iter=15,
)

