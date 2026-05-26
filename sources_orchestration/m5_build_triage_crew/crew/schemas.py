"""Pydantic 출력 스키마.

에이전트 출력이 자유 텍스트가 아니라 정형 객체로 산출되도록 강제한다.
스키마 정의가 곧 인터페이스 계약이며, 후속 처리(DB 저장·API 응답·Slack 알림)의 안정성을 결정한다.
"""

from enum import Enum
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class DecisionType(str, Enum):
    """Build Triage 최종 판정."""
    GO = "GO"
    NO_GO = "NO_GO"
    HOLD = "HOLD"   # 추가 정보 필요


class Domain(str, Enum):
    """본 Crew가 다루는 5개 도메인."""
    UI = "UI"
    PERF = "Perf"
    COMPAT = "Compat"
    L10N = "L10n"
    KNOX = "Knox"


class DomainImpact(BaseModel):
    """도메인별 영향 범위."""

    domain: Domain
    affected_modules: List[str] = Field(
        default_factory=list,
        description="해당 도메인에서 검토할 모듈/패키지 경로 목록"
    )
    rationale: str = Field(
        min_length=20, max_length=500,
        description="도메인 분류 근거"
    )


class BuildImpactScope(BaseModel):
    """초기 diff 분석 산출물 — Worker에게 넘길 영향 범위."""

    build_id: str = Field(..., description="nightly build 식별자")
    total_changed_files: int = Field(
        ge=0,
        description="diff에서 식별한 변경 파일 수"
    )
    domains_to_review: List[DomainImpact] = Field(
        ..., min_length=1, max_length=5,
        description="Worker 검토가 필요한 도메인별 영향 범위"
    )
    summary: str = Field(
        min_length=50,
        description="변경 범위와 위임 계획 요약"
    )


class WorkerVerdict(BaseModel):
    """Worker 단위 도메인 평가 결과."""

    domain: Domain = Field(..., description="평가 대상 도메인")
    severity: int = Field(
        ge=1, le=5,
        description="회귀 위험 1(낮음) ~ 5(높음)"
    )
    affected_modules: List[str] = Field(
        default_factory=list,
        description="영향받는 모듈/패키지 경로 목록"
    )
    rationale: str = Field(
        min_length=20, max_length=500,
        description="평가 근거 — 변경 영역과 위험 분석"
    )
    suggested_fix_hours: Optional[float] = Field(
        default=None,
        description="예상 수정 소요 시간 (시간 단위)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "domain": "UI",
                "severity": 4,
                "affected_modules": [
                    "ui/dark_mode/ToggleView.kt",
                    "ui/i18n/LocaleManager.kt"
                ],
                "rationale": (
                    "다크 모드 토글 위젯에서 색상 매핑 변경 — "
                    "기존 사용자 설정 호환성에 영향. 다국어 정렬 회귀 가능성 있음."
                ),
                "suggested_fix_hours": 4.5
            }
        }


class BuildTriageReport(BaseModel):
    """Manager 통합 산출물 — 최종 판정 + 우선순위 보고서."""

    build_id: str = Field(..., description="nightly build 식별자")
    decision: DecisionType
    priority: int = Field(
        ge=1, le=5,
        description="P1(최우선) ~ P5(낮음)"
    )
    worker_verdicts: List[WorkerVerdict] = Field(
        ..., min_length=1, max_length=5,
        description="도메인별 Worker 평가 결과"
    )
    summary: str = Field(
        min_length=50,
        description="임원 보고용 1단락 요약"
    )
    estimated_fix_hours: Optional[float] = Field(
        default=None,
        description="전체 예상 수정 소요 시간 (Worker별 합산)"
    )
    confidence: Literal["high", "medium", "low"] = Field(
        default="medium",
        description="판정 신뢰도 — Worker 간 합의 정도에 따라"
    )

    def is_blocking(self) -> bool:
        """배포를 차단해야 하는 판정인지 확인한다."""
        return self.decision == DecisionType.NO_GO

    def critical_domains(self) -> List[Domain]:
        """severity 4 이상인 도메인 목록을 반환한다."""
        return [
            v.domain for v in self.worker_verdicts
            if v.severity >= 4
        ]
