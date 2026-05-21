"""Compat Worker — Android SDK 호환성 회귀 평가."""

from crewai import Agent, Task

from ..schemas import WorkerVerdict
from ..tools import diff_reader, module_lookup, severity_estimator
from ..manager import analyze_diff_task


compat_worker = Agent(
    role="Compatibility Specialist",
    goal=(
        "build diff에서 Android SDK 호환성 회귀를 식별한다. "
        "minSdk·targetSdk·deprecated API 사용·하위 호환성 깨짐을 우선 확인한다. "
        "최종 산출물은 WorkerVerdict(domain='Compat') 객체다."
    ),
    backstory=(
        "Android SDK 호환성 6년 차 전문가다. "
        "Android 8(API 26)부터 14(API 34)까지의 호환성 패턴을 숙지하고 있으며, "
        "deprecated API와 동작 변경 사항을 모듈 단위로 추적한다. "
        "특히 manifest 변경과 권한 모델 차이를 우선 검토한다."
    ),
    allow_delegation=False,
    tools=[diff_reader, module_lookup, severity_estimator],
    verbose=True,
    max_iter=4,
)

compat_task = Task(
    description=(
        "Manager가 분배한 Compat 도메인 영향 모듈에 대해 호환성 회귀 위험을 평가한다.\n"
        "\n"
        "평가 절차:\n"
        "1) module_lookup 으로 영향 모듈의 실제 존재를 확인한다.\n"
        "2) AndroidManifest·gradle 설정·SDK 버전 의존성 변화를 분석한다.\n"
        "3) deprecated API 사용·하위 호환성 깨짐 패턴을 식별한다.\n"
        "4) rationale 에 영향받는 Android 버전 범위를 명시한다.\n"
        "\n"
        "결과는 WorkerVerdict(domain='Compat') 형식으로 산출한다."
    ),
    expected_output="WorkerVerdict 객체 (domain='Compat')",
    output_pydantic=WorkerVerdict,
    agent=compat_worker,
    context=[analyze_diff_task],
)
