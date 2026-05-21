---
name: log_analyzer
description: 로그 파일을 받아 이상 패턴·에러 클러스터·시계열 트렌드를 추출하여 진단 리포트를 생성한다
version: 1.0
inputs:
  - log_path: 분석 대상 로그 파일 경로 (필수)
  - time_window: 분석 시간 범위 — last_1h / last_24h / last_7d / all (기본 last_24h)
  - severity_filter: 분석할 최소 레벨 — DEBUG / INFO / WARN / ERROR / FATAL (기본 WARN)
outputs:
  - log_diagnosis.md: 진단 리포트
  - error_clusters.json: 에러 클러스터링 결과 (구조화 데이터)
---

# 로그 분석 절차

## 1. 로그 파싱

- `log_path` 파일을 읽고 다음 형식을 자동 감지한다:
  - JSON 라인 (`{"ts":..., "level":..., "msg":...}`)
  - 표준 syslog 형식
  - Python logging 기본 형식
- 파싱 실패 라인은 raw_lines 카운트로 별도 집계한다.

## 2. 시간 범위 필터링

- `time_window` 기준으로 분석 대상 라인을 선별한다.
- 타임스탬프가 없는 라인은 raw_lines 로 분류한다.

## 3. 레벨별 집계

각 로그 레벨의 발생 빈도와 시계열 분포를 산출한다:

| 레벨 | 정상 임계 | 경고 임계 | 위험 임계 |
|---|---|---|---|
| WARN | < 10/min | 10~50/min | > 50/min |
| ERROR | < 1/min | 1~10/min | > 10/min |
| FATAL | 0 | 1~3/hour | > 3/hour |

## 4. 에러 클러스터링

ERROR·FATAL 레벨의 메시지를 다음 기준으로 클러스터링:

1. 메시지의 정규화된 패턴 (숫자·UUID 제거) 기준 그룹화
2. 동일 패턴 메시지의 빈도·첫 발생·마지막 발생 시각 기록
3. 클러스터별 대표 stacktrace 1개를 샘플로 보존

## 5. 이상 패턴 식별

다음 패턴을 우선 식별한다:

| 패턴 | 식별 기준 |
|---|---|
| **Burst** | 5분 이내 동일 클러스터 100건 이상 |
| **Trending** | 직전 시간 대비 200% 증가 |
| **New** | 이전 7일 내 발생하지 않은 신규 클러스터 |
| **Silent Recovery** | 30분 이상 미발생 후 재발 |

## 6. 시계열 트렌드

- 1시간 단위 버킷의 에러 빈도 시계열을 산출한다.
- 이상 점프(평균 + 3σ) 시점을 명시한다.

## 7. 진단 리포트 작성

`log_diagnosis.md` 양식:

```markdown
# Log Diagnosis Report

**Target**: {log_path}
**Time Window**: {time_window}
**Generated**: {ISO timestamp}

## 1. Overview
- Total lines: {n}
- WARN: {x} · ERROR: {y} · FATAL: {z}
- Anomalies detected: {count}

## 2. Top Error Clusters
| # | Pattern | Count | First Seen | Last Seen | Severity |
|---|---------|-------|------------|-----------|----------|

## 3. Anomaly Detection
### Anomaly 1 — Burst Pattern (16:30 ~ 16:35)
- Cluster: "Database connection timeout"
- Count: 247 (직전 시간 평균 12 대비 +1958%)
- Sample stacktrace:
  ```
  ...
  ```

## 4. Recommendations
- 즉시 조치: ...
- 단기 조치: ...
- 모니터링 추가: ...
```

## 8. 구조화 출력

`error_clusters.json` 에 클러스터 데이터를 다음 형식으로 산출한다:

```json
{
  "generated_at": "2026-05-20T15:32:01Z",
  "time_window": "last_24h",
  "clusters": [
    {
      "pattern": "Database connection timeout: %s",
      "count": 247,
      "first_seen": "2026-05-20T14:23:01Z",
      "last_seen": "2026-05-20T16:35:42Z",
      "severity": "ERROR",
      "sample": "Database connection timeout: db-prod-3",
      "anomaly_type": "burst"
    }
  ]
}
```

## 9. 검증 체크리스트

- [ ] 파싱 실패율이 5% 미만인가
- [ ] 모든 anomaly 에 식별 기준(burst·trending·new·silent recovery)이 명시되었는가
- [ ] Top 클러스터의 sample stacktrace 가 동봉되었는가
- [ ] 권고에 우선순위(즉시/단기/모니터링)가 명시되었는가
