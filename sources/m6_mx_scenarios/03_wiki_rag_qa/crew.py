"""Scenario 03 — 내부 위키 RAG QA.

사용자 질문을 받아 3개 Worker(Retrieval·Synthesis·Citation)가 협업하여
출처 인용이 명시된 답변을 산출한다.
"""

from pydantic import BaseModel, Field
from typing import List, Literal
from crewai import Agent, Task
import sys
from pathlib import Path

SCENARIOS_ROOT = Path(__file__).resolve().parent.parent
if str(SCENARIOS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCENARIOS_ROOT))

from scenario_common import configure_runtime, create_hierarchical_crew, require_openai_key, tool


# === @tool ===
@tool("Wiki Search")
def wiki_search(query: str, top_k: int = 5) -> str:
    """사내 위키 인덱스에서 query 와 가장 관련 있는 문서 top_k 개를 반환한다."""
    # 실제 운영에서는 벡터 DB (Pinecone·Weaviate·Qdrant 등) 호출로 교체
    return f"[stub] {top_k} docs matching '{query[:40]}'"


@tool("Doc Fetch")
def doc_fetch(doc_id: str) -> str:
    """위키 문서 ID로 전체 본문을 반환한다."""
    return f"[stub] full text of doc {doc_id}"


# === 출력 스키마 ===
class Citation(BaseModel):
    doc_id: str
    title: str
    excerpt: str = Field(max_length=200)


class WikiQAAnswer(BaseModel):
    question: str
    answer: str = Field(min_length=50)
    citations: List[Citation]
    confidence: Literal["high", "medium", "low"] = Field(default="medium")


# === Manager ===
qa_manager = Agent(
    role="Wiki QA Manager",
    goal="사용자 질문을 3개 Worker에 분배하여 출처 인용이 포함된 답변을 산출한다",
    backstory="사내 지식관리 시스템 운영 6년차. RAG 파이프라인의 환각 방지 패턴을 숙지.",
    allow_delegation=True,
    verbose=True,
)


# === Workers ===
retrieval_worker = Agent(
    role="Retrieval Specialist",
    goal="질문에 가장 관련 있는 위키 문서 top 5 를 추출한다",
    backstory="정보 검색 7년차. 의미적 검색과 키워드 검색의 하이브리드 전략을 운영.",
    allow_delegation=False,
    tools=[wiki_search, doc_fetch],
)

synthesis_worker = Agent(
    role="Synthesis Specialist",
    goal="검색된 문서들을 종합하여 질문에 대한 일관된 답변을 작성한다",
    backstory="기술 문서 작성 8년차. 다수 출처를 통합하면서 모순을 명시하는 데 특화.",
    allow_delegation=False,
)

citation_worker = Agent(
    role="Citation Verifier",
    goal="답변의 각 주장에 출처 인용이 명시되어 있는지 검증하고 누락 시 보강한다",
    backstory="학술 인용 검증 4년차. 환각 패턴(없는 인용)을 즉시 식별.",
    allow_delegation=False,
    tools=[doc_fetch],
)


# === Task ===
qa_task = Task(
    description=(
        "사용자 질문: {question}\n"
        "1) Retrieval Worker로 top 5 문서를 가져온다.\n"
        "2) Synthesis Worker로 통합 답변을 작성한다.\n"
        "3) Citation Worker로 인용 누락을 검증·보강한다.\n"
        "4) WikiQAAnswer 객체로 산출한다."
    ),
    expected_output="WikiQAAnswer 객체 (citations 1개 이상 필수)",
    output_pydantic=WikiQAAnswer,
    agent=qa_manager,
)


wiki_qa_crew = create_hierarchical_crew(
    manager=qa_manager,
    workers=[retrieval_worker, synthesis_worker, citation_worker],
    tasks=[qa_task],
    manager_llm="gpt-4o",
)


if __name__ == "__main__":
    configure_runtime()
    if not require_openai_key():
        sys.exit(1)
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--question", required=True)
    args = parser.parse_args()
    result = wiki_qa_crew.kickoff(inputs={"question": args.question})
    print(result)
