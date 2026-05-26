---
name: code_review
description: PR diff 또는 단일 소스 파일을 받아 코드 리뷰를 수행하는 표준 절차
version: 1.0
inputs:
  - target_path: 검토 대상 파일 또는 diff 경로 (필수)
  - language: 소스 언어 — auto / python / java / kotlin / typescript (기본 auto)
  - context_path: 참조 컨텍스트 폴더 (선택)
outputs:
  - review_report.md: 마크다운 형식 리뷰 리포트
---

# 코드 리뷰 절차

## 1. 변경 범위 식별

- `target_path` 가 diff 파일인 경우 `diff --git` 블록 단위로 분리한다.
- `target_path` 가 단일 소스 파일인 경우 함수·클래스 단위로 분리한다.
- 각 변경 블록의 메타데이터(파일·라인·언어)를 기록한다.

## 2. 결함 가능성 점검 (5차원)

각 변경 블록을 다음 5개 차원에서 평가하고 1~5 severity 를 산정한다.

| # | 차원 | 점검 사항 |
|---|---|---|
| 1 | **로직 정합성** | 조건문 분기·반환 값·예외 흐름이 의도대로 동작하는가 |
| 2 | **예외 처리** | None·빈 입력·잘못된 타입·외부 IO 실패에 대한 방어가 있는가 |
| 3 | **보안** | 사용자 입력 검증·SQL 인젝션·평문 비밀번호·LDAP 인젝션이 없는가 |
| 4 | **성능** | O(n²) 이상의 비효율 패턴·불필요한 IO·메모리 누수가 없는가 |
| 5 | **가독성** | 함수 분할·명명·docstring·타입 힌트·주석이 적절한가 |

## 3. severity 산정 기준

| Severity | 기준 | 권장 액션 |
|---|---|---|
| **5 (Critical)** | 보안 취약점 · 데이터 손실 · 런타임 충돌 | 즉시 수정 후 머지 |
| **4 (High)** | 명확한 결함 · 회귀 가능성 | 단기 내 수정 |
| **3 (Medium)** | 잠재적 위험 · 코딩 표준 위반 | PR 내 수정 권고 |
| **2 (Low)** | 가독성 · 사소한 개선 | 선택적 수정 |
| **1 (Info)** | 정보성 의견 · 향후 개선 아이디어 | 기록만 |

## 4. 리포트 작성

`review_report.md` 에 다음 양식으로 출력한다:

```markdown
# Code Review Report

**Reviewer**: {도구명} {version}
**Target**: {target_path}
**Generated**: {ISO timestamp}

## 1. Summary
- Files changed: {n}
- Lines added: +{m}
- Lines removed: -{k}
- Risk level: Low | Medium | High

## 2. Findings
| # | File | Line | Severity | Issue |
|---|------|------|----------|-------|

## 3. Detailed Recommendations
### Finding 1 — {short title} (line {n})
{원본 코드 블록}

**Suggested fix**:
{수정안 코드 블록}
```

## 5. 검증 체크리스트

산출 후 다음을 확인한다:

- [ ] Severity 5 항목이 가장 위에 정렬되었는가
- [ ] 각 Finding 에 구체적 수정안이 동봉되었는가
- [ ] False positive 가 의심되는 항목에 confidence 가 명시되었는가
- [ ] 검토 대상 외 파일은 언급되지 않았는가
