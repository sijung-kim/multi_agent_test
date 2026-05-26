"""L10n Worker — 다국어·지역화 회귀 평가."""

from crewai import Agent, Task

from ..schemas import WorkerVerdict
from ..tools import diff_reader, module_lookup, severity_estimator
from ..manager import analyze_diff_task


l10n_worker = Agent(
    role="Localization Specialist",
    goal=(
        "build diff에서 다국어·지역화 회귀를 식별한다. "
        "특히 RTL 언어 정렬·문자열 리소스 누락·플레이스홀더 불일치·날짜·통화 포맷을 우선 확인한다. "
        "최종 산출물은 WorkerVerdict(domain='L10n') 객체다."
    ),
    backstory=(
        "Galaxy 다국어 지원 5년 차 전문가다. 한국어·영어·아랍어·히브리어 등 "
        "120개 언어의 회귀 패턴을 숙지하고 있으며, "
        "특히 RTL(Right-to-Left) 정렬과 플레이스홀더 매핑 오류를 즉시 식별한다. "
        "values-* 리소스 파일의 누락과 불일치를 우선 검토한다."
    ),
    allow_delegation=False,
    tools=[diff_reader, module_lookup, severity_estimator],
    verbose=True,
    max_iter=4,
)

l10n_task = Task(
    description=(
        "Manager가 분배한 L10n 도메인 영향 모듈에 대해 지역화 회귀 위험을 평가한다.\n"
        "\n"
        "평가 절차:\n"
        "1) module_lookup 으로 values-* 리소스의 일관성을 확인한다.\n"
        "2) 플레이스홀더 ({0} %s 등) 매핑 누락 패턴을 식별한다.\n"
        "3) RTL 언어 정렬·날짜·통화·전화번호 포맷 변경 영향을 분석한다.\n"
        "4) rationale 에 영향받는 언어 범위와 사용자 비율 추정을 명시한다.\n"
        "\n"
        "결과는 WorkerVerdict(domain='L10n') 형식으로 산출한다."
    ),
    expected_output="WorkerVerdict 객체 (domain='L10n')",
    output_pydantic=WorkerVerdict,
    agent=l10n_worker,
    context=[analyze_diff_task],
)
