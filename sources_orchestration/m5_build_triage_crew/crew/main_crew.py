"""Build Triage Crew 조립 — Coordinator + 실행 Agent + Hook + Pydantic 출력."""

import inspect

from crewai import Crew, Process

from .manager import (
    build_coordinator,
    build_scope_analyzer,
    build_integrator,
    analyze_diff_task,
    integrate_triage_task,
)
from .workers import (
    ui_worker, ui_task,
    perf_worker, perf_task,
    compat_worker, compat_task,
    l10n_worker, l10n_task,
    knox_worker, knox_task,
)
from .hooks import CALLBACKS
from .schemas import BuildTriageReport


# === Build Triage Crew ===
#
# Process.hierarchical 로 Manager 주도 위임 패턴을 활성화한다.
# 위임 전용 coordinator는 manager_agent로만 전달하고, 실행 agent 목록에는 넣지 않는다.
# manager_agent를 지원하지 않는 CrewAI 버전에서는 manager_llm 내부 매니저를 사용한다.
integrate_triage_task.context = [
    analyze_diff_task,
    ui_task,
    perf_task,
    compat_task,
    l10n_task,
    knox_task,
]


def _build_crew_kwargs():
    kwargs = {
        "agents": [
            build_scope_analyzer,
            ui_worker,
            perf_worker,
            compat_worker,
            l10n_worker,
            knox_worker,
            build_integrator,
        ],
        "tasks": [
            analyze_diff_task,
            ui_task,
            perf_task,
            compat_task,
            l10n_task,
            knox_task,
            integrate_triage_task,
        ],
        "process": Process.hierarchical,
        "verbose": True,
    }

    crew_params = inspect.signature(Crew.__init__).parameters
    if "manager_agent" in crew_params:
        kwargs["manager_agent"] = build_coordinator
    else:
        kwargs["manager_llm"] = "gpt-4o"
    return kwargs


build_triage_crew = Crew(**_build_crew_kwargs())


def attach_callbacks_if_supported():
    """CrewAI 버전에 따라 콜백 등록 인터페이스가 다르므로 호환 처리.

    최신 버전에서는 Crew(callbacks=...) 또는 step_callback 으로 등록되며,
    구버전에서는 별도 attach 방식이 필요할 수 있다.
    """
    if hasattr(build_triage_crew, "callbacks"):
        try:
            build_triage_crew.callbacks = CALLBACKS
        except Exception:
            pass
