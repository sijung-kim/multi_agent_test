"""Notification Agent — Slack/Jira에 리뷰 결과를 티켓으로 등록한다.

migration_worksheet.md 예시 1 · TO-BE Agent 4.
"""

from crewai import Agent, Task

from .schemas import CodeReviewReport
from .tools import slack_notifier, jira_ticket_creator
from .manager import CLAUDE


# === Notification Agent ===
notification_agent = Agent(
    role="DevOps Notification Specialist",
    goal=(
        "리뷰 결과를 Slack 채널에 요약 메시지로 전송하고, "
        "High/Critical 위험 항목은 Jira 티켓으로 등록한다. "
        "최종 산출물은 CodeReviewReport 객체(티켓 ID 포함)다."
    ),
    backstory=(
        "MX 개발팀 DevOps 엔지니어로서 코드 리뷰 자동화 파이프라인을 구축·운영한다. "
        "Slack 알림 피로도를 최소화하면서도 중요 이슈가 누락되지 않도록 "
        "알림 규칙과 Jira 티켓 구조를 설계해 왔다. "
        "간결하고 행동 가능한 메시지를 우선 가치로 삼는다."
    ),
    allow_delegation=False,
    tools=[slack_notifier, jira_ticket_creator],
    llm=CLAUDE,
    verbose=True,
    max_iter=10,
)


# === 알림 발송 Task ===
notify_task = Task(
    description=(
        "리뷰 결과를 Slack과 Jira에 등록하고 최종 CodeReviewReport를 산출한다.\n"
        "\n"
        "처리 절차:\n"
        "1) 이전 단계의 리뷰 결과(decision, comments, summary, risks)를 확인한다.\n"
        "2) slack_notifier 를 1회 호출한다.\n"
        "   - channel: {slack_channel}\n"
        "   - message: '[PR {pr_id}] 리뷰 결과 요약' 형태로 간단히 작성\n"
        "3) jira_ticket_creator 를 최대 2회만 호출한다 (Critical 이슈 상위 2건만).\n"
        "   - project: {jira_project}\n"
        "   - description: 이슈 설명 (파일 경로 + 위험 내용 포함)\n"
        "   - severity: Critical 또는 High\n"
        "4) 위 결과를 CodeReviewReport 스키마로 산출한다.\n"
        "   jira_ticket_ids 에 생성된 티켓 ID 목록을 넣는다.\n"
    ),
    expected_output=(
        "CodeReviewReport 객체 — pr_id, decision, overall_severity, risk_count, "
        "comment_count, review_summary(30자 이상), slack_message_id, "
        "jira_ticket_ids(목록), channels_notified(목록)."
    ),
    output_pydantic=CodeReviewReport,
    agent=notification_agent,
    # context는 main_crew.py 조립 단계에서 주입된다 (notify_task.context = [...])
)
