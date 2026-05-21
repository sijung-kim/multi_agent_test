"""Code Review Crew 실행 엔트리 — 예시 1 빌드 리뷰 (Galaxy 앱 개발팀).

사용법:
    python main.py --diff ./sample_diff.txt --pr-id PR-2026-001
    python main.py --diff ./sample_diff.txt --pr-id PR-2026-001 \\
                   --guideline ./guidelines.md \\
                   --slack-channel code-review-alerts \\
                   --jira-project GALAXYAPP
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from crew.main_crew import code_review_crew
from crew.schemas import CodeReviewReport


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Code Review Crew — Galaxy 앱 소스코드 diff 리뷰 자동화"
    )
    p.add_argument(
        "--diff", required=True,
        help="소스코드 diff 파일 경로 (예: ./sample_diff.txt)"
    )
    p.add_argument(
        "--pr-id", required=True,
        help="PR 또는 빌드 식별자 (예: PR-2026-001)"
    )
    p.add_argument(
        "--guideline", default="",
        help="개발 가이드라인 파일 경로 (없으면 기본 Galaxy 가이드라인 사용)"
    )
    p.add_argument(
        "--slack-channel", default="code-review-alerts",
        help="Slack 알림 채널 (기본: code-review-alerts)"
    )
    p.add_argument(
        "--jira-project", default="GALAXYAPP",
        help="Jira 프로젝트 키 (기본: GALAXYAPP)"
    )
    p.add_argument(
        "--no-tracing", action="store_true",
        help="LangSmith 추적 비활성화"
    )
    return p.parse_args()


def setup_environment(no_tracing: bool = False) -> None:
    load_dotenv()

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("[ERROR] ANTHROPIC_API_KEY 환경변수가 설정되어 있지 않습니다.")
        print("        .env 파일에 ANTHROPIC_API_KEY 를 입력하세요.")
        sys.exit(1)

    if not no_tracing and os.getenv("LANGCHAIN_API_KEY"):
        os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
        os.environ.setdefault("LANGCHAIN_PROJECT", "code-review-curriculum")
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

    print(f"[input ] diff={diff_path}")
    print(f"[input ] pr_id={args.pr_id}")
    print(f"[input ] guideline={args.guideline or '(기본 가이드라인 사용)'}")
    print(f"[input ] slack_channel=#{args.slack_channel}")
    print(f"[input ] jira_project={args.jira_project}")
    print("[run   ] Code Review Crew 시작 ...")
    print()

    inputs = {
        "diff_path": str(diff_path),
        "pr_id": args.pr_id,
        "guideline_path": args.guideline or "__default__",
        "slack_channel": args.slack_channel,
        "jira_project": args.jira_project,
    }

    try:
        result = code_review_crew.kickoff(inputs=inputs)
    except Exception as e:
        print(f"[FATAL ] kickoff 중 예외: {type(e).__name__}: {e}")
        return 2

    # crewAI 1.x: kickoff() 는 CrewOutput 래퍼를 반환한다.
    # .pydantic → output_pydantic 으로 지정된 모델 인스턴스
    # .json_dict → dict 형태
    # .raw       → 문자열
    if isinstance(result, CodeReviewReport):
        report = result
    elif hasattr(result, "pydantic") and isinstance(result.pydantic, CodeReviewReport):
        report = result.pydantic
    elif hasattr(result, "json_dict") and result.json_dict:
        report = CodeReviewReport(**result.json_dict)
    elif isinstance(result, dict):
        report = CodeReviewReport(**result)
    else:
        try:
            report = CodeReviewReport.model_validate_json(
                result.raw if hasattr(result, "raw") else str(result)
            )
        except Exception:
            print("[WARN ] 결과를 CodeReviewReport 로 파싱하지 못함")
            print(f"[raw  ] {result}")
            return 3

    print()
    print("=" * 60)
    print(f"[PR          ] {report.pr_id}")
    print(f"[decision    ] {report.decision}")
    print(f"[severity    ] {report.overall_severity.value}")
    print(f"[risks       ] {report.risk_count}건")
    print(f"[comments    ] {report.comment_count}건")
    print(f"[summary     ] {report.review_summary}")
    print()
    print(f"[slack       ] {report.slack_message_id or '(없음)'}")
    if report.jira_ticket_ids:
        print(f"[jira tickets] {', '.join(report.jira_ticket_ids)}")
    else:
        print("[jira tickets] (생성 없음 — High/Critical 이슈 없음)")
    print("=" * 60)

    return 1 if report.is_blocking() else 0


if __name__ == "__main__":
    sys.exit(main())
