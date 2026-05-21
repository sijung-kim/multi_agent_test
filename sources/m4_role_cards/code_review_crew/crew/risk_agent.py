"""Risk Agent — 보안·성능·호환성 이슈와 위험을 탐지한다.

migration_worksheet.md 예시 1 · TO-BE Agent 2.
"""

from crewai import Agent, Task

from .schemas import RiskReport
from .tools import code_diff_reader, risk_pattern_scanner
from .analyzer import analyze_task
from .manager import CLAUDE


# === Risk Agent ===
risk_agent = Agent(
    role="Security & Risk Specialist",
    goal=(
        "소스코드 변경에서 보안 취약점, 성능 병목, 호환성 문제를 탐지한다. "
        "각 위험 항목에 대해 카테고리·심각도·권장 조치를 산출한다. "
        "최종 산출물은 RiskReport 객체다."
    ),
    backstory=(
        "Galaxy 보안 인증(Knox) 및 성능 최적화 경력 8년의 시니어 전문가다. "
        "OWASP Mobile Top 10, Android 보안 모범 사례, "
        "Galaxy 성능 기준선을 체득하고 있으며, "
        "코드 한 줄에서 잠재적 취약점을 발견하는 직관을 갖추었다. "
        "위험을 과소 평가하지 않고, 근거 기반으로 심각도를 결정한다."
    ),
    allow_delegation=False,
    tools=[code_diff_reader, risk_pattern_scanner],
    llm=CLAUDE,
    verbose=True,
    max_iter=4,
)


# === 위험 탐지 Task ===
risk_task = Task(
    description=(
        "Analyzer가 파악한 변경 범위를 기반으로 보안·성능·호환성 위험을 탐지한다.\n"
        "\n"
        "탐지 절차:\n"
        "1) code_diff_reader 로 {diff_path} 의 diff를 다시 읽는다.\n"
        "2) risk_pattern_scanner 로 1차 자동 패턴 스캔을 수행한다.\n"
        "3) Analyzer가 식별한 affected_areas 와 guideline_violations 를 참조해 "
           "패턴 스캔 결과를 맥락화한다.\n"
        "4) 각 위험 항목에 대해 RiskItem(category, severity, file_path, description, recommendation)을 작성한다.\n"
        "   - Security: 인증·암호화·입력 검증·민감정보 노출 관련\n"
        "   - Performance: 메인 스레드 IO·중첩 루프·메모리 누수 관련\n"
        "   - Compatibility: deprecated API·minSdk 위반·AndroidX 미전환 관련\n"
        "5) 전체 위험 중 가장 높은 심각도를 overall_severity 로 결정한다.\n"
        "6) 탐지 결과를 20자 이상으로 요약한다.\n"
    ),
    expected_output=(
        "RiskReport 객체 — risks(RiskItem 목록), overall_severity(최고 심각도), summary(20자 이상)."
    ),
    output_pydantic=RiskReport,
    agent=risk_agent,
    context=[analyze_task],   # ★ Analyzer 결과에 의존
)
