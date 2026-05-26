# Code Review Report

**Reviewer**: Codex CLI v0.x
**Target**: sources/m2_harness_demo/sample.py
**Generated**: 2026-05-21T14:32:32.7346520+09:00

## 1. Summary

- Files changed: 1
- Lines added: +31
- Lines removed: -0
- Risk level: **Low**

## 2. Findings

| # | File | Line | Severity | Issue |
|---|------|------|----------|-------|
| 1 | sources/m2_harness_demo/sample.py | 30 | Low | `__main__` 블록이 `pass`만 포함해 샘플 함수의 실행 확인 경로가 없다. |

## 3. Detailed Recommendations

### Finding 1 — 실행 확인 경로 부재 (line 30)

현재 산술 함수 자체는 단순하고 타입 힌트와 docstring이 적절합니다. 로직 정합성, 보안, 성능 측면에서 즉시 수정해야 할 결함은 발견되지 않았습니다.

다만 이 파일이 harness demo용 샘플이라면 `__main__` 블록이 비어 있어 직접 실행 시 함수 동작을 확인할 수 없습니다.

```python
if __name__ == "__main__":
    pass
```

**Suggested fix**:
```python
if __name__ == "__main__":
    print(f"add(2, 3) = {add(2, 3)}")
    print(f"multiply(2, 3) = {multiply(2, 3)}")
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
