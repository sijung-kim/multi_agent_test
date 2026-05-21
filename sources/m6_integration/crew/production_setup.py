"""Production 통합본 — M5의 Crew + M6의 모든 도구를 결합한 운영 진입점.

본 모듈은 M5 코드(m5_build_triage_crew/crew/)를 그대로 import 한 후
M6에서 추가된 표준 도구와 MCP 도구를 일괄 등록한다.
"""

import os
import sys
from pathlib import Path

# M5 crew 모듈을 import 가능하게 sys.path에 추가
M5_PATH = Path(__file__).resolve().parents[2] / "m5_build_triage_crew"
if M5_PATH.exists() and str(M5_PATH) not in sys.path:
    sys.path.insert(0, str(M5_PATH))

# M5 Crew 컴포넌트 import (M5와 동일 인터페이스 유지)
from crew.manager import (
    build_coordinator,
    build_scope_analyzer,
    build_integrator,
    analyze_diff_task,
    integrate_triage_task,
)
from crew.workers import (
    ui_worker, ui_task,
    perf_worker, perf_task,
    compat_worker, compat_task,
    l10n_worker, l10n_task,
    knox_worker, knox_task,
)
from crew.hooks import CALLBACKS
from crew.schemas import BuildTriageReport

# M6 추가 도구
from .tools.standard_tools import (
    diff_reader,
    area_classifier,
    slack_notifier,
    build_report_writer,
    json_dump,
)
from .tools.mcp_tools import MCP_TOOLS_FILESYSTEM

from crewai import Crew, Process, LLM

# M5 에이전트에 Claude LLM 일괄 주입 (M5는 LLM 미지정 → OpenAI 기본값 방지)
CLAUDE = LLM(model="anthropic/claude-sonnet-4-5-20250929")
for _agent in [
    build_coordinator, build_scope_analyzer, build_integrator,
    ui_worker, perf_worker, compat_worker, l10n_worker, knox_worker,
]:
    _agent.llm = CLAUDE


# === 모든 Worker에 표준 도구 일괄 등록 ===
STANDARD_TOOLSET = [
    diff_reader,
    area_classifier,
    *MCP_TOOLS_FILESYSTEM,
]

MANAGER_TOOLSET = STANDARD_TOOLSET + [
    slack_notifier,
    build_report_writer,
    json_dump,
]

# Worker는 검색·읽기 권한만, Integrator는 알림·저장 권한까지 갖는다.
# Coordinator는 hierarchical 위임만 담당하므로 도구와 Task를 갖지 않는다.
for worker in [ui_worker, perf_worker, compat_worker, l10n_worker, knox_worker]:
    # CrewAI 버전에 따라 tools 인터페이스가 다르므로 안전한 갱신
    existing = list(getattr(worker, "tools", []) or [])
    worker.tools = existing + STANDARD_TOOLSET

existing_scope = list(getattr(build_scope_analyzer, "tools", []) or [])
build_scope_analyzer.tools = existing_scope + STANDARD_TOOLSET

existing_integrator = list(getattr(build_integrator, "tools", []) or [])
build_integrator.tools = existing_integrator + MANAGER_TOOLSET


# === LangSmith 추적 환경 ===
def enable_langsmith_tracing(project: str = "build-triage-prod") -> None:
    """LangSmith 추적을 활성화한다 (LANGCHAIN_API_KEY 가 설정된 경우)."""
    if not os.getenv("LANGCHAIN_API_KEY"):
        print("[tracing] LANGCHAIN_API_KEY not set — tracing disabled")
        return
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ.setdefault("LANGCHAIN_PROJECT", project)
    print(f"[tracing] enabled · project={os.environ['LANGCHAIN_PROJECT']}")


# === Production Crew ===
integrate_triage_task.context = [
    analyze_diff_task,
    ui_task,
    perf_task,
    compat_task,
    l10n_task,
    knox_task,
]


def _production_crew_kwargs():
    kwargs = {
        "agents": [
            build_scope_analyzer,
            ui_worker, perf_worker, compat_worker,
            l10n_worker, knox_worker,
            build_integrator,
        ],
        "tasks": [
            analyze_diff_task,
            ui_task, perf_task, compat_task,
            l10n_task, knox_task,
            integrate_triage_task,
        ],
        "process": Process.hierarchical,
        "verbose": True,
    }

    if "manager_agent" in Crew.model_fields:
        kwargs["manager_agent"] = build_coordinator
    else:
        kwargs["manager_llm"] = "anthropic/claude-sonnet-4-5-20250929"
    return kwargs


production_crew = Crew(**_production_crew_kwargs())


def run_triage(diff_path: str, build_id: str,
               notify_slack: bool = True) -> BuildTriageReport:
    """Build Triage 한 회차 실행.

    Args:
        diff_path: build diff 파일 경로
        build_id: 빌드 식별자
        notify_slack: 결과를 Slack에 자동 전송할지 (SLACK_BOT_TOKEN 필요)
    """
    enable_langsmith_tracing()

    inputs = {"diff_path": diff_path, "build_id": build_id}
    raw = production_crew.kickoff(inputs=inputs)

    # 결과 파싱 (crewAI 1.x: kickoff()는 CrewOutput 래퍼 반환)
    if isinstance(raw, BuildTriageReport):
        report = raw
    elif hasattr(raw, "pydantic") and isinstance(raw.pydantic, BuildTriageReport):
        report = raw.pydantic
    elif hasattr(raw, "json_dict") and raw.json_dict:
        report = BuildTriageReport(**raw.json_dict)
    elif isinstance(raw, dict):
        report = BuildTriageReport(**raw)
    else:
        try:
            report = BuildTriageReport.model_validate_json(
                raw.raw if hasattr(raw, "raw") else str(raw)
            )
        except Exception:
            raise ValueError(f"BuildTriageReport 파싱 실패: {raw}")

    # Slack 알림
    if notify_slack and os.getenv("SLACK_BOT_TOKEN"):
        msg = (
            f"*Build Triage* — `{report.build_id}`\n"
            f"Decision: *{report.decision.value}*  (P{report.priority})\n"
            f"Summary: {report.summary}"
        )
        slack_notifier(
            channel=os.getenv("SLACK_DEFAULT_CHANNEL", "#build-triage"),
            message=msg,
        )

    return report
