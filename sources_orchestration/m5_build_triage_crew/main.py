"""Build Triage Crew 실행 엔트리.

사용법:
    python main.py --diff ./sample_diff.txt --build-id GA-2026-05-20
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from crew.main_crew import build_triage_crew, attach_callbacks_if_supported
from crew.schemas import BuildTriageReport


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Build Triage Crew — Galaxy nightly build diff 분석"
    )
    p.add_argument(
        "--diff", required=True,
        help="nightly build diff 파일 경로"
    )
    p.add_argument(
        "--build-id", required=True,
        help="빌드 식별자 (예: GA-2026-05-20-001)"
    )
    p.add_argument(
        "--no-tracing", action="store_true",
        help="LangSmith 추적을 비활성화한다"
    )
    return p.parse_args()


def setup_environment(no_tracing: bool = False) -> None:
    """환경변수 로드 및 LangSmith 추적 활성화."""
    load_dotenv()

    if not os.getenv("OPENAI_API_KEY"):
        print("[ERROR] OPENAI_API_KEY 환경변수가 설정되어 있지 않습니다.")
        print("        sources/.env.example 을 참고해 .env 파일을 작성하세요.")
        sys.exit(1)

    if not no_tracing and os.getenv("LANGCHAIN_API_KEY"):
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
        os.environ.setdefault(
            "LANGCHAIN_PROJECT", "build-triage-curriculum"
        )
        print(
            f"[tracing] LangSmith enabled · "
            f"project={os.environ['LANGCHAIN_PROJECT']}"
        )
    else:
        print("[tracing] disabled")


def validate_diff_path(path: str) -> Path:
    p = Path(path).resolve()
    if not p.exists():
        print(f"[ERROR] diff 파일을 찾을 수 없습니다: {p}")
        sys.exit(1)
    if not p.is_file():
        print(f"[ERROR] 디렉터리가 아닌 파일을 지정해야 합니다: {p}")
        sys.exit(1)
    return p


def main() -> int:
    args = parse_args()
    setup_environment(no_tracing=args.no_tracing)
    diff_path = validate_diff_path(args.diff)
    attach_callbacks_if_supported()

    print(f"[input ] diff={diff_path}")
    print(f"[input ] build_id={args.build_id}")
    print("[run   ] Build Triage Crew 시작 ...")

    inputs = {
        "diff_path": str(diff_path),
        "build_id": args.build_id,
    }

    try:
        result = build_triage_crew.kickoff(inputs=inputs)
    except Exception as e:
        print(f"[FATAL ] kickoff 중 예외: {type(e).__name__}: {e}")
        return 2

    # CrewAI 버전에 따라 result가 dict / str / Pydantic 객체일 수 있다.
    if isinstance(result, BuildTriageReport):
        report = result
    elif isinstance(result, dict):
        report = BuildTriageReport(**result)
    else:
        # JSON 파싱 시도
        import json
        try:
            report = BuildTriageReport.model_validate_json(str(result))
        except Exception:
            print(f"[WARN ] 결과를 BuildTriageReport 로 파싱하지 못함")
            print(f"[raw  ] {result}")
            return 3

    print()
    print("=" * 60)
    print(f"[decision] {report.decision.value}  (P{report.priority})")
    print(f"[summary ] {report.summary}")
    print(f"[fix-hrs ] {report.estimated_fix_hours}")
    print(f"[confidence] {report.confidence}")
    print()
    print("[verdicts]")
    for v in report.worker_verdicts:
        print(
            f"  · {v.domain.value:<6} sev={v.severity}  "
            f"modules={len(v.affected_modules)}"
        )
    print("=" * 60)

    return 0 if not report.is_blocking() else 1


if __name__ == "__main__":
    sys.exit(main())
