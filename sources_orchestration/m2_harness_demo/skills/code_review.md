---
name: code_review
description: PR diff 또는 단일 Python 파일을 받아 코드 리뷰를 수행하는 표준 절차
version: 1.0
inputs:
  - target_path: 검토 대상 파일 경로 (.py 또는 diff)
  - context_path: (선택) 참조 컨텍스트 폴더 경로
outputs:
  - review_report.md: 마크다운 형식 리뷰 리포트
---

# 검토 절차

## 1. 변경 범위 식별

- `target_path` 파일을 읽고 변경 블록을 추출한다.
- 각 블록의 파일·라인·언어를 메타데이터로 기록한다.

## 2. 결함 가능성 점검 (5차원)

각 변경 블록을 다음 5개 차원에서 평가한다:

| # | 차원 | 점검 사항 |
|---|---|---|
| 1 | **로직 정합성** | 조건문 분기·반환 값·예외 흐름이 의도대로 동작하는가 |
| 2 | **예외 처리** | None·빈 입력·잘못된 타입에 대한 방어가 있는가 |
| 3 | **보안** | 사용자 입력 검증·SQL 인젝션·평문 비밀번호 등이 없는가 |
| 4 | **성능** | O(n²) 이상의 비효율적 패턴·불필요한 IO·메모리 누수가 없는가 |
| 5 | **가독성** | 함수 분할·명명·docstring·타입 힌트가 적절한가 |

## 3. 리포트 작성

`review_report.md` 에 다음 양식으로 출력한다:

```markdown
# Code Review Report

**Reviewer**: Codex CLI v0.x
**Target**:  {target_path}
**Generated**: {ISO timestamp}

## 1. Summary
- Files changed: {n}
- Lines added: +{m}
- Lines removed: -{k}
- Risk level: Low | Medium | High

## 2. Findings
| # | File | Line | Severity | Issue |
|---|------|------|----------|-------|
| 1 | ...  | ...  | High     | ...   |

## 3. Detailed Recommendations
### Finding 1 — {short title} (line {n})
```{language}
{before code}
```

**Suggested fix**:
```{language}
{after code}
```
```

## 4. 호출 패턴

Claude:
```
> /skill code_review --target sample.py
```

Codex:
```
> use skill code_review on ./sample.py
```
