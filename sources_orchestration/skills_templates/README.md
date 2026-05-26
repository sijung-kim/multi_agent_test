# Skill 템플릿 — 사후 학습 자료

본 폴더는 본인 업무에 즉시 적용 가능한 Skill MD 파일 3종 양식이다.

각 Skill은 frontmatter(name·description·inputs·outputs) + 본문(절차) 구조로 작성되었으며, Claude·Codex 양 도구에서 동일한 인터페이스로 호출 가능하다.

## 폴더 구성

```
skills_templates/
├── README.md
├── skill_code_review.md         # 코드 리뷰 자동화
├── skill_doc_generator.md       # docstring 자동 생성
└── skill_log_analyzer.md        # 로그 파일 분석·이슈 추출
```

## 사용 방법

### 1. Skill 폴더에 배치

본인 프로젝트의 `skills/` 폴더에 복사한다.

```bash
mkdir -p myproject/skills/
cp skills_templates/*.md myproject/skills/
```

### 2. 호출

#### Claude Code 에서
```
> /skill code_review --target ./src/auth.py
```

#### Codex CLI 에서
```
> use skill code_review on ./src/auth.py
```

### 3. 본인 업무에 맞게 수정

각 Skill의 본문에 도메인별 검증 차원·금기 패턴·필수 출력 형식을 추가한다.

## 작성 원칙

| 원칙 | 적용 |
|---|---|
| **명확한 inputs/outputs** | 호출자가 무엇을 줘야 하고 무엇을 받는지 frontmatter에 명시 |
| **단계화된 절차** | 1) ... 2) ... 3) ... 형식의 순서 명시 |
| **검증 기준** | 각 단계의 완료 조건을 체크리스트로 명시 |
| **재사용 가능성** | 도메인 의존도를 낮추고 입력 파라미터로 분기 |

## 권장 학습 경로

1. 본 3개 템플릿을 그대로 본인 프로젝트에서 호출해본다.
2. 출력이 기대와 다른 부분을 식별하여 본문 절차를 수정한다.
3. 본인 도메인에 특화된 새 Skill 1개를 처음부터 작성한다.
4. 팀에 공유하여 사내 Skill 카탈로그를 구축한다.
