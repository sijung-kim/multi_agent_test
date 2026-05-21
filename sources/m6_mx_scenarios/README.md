# M6 미니 핸즈온 — MX 5종 시나리오 예시 답안

본 폴더는 M6 슬라이드 11에서 학생이 선택하는 5종 시나리오의 예시 답안이다.

각 시나리오는 M5의 Build Triage Crew 구조를 그대로 차용하되 도메인만 변경한다.

## 5종 시나리오 개요

| # | 시나리오 | 대상 | 핵심 Worker |
|---|---|---|---|
| 01 | **PRD 리뷰** | PM·기획 | Spec·Feasibility·UX·Risk |
| 02 | **스토어 리뷰 트리아지** | CS·QA | Severity·Category·Sentiment |
| 03 | **위키 RAG QA** | 전 직원 | Retrieval·Synthesis·Citation |
| 04 | **다국어 마케팅 카피** | 마케팅 | Copywriter·Localizer·Reviewer |
| 05 | **Customer Care 자동화** | CS 운영 | Intent·Resolver·Escalation |

## 적용 패턴

모든 시나리오는 `Process.hierarchical` Manager-Worker 패턴을 사용한다. 본인 도메인 적용 시:

1. M5의 `crew/manager.py` 와 `crew/workers/*.py` 를 본 시나리오 폴더로 복사
2. role·goal·backstory 를 도메인에 맞게 수정
3. Pydantic 스키마 (`schemas.py`) 의 필드를 산출물 형식에 맞게 조정
4. `sample_input.txt` 를 본인 데이터로 교체

## 시나리오별 폴더

각 폴더의 `README.md` 에 본인 적용 가이드가 있다.

```
m6_mx_scenarios/
├── 01_prd_review/
├── 02_store_review_triage/
├── 03_wiki_rag_qa/
├── 04_multilingual_copy/
└── 05_customer_care/
```
