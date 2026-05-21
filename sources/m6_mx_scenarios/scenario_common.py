"""Shared helpers for the M6 MX scenario examples."""

import os
import sys
from pathlib import Path
from typing import Iterable, List, Optional

from crewai import Agent, Crew, Process, Task

try:
    from crewai_tools import tool
except ImportError:  # CrewAI/CrewAI Tools version compatibility
    from crewai.tools import tool


SCENARIOS_ROOT = Path(__file__).resolve().parent
SOURCES_ROOT = SCENARIOS_ROOT.parent


def configure_runtime() -> None:
    """Make examples runnable from any scenario folder on Windows or Unix."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    for path in (SOURCES_ROOT / ".env", SCENARIOS_ROOT / ".env", Path.cwd() / ".env"):
        if path.exists():
            try:
                from dotenv import load_dotenv

                load_dotenv(path, override=False)
            except Exception:
                pass

    os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")


def require_openai_key() -> bool:
    """Return False with a clear message when the examples cannot call the LLM."""
    if os.getenv("OPENAI_API_KEY"):
        return True
    print("[ERROR] OPENAI_API_KEY 환경변수가 필요합니다.")
    print("        sources/.env 또는 현재 셸 환경변수에 OPENAI_API_KEY를 설정하세요.")
    return False


@tool("Text File Reader")
def text_file_reader(path: str, max_chars: int = 20000) -> str:
    """Read a UTF-8 text file for scenario inputs such as PRDs or review batches."""
    p = Path(path).expanduser()
    if not p.is_absolute():
        p = Path.cwd() / p
    if not p.exists():
        return f"[ERROR] file not found: {p}"
    if not p.is_file():
        return f"[ERROR] path is not a file: {p}"
    return p.read_text(encoding="utf-8", errors="replace")[:max_chars]


def create_hierarchical_crew(
    *,
    manager: Agent,
    workers: Iterable[Agent],
    tasks: List[Task],
    manager_llm: Optional[str] = None,
) -> Crew:
    """Create a hierarchical Crew while avoiding manager/executor conflicts.

    Newer CrewAI versions support ``manager_agent``. In that mode the manager is
    passed only as the delegation coordinator, and is not duplicated in agents.
    Older versions fall back to ``manager_llm`` and CrewAI's internal manager.
    """
    kwargs = {
        "agents": list(workers),
        "tasks": tasks,
        "process": Process.hierarchical,
        "verbose": True,
    }

    fields = getattr(Crew, "model_fields", {})
    if "manager_agent" in fields:
        kwargs["manager_agent"] = manager
    else:
        kwargs["manager_llm"] = manager_llm or os.getenv("OPENAI_MODEL", "gpt-4o")

    return Crew(**kwargs)
