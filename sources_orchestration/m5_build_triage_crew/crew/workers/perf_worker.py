"""Perf Worker — Codex 가속 생성 산출물 (UI Worker 패턴 참조).

M5 슬라이드 12에서 Codex CLI에 "UI Worker처럼 만들어줘"로 가속 생성된 결과의 정답 형태.
"""

from crewai import Agent, Task

from ..schemas import WorkerVerdict
from ..tools import diff_reader, module_lookup, severity_estimator
from ..manager import analyze_diff_task


perf_worker = Agent(
    role="Performance Specialist",
    goal=(
        "build diff에서 성능 회귀 영향을 측정하고, 병목 지점·메모리 누수·런타임 지연을 식별한다. "
        "특히 콜드 부팅 시간·앱 응답성·배터리 소모·메모리 풋프린트를 우선 확인한다. "
        "최종 산출물은 WorkerVerdict(domain='Perf') 객체다."
    ),
    backstory=(
        "Galaxy 성능 최적화 7년 차 시니어 엔지니어다. "
        "GPU·메모리·런타임 프로파일링에 특화되어 있으며, "
        "벤치마크 회귀 패턴과 미세 성능 누락을 데이터 기반으로 분석한다. "
        "기능 정확성보다 사용자 체감 응답성을 우선 가치로 둔다."
    ),
    allow_delegation=False,
    tools=[diff_reader, module_lookup, severity_estimator],
    verbose=True,
    max_iter=4,
)

perf_task = Task(
    description=(
        "Manager가 분배한 Perf 도메인 영향 모듈 목록을 기반으로 성능 회귀 위험을 평가한다.\n"
        "\n"
        "평가 절차:\n"
        "1) module_lookup 으로 영향 모듈의 규모를 확인한다.\n"
        "2) 콜드 부팅·앱 응답성·배터리·메모리 4대 차원에서 회귀 위험을 분석한다.\n"
        "3) severity_estimator + 도메인 컨텍스트로 최종 severity 를 결정한다.\n"
        "4) rationale 에 측정 가능한 위험 가설을 명시한다 (예: '렌더링 5ms 추가 가능').\n"
        "\n"
        "결과는 WorkerVerdict(domain='Perf') 형식으로 산출한다."
    ),
    expected_output="WorkerVerdict 객체 (domain='Perf')",
    output_pydantic=WorkerVerdict,
    agent=perf_worker,
    context=[analyze_diff_task],
)
