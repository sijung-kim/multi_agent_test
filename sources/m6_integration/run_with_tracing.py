"""Production 통합본 실행 스크립트 — LangSmith 추적 + 추적 ID 출력."""

import argparse
import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# sources 패키지 import 경로 설정
HERE = Path(__file__).resolve().parent
SOURCES_ROOT = HERE.parent
if str(SOURCES_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCES_ROOT))

from m6_integration.crew.production_setup import run_triage


def configure_console() -> None:
    """Windows 콘솔에서도 CrewAI의 유니코드 로그가 깨지지 않도록 설정한다."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def load_environment() -> None:
    """실행 위치와 무관하게 M6/sources/.env를 우선 로드한다."""
    load_dotenv(SOURCES_ROOT / ".env")
    load_dotenv(HERE / ".env", override=False)
    load_dotenv(override=False)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="M6 Production 통합본 실행 (LangSmith 추적 포함)"
    )
    p.add_argument(
        "--diff", required=True,
        help="build diff 파일 경로"
    )
    p.add_argument(
        "--build-id", required=True,
        help="빌드 식별자"
    )
    p.add_argument(
        "--no-slack", action="store_true",
        help="Slack 알림을 비활성화"
    )
    return p.parse_args()


def main() -> int:
    configure_console()
    args = parse_args()
    load_environment()

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("[ERROR] ANTHROPIC_API_KEY 환경변수가 필요합니다.")
        print("        .env 파일에 ANTHROPIC_API_KEY 를 입력하세요.")
        return 1

    # 추적 ID 생성
    trace_id = (
        f"build-{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}-"
        f"{uuid.uuid4().hex[:6]}"
    )
    os.environ["LANGCHAIN_TRACE_ID"] = trace_id
    print(f"[trace_id] {trace_id}")
    print(f"[input   ] diff={args.diff}")
    print(f"[input   ] build_id={args.build_id}")
    print()

    try:
        report = run_triage(
            diff_path=args.diff,
            build_id=args.build_id,
            notify_slack=not args.no_slack,
        )
    except Exception as e:
        print(f"[FATAL] {type(e).__name__}: {e}")
        return 2

    # LangSmith 대시보드 URL
    project = os.getenv("LANGCHAIN_PROJECT", "build-triage-prod")
    dashboard_url = (
        f"https://smith.langchain.com/o/_/projects/p/{project}"
        f"?searchModel={{\"filter\":\"trace_id={trace_id}\"}}"
    )
    print()
    print("=" * 60)
    print(f"[decision ] {report.decision.value}  (P{report.priority})")
    print(f"[confidence] {report.confidence}")
    print(f"[fix-hrs  ] {report.estimated_fix_hours}")
    print(f"[summary  ] {report.summary[:120]}")
    print()
    print(f"[dashboard] {dashboard_url}")
    print("=" * 60)

    return 0 if not report.is_blocking() else 1


if __name__ == "__main__":
    sys.exit(main())
