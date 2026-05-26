---
name: doc_generator
description: 함수·클래스·모듈의 docstring 을 PEP 257 / Google Style 양식으로 자동 생성한다
version: 1.0
inputs:
  - target_path: 대상 Python 파일 경로 (필수)
  - style: docstring 양식 — google / numpy / sphinx (기본 google)
  - include_examples: 사용 예시 포함 여부 — true / false (기본 false)
outputs:
  - target_path 파일이 docstring 이 추가된 형태로 수정됨
  - doc_summary.md: 생성된 docstring 의 요약 보고서
---

# Docstring 자동 생성 절차

## 1. 대상 식별

- `target_path` 파일을 읽고 AST 로 파싱한다.
- 다음을 docstring 추가 대상으로 선정한다:
  - 모듈 최상단 (모듈 docstring)
  - 모든 클래스 정의
  - 모든 함수 정의 (`_` 로 시작하는 private 제외 가능)

## 2. 시그니처 분석

각 함수에 대해:
- 함수명·인자명·인자 타입 hint·반환 타입 hint·decorator 를 추출
- 함수 본문에서 raise 구문을 식별하여 Raises 섹션 후보 추출
- 함수 본문의 첫 5줄로 동작 요약 후보 추출

## 3. Docstring 생성 (style 별)

### Google Style (기본)

```python
def divide(a: float, b: float) -> float:
    """두 수의 나눗셈 결과를 반환한다.

    Args:
        a: 피제수 (dividend).
        b: 제수 (divisor). 0 이 아니어야 한다.

    Returns:
        a / b 의 결과.

    Raises:
        ValueError: b 가 0 일 때.

    Example:
        >>> divide(10, 2)
        5.0
    """
    if b == 0:
        raise ValueError("divisor must be non-zero")
    return a / b
```

### NumPy Style

```python
def divide(a: float, b: float) -> float:
    """두 수의 나눗셈 결과를 반환한다.

    Parameters
    ----------
    a : float
        피제수.
    b : float
        제수. 0 이 아니어야 한다.

    Returns
    -------
    float
        a / b 의 결과.

    Raises
    ------
    ValueError
        b 가 0 일 때.
    """
```

## 4. 작성 원칙

- 첫 줄은 명령형 1문장 요약 (최대 80자).
- Args / Returns / Raises 섹션은 해당 정보가 있을 때만 추가.
- `include_examples=true` 일 때만 Example 섹션 추가.
- 한국어 docstring 을 우선 사용하되, 함수 시그니처의 한자어는 영문 용어 병기.

## 5. 수정 적용

- 원본 파일을 백업 (`target_path.bak`) 후 docstring 이 삽입된 형태로 덮어쓴다.
- 기존 docstring 이 있는 경우 덮어쓰지 않고 건너뛴다 (`--force` 옵션 시 덮어쓰기 가능).

## 6. 요약 보고서

`doc_summary.md` 에 다음을 기록한다:

```markdown
# Docstring Generation Summary

**Target**: {target_path}
**Style**: {style}

## Generated
- {N}개 함수에 docstring 추가
- {M}개 클래스에 docstring 추가
- {K}개 항목은 기존 docstring 존재로 건너뜀

## Skipped (이유)
| Function | Reason |
|---|---|
| _private_helper | private 함수 |
```

## 7. 검증

- [ ] 모든 public 함수에 docstring 이 있는가
- [ ] Args 의 인자명이 함수 시그니처와 일치하는가
- [ ] Raises 의 예외가 실제 raise 구문과 일치하는가
- [ ] 한국어 자연스러움 (기계 번역체 회피)
