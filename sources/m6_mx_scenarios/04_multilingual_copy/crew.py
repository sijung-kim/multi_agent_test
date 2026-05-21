"""Scenario 04 — 다국어 마케팅 카피 생성.

한국어 카피를 입력받아 영어·일본어·중국어로 번역하고, 각 언어 Reviewer가 검수한다.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Literal
from crewai import Agent, Task, Crew, Process


TargetLang = Literal["en", "ja", "zh-CN"]


class CopyVariant(BaseModel):
    lang: TargetLang
    headline: str = Field(max_length=80)
    body: str = Field(max_length=400)
    cta: str = Field(max_length=30)
    cultural_notes: str = Field(default="")


class MultilingualCopyReport(BaseModel):
    campaign_id: str
    source_lang: str = "ko"
    source_copy: str
    variants: List[CopyVariant]
    quality_score: int = Field(ge=1, le=10)


# Manager
copy_manager = Agent(
    role="Multilingual Copy Manager",
    goal="한국어 카피를 3개 언어 Worker에 분배하고 검수된 변종을 통합 산출한다",
    backstory="글로벌 마케팅 카피 6년차. EU·미주·아시아 캠페인 운영 경험.",
    allow_delegation=True,
    verbose=True,
)

# Copywriter Workers (per language)
en_copywriter = Agent(
    role="English Copywriter",
    goal="한국어 카피를 미주 시장에 적합한 영어 카피로 재창작한다",
    backstory="미국 광고 카피 8년차. 직역이 아닌 문화적 재해석에 특화.",
    allow_delegation=False,
)
ja_copywriter = Agent(
    role="Japanese Copywriter",
    goal="한국어 카피를 일본 시장에 적합한 일본어 카피로 재창작한다",
    backstool="일본 광고 7년차. 경어 단계와 문화적 절제미 표현에 특화.",
    allow_delegation=False,
)
zh_copywriter = Agent(
    role="Chinese (Simplified) Copywriter",
    goal="한국어 카피를 중국 시장에 적합한 간체 중국어 카피로 재창작한다",
    backstory="중국 광고 6년차. 검열·정치적 민감어를 우회하는 데 특화.",
    allow_delegation=False,
)


# Tasks
copy_task = Task(
    description=(
        "한국어 원본: {source_copy}\n"
        "campaign_id: {campaign_id}\n"
        "\n"
        "1) 3개 Copywriter Worker에 분배\n"
        "2) 각 Worker가 CopyVariant 산출 (headline·body·cta·cultural_notes)\n"
        "3) 전체를 MultilingualCopyReport 로 통합"
    ),
    expected_output="MultilingualCopyReport 객체",
    output_pydantic=MultilingualCopyReport,
    agent=copy_manager,
)


copy_crew = Crew(
    agents=[copy_manager, en_copywriter, ja_copywriter, zh_copywriter],
    tasks=[copy_task],
    process=Process.hierarchical,
    manager_llm="gpt-4o",
    verbose=True,
)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-copy", required=True, help="한국어 원본 카피")
    parser.add_argument("--campaign-id", required=True)
    args = parser.parse_args()

    result = copy_crew.kickoff(inputs={
        "source_copy": args.source_copy,
        "campaign_id": args.campaign_id,
    })
    print(result)
