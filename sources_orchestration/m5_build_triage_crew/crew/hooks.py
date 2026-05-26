"""Hook 모듈 — Task 실행 전/후의 자동 콜백.

Crew에 등록되면 모든 Task의 execute() 진입·종료 시점에 자동 호출된다.
운영 환경에서는 로깅·메트릭 수집·외부 모니터링 시스템 연동의 진입점이 된다.
"""

import json
import logging
from datetime import datetime
from typing import Any

from crewai import Task


# 로거 설정 — JSON 라인 출력으로 통일해 파싱 가능하게
logger = logging.getLogger("build_triage")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)


def _ts() -> str:
    """현재 UTC 시각의 ISO 8601 문자열."""
    return datetime.utcnow().isoformat() + "Z"


def on_task_start(task: Task) -> None:
    """Task.execute() 진입 직전 자동 호출.

    실행 시작 시점·에이전트·작업 설명을 구조화된 JSON으로 로깅한다.
    """
    payload = {
        "event": "task_start",
        "ts": _ts(),
        "agent": getattr(task.agent, "role", "unknown"),
        "task_id": id(task),
        "description": (task.description or "")[:80],
    }
    logger.info(json.dumps(payload, ensure_ascii=False))


def on_task_end(task: Task, output: Any) -> None:
    """Task.execute() 종료 직후 자동 호출.

    소요 시간·토큰 사용량·산출 상태를 로깅한다.
    """
    tokens = getattr(output, "tokens_used", None)
    duration = getattr(output, "duration_seconds", None)
    payload = {
        "event": "task_end",
        "ts": _ts(),
        "agent": getattr(task.agent, "role", "unknown"),
        "task_id": id(task),
        "tokens": tokens,
        "duration_s": duration,
        "status": "ok" if output else "failed",
    }
    logger.info(json.dumps(payload, ensure_ascii=False))


def on_agent_finish(agent_role: str, output: Any) -> None:
    """Agent 전체 작업 종료 시 호출 (선택적).

    Manager의 통합 단계가 끝난 후 호출되며, 운영에서는 Slack 알림 등에 연결한다.
    """
    payload = {
        "event": "agent_finish",
        "ts": _ts(),
        "agent": agent_role,
        "output_summary": str(output)[:200] if output else None,
    }
    logger.info(json.dumps(payload, ensure_ascii=False))


# Crew 등록용 dict — main_crew.py 에서 import 후 callbacks 인자에 전달
CALLBACKS = {
    "on_task_start": on_task_start,
    "on_task_end": on_task_end,
}
