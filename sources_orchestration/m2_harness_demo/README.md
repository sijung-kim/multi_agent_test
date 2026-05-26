# M2 — 하네스 데모 (Codex × Claude 협업)

VS Code 안에서 Codex CLI와 Claude Code가 협업하여 코드를 생성·검토하는 하네스 데모.

## 협업 흐름

```
사용자 ──지시──→ Claude (sample.py 작성)
                ↓
            sample.py 생성
                ↓
사용자 ──지시──→ Codex (code_review Skill 호출)
                ↓
            review_report.md 생성
```

## 폴더 구성

```
m2_harness_demo/
├── README.md
├── skills/
│   └── code_review.md       # Skill MD 파일 (실행 절차 정의)
├── sample.py                # Claude 산출물 예시
└── review_report.md         # Codex 산출물 예시
```

## 실습 절차 (M2 슬라이드 9~13)

### Step 1. VS Code 두 CLI 분할

```bash
# VS Code 터미널 단축키: Ctrl + Shift + `
# 좌측 패널
codex

# 우상단 분할 아이콘 → 우측 패널
claude
```

### Step 2. Skill 정의 (이미 작성됨)

`skills/code_review.md` 파일이 이미 준비되어 있다. Claude·Codex 모두 동일한 Skill을 호출한다.

### Step 3. Claude가 코드 작성 (Claude 호출 1회)

우측 Claude 패널에서:

```
> /skill code_review 를 참고하여 sample.py 파일을 작성하라.
> 요구 사항:
>   - 함수 add(a, b)와 multiply(a, b) 포함
>   - 각 함수에 docstring 명시
>   - 빈 main 가드 추가
```

### Step 4. Codex가 검토

좌측 Codex 패널에서:

```
> use skill code_review on ./sample.py
> 결과를 review_report.md 로 저장하라.
```

## 산출물

| 파일 | 생성 주체 |
|---|---|
| `skills/code_review.md` | 사전 작성 (재사용) |
| `sample.py` | Claude (Step 3 산출) |
| `review_report.md` | Codex (Step 4 산출) |

## 도구 전환 시점

- **Claude (호출 1회만)**: Step 3 코드 작성 (5천원 크레딧 안전 운영)
- **Codex (메인)**: Skill 정의·검토·후속 모든 작업
