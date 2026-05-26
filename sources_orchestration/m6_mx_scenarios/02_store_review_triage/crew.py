"""Scenario 02 — 갤럭시 스토어 리뷰 트리아지.

사용자 리뷰 텍스트 묶음을 받아 3개 Worker가 평가하고 Manager가 CS 처리 우선순위를 산출한다.
"""

from pydantic import BaseModel, Field
from typing import List, Literal
from crewai import Agent, Task
import sys
from pathlib import Path

SCENARIOS_ROOT = Path(__file__).resolve().parent.parent
if str(SCENARIOS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCENARIOS_ROOT))

from scenario_common import (
    configure_runtime,
    create_hierarchical_crew,
    require_openai_key,
    text_file_reader,
)


# === 출력 스키마 ===
class ReviewItem(BaseModel):
    review_id: str
    severity: Literal["P1", "P2", "P3"]
    category: Literal["Bug", "Feature Request", "UX Complaint", "Performance", "Other"]
    sentiment: Literal["positive", "neutral", "negative", "very_negative"]
    suggested_response: str


class StoreReviewTriageReport(BaseModel):
    batch_id: str
    total_reviews: int
    p1_count: int
    p2_count: int
    p3_count: int
    items: List[ReviewItem]
    summary: str


# === Manager ===
triage_manager = Agent(
    role="Store Review Triage Manager",
    goal="갤럭시 스토어 리뷰 묶음을 3개 Worker로 분배하고 CS 처리 우선순위 리포트를 산출한다",
    backstory="갤럭시 스토어 CS 매니저 5년차. 일 평균 1만 건의 리뷰를 P1~P3로 분류해 온 경험.",
    allow_delegation=True,
    verbose=True,
)


# === Workers ===
severity_worker = Agent(
    role="Severity Classifier",
    goal="리뷰의 심각도를 P1(긴급)~P3(낮음)으로 분류한다",
    backstory="CS 운영 6년차. 데이터 손실·결제 실패 등 P1 패턴을 즉시 식별.",
    allow_delegation=False,
    tools=[text_file_reader],
)

category_worker = Agent(
    role="Category Classifier",
    goal="리뷰를 Bug·Feature Request·UX·Performance·Other 5종으로 분류한다",
    backstory="VOC 분석 5년차. 자유 텍스트를 표준 카테고리로 정규화하는 데 특화.",
    allow_delegation=False,
    tools=[text_file_reader],
)

sentiment_worker = Agent(
    role="Sentiment Analyzer",
    goal="리뷰의 감성을 positive·neutral·negative·very_negative 4단계로 분류한다",
    backstory="NLP 분석 4년차. 한국어 비꼼·반어법까지 감지하는 모델 운영 경험.",
    allow_delegation=False,
    tools=[text_file_reader],
)


# === Task ===
triage_task = Task(
    description=(
        "text_file_reader 로 {reviews_path} 의 리뷰 묶음을 읽고 3개 Worker에 분배한다. "
        "각 리뷰별로 severity·category·sentiment를 결합하여 ReviewItem 을 산출하고, "
        "전체를 StoreReviewTriageReport 로 통합한다."
    ),
    expected_output="StoreReviewTriageReport 객체",
    output_pydantic=StoreReviewTriageReport,
    agent=triage_manager,
)


store_triage_crew = create_hierarchical_crew(
    manager=triage_manager,
    workers=[severity_worker, category_worker, sentiment_worker],
    tasks=[triage_task],
    manager_llm="gpt-4o",
)


if __name__ == "__main__":
    configure_runtime()
    if not require_openai_key():
        sys.exit(1)
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--reviews", required=True)
    parser.add_argument("--batch-id", required=True)
    args = parser.parse_args()
    result = store_triage_crew.kickoff(
        inputs={"reviews_path": args.reviews, "batch_id": args.batch_id}
    )
    print(result)
