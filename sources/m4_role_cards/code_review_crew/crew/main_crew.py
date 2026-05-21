"""Code Review Crew 조립 — Coordinator + 4 Worker Agent + Pydantic 출력.

예시 1 (빌드 리뷰) 파이프라인:
  Coordinator(위임 전용) → Analyzer → Risk → Reviewer → Notifier

위임 전용 coordinator는 manager_agent로만 전달하고, 실행 agent 목록에는 넣지 않는다.
manager_agent를 지원하지 않는 CrewAI 버전에서는 manager_llm 내부 매니저를 사용한다.
"""

from crewai import Crew, Process

from .manager import code_review_coordinator
from .analyzer import analyzer_agent, analyze_task
from .risk_agent import risk_agent, risk_task
from .reviewer import reviewer_agent, review_task
from .notifier import notification_agent, notify_task


# notify_task 의 context를 여기서 명시적으로 설정한다.
# notifier.py 에서 상위 모듈을 직접 import 하는 대신 조립 단계에서 주입하는 방식으로
# 모듈 간 결합도를 낮춘다. (m5 integrate_triage_task 패턴 동일)
notify_task.context = [analyze_task, risk_task, review_task]


def _build_crew_kwargs() -> dict:
    kwargs = {
        "agents": [
            analyzer_agent,
            risk_agent,
            reviewer_agent,
            notification_agent,
        ],
        "tasks": [
            analyze_task,
            risk_task,
            review_task,
            notify_task,
        ],
        "process": Process.hierarchical,
        "verbose": True,
    }

    # CrewAI 버전 호환: Pydantic V2 모델이므로 model_fields로 파라미터 존재 확인
    if "manager_agent" in Crew.model_fields:
        kwargs["manager_agent"] = code_review_coordinator
    else:
        kwargs["manager_llm"] = "claude-sonnet-4-5-20251001"   # 구버전 폴백

    return kwargs


# === Code Review Crew ===
code_review_crew = Crew(**_build_crew_kwargs())
