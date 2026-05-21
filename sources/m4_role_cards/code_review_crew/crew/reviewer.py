"""Reviewer Agent — 심각도 분류 및 리뷰 코멘트를 작성한다.

migration_worksheet.md 예시 1 · TO-BE Agent 3.
"""

from crewai import Agent, Task

from .schemas import ReviewReport
from .analyzer import analyze_task
from .risk_agent import risk_task
from .manager import CLAUDE


# === Reviewer Agent ===
reviewer_agent = Agent(
    role="Code Reviewer",
    goal=(
        "Analyzer의 변경 범위와 Risk Agent의 위험 탐지 결과를 종합하여 "
        "심각도별 리뷰 코멘트를 작성하고 APPROVE/REQUEST_CHANGES/COMMENT 결정을 내린다. "
        "최종 산출물은 ReviewReport 객체다."
    ),
    backstory=(
        "Galaxy 앱 팀에서 10년간 수백 건의 코드 리뷰를 진행한 수석 리뷰어다. "
        "기술적 정확성뿐 아니라 유지보수성·가독성·팀 표준 준수를 균형 있게 평가한다. "
        "개발자가 이해하고 행동할 수 있는 명확하고 건설적인 코멘트를 작성하는 것을 원칙으로 한다. "
        "위험 데이터를 비즈니스 영향으로 번역하여 우선순위를 결정한다."
    ),
    allow_delegation=False,
    tools=[],   # 분석 결과 통합이 주 업무 — 추가 도구 불필요
    llm=CLAUDE,
    verbose=True,
    max_iter=4,
)


# === 리뷰 코멘트 작성 Task ===
review_task = Task(
    description=(
        "Analyzer와 Risk Agent의 결과를 통합하여 최종 리뷰 판정과 코멘트를 작성한다.\n"
        "\n"
        "작성 절차:\n"
        "1) Analyzer의 AnalysisResult(변경 범위·가이드라인 위반)와 "
           "Risk Agent의 RiskReport(위험 목록·전체 심각도)를 검토한다.\n"
        "2) 각 위험 항목과 가이드라인 위반에 대해 ReviewComment를 작성한다.\n"
        "   - file_path: 해당 파일 경로\n"
        "   - severity: 심각도 (Critical/High/Medium/Low/Info)\n"
        "   - comment: 10~500자의 구체적이고 건설적인 코멘트 (한국어)\n"
        "   - line_hint: 관련 코드 위치 힌트 (있으면 포함)\n"
        "3) 전체 리뷰 결정을 내린다:\n"
        "   - APPROVE: 위험 없음 또는 Info 수준만 존재\n"
        "   - COMMENT: Low/Medium 위험 — 배포 차단 불필요하나 개선 권장\n"
        "   - REQUEST_CHANGES: High/Critical 위험 존재 — 수정 후 재검토 필요\n"
        "4) 리뷰 총평을 30자 이상으로 작성한다.\n"
    ),
    expected_output=(
        "ReviewReport 객체 — decision(APPROVE/REQUEST_CHANGES/COMMENT), "
        "comments(ReviewComment 목록), summary(30자 이상)."
    ),
    output_pydantic=ReviewReport,
    agent=reviewer_agent,
    context=[analyze_task, risk_task],   # ★ 두 선행 Task 에 의존
)
