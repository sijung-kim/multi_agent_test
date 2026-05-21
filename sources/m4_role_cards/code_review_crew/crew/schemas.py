"""Pydantic 출력 스키마 — 예시 1 빌드 리뷰 (Galaxy 앱 개발팀).

Analyzer → Risk → Reviewer → Notifier 순서로 전달되는 정형 인터페이스.
각 Task의 output_pydantic 에 지정되어 자유 텍스트 출력을 방지한다.
"""

from enum import Enum
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class SeverityLevel(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
    INFO = "Info"


class RiskCategory(str, Enum):
    SECURITY = "Security"
    PERFORMANCE = "Performance"
    COMPATIBILITY = "Compatibility"


# ── Analyzer 출력 ─────────────────────────────────────────────────────────────

class ChangedFile(BaseModel):
    path: str = Field(..., description="변경된 파일 경로")
    change_type: Literal["added", "modified", "deleted"] = Field(
        ..., description="변경 유형"
    )
    lines_added: int = Field(default=0, ge=0)
    lines_removed: int = Field(default=0, ge=0)


class AnalysisResult(BaseModel):
    """Analyzer Agent 산출물 — 변경 범위 + 가이드라인 위반 목록."""

    changed_files: List[ChangedFile] = Field(
        ..., description="변경된 파일 목록"
    )
    total_changes: int = Field(
        ge=0, description="전체 변경 라인 수 (추가+삭제)"
    )
    affected_areas: List[str] = Field(
        default_factory=list,
        description="영향받는 기능 영역 (예: UI, Auth, Network)"
    )
    guideline_violations: List[str] = Field(
        default_factory=list,
        description="가이드라인 위반 항목 목록"
    )
    summary: str = Field(
        min_length=20,
        description="변경 범위 요약 — 20자 이상"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "changed_files": [
                    {"path": "app/auth/LoginActivity.kt",
                     "change_type": "modified",
                     "lines_added": 45, "lines_removed": 12}
                ],
                "total_changes": 57,
                "affected_areas": ["Auth", "UI"],
                "guideline_violations": ["하드코딩된 문자열 사용 (strings.xml 미등록)"],
                "summary": "로그인 화면 UI 개편 및 인증 로직 변경 — 보안 점검 필요"
            }
        }


# ── Risk Agent 출력 ───────────────────────────────────────────────────────────

class RiskItem(BaseModel):
    """개별 위험 항목."""

    category: RiskCategory
    severity: SeverityLevel
    file_path: str = Field(..., description="위험이 발견된 파일 경로")
    description: str = Field(
        min_length=10, max_length=400,
        description="위험 내용 설명"
    )
    recommendation: str = Field(
        min_length=10, max_length=300,
        description="권장 조치"
    )


class RiskReport(BaseModel):
    """Risk Agent 산출물 — 보안/성능/호환성 위험 목록."""

    risks: List[RiskItem] = Field(
        default_factory=list,
        description="탐지된 위험 항목 목록"
    )
    overall_severity: SeverityLevel = Field(
        ..., description="전체 위험 최고 심각도"
    )
    summary: str = Field(
        min_length=20,
        description="위험 분석 요약"
    )

    def has_blocking_risk(self) -> bool:
        """Critical/High 위험이 존재하면 True."""
        return any(
            r.severity in (SeverityLevel.CRITICAL, SeverityLevel.HIGH)
            for r in self.risks
        )


# ── Reviewer 출력 ─────────────────────────────────────────────────────────────

class ReviewComment(BaseModel):
    """개별 리뷰 코멘트."""

    file_path: str
    severity: SeverityLevel
    comment: str = Field(min_length=10, max_length=500)
    line_hint: Optional[str] = Field(
        default=None,
        description="관련 코드 줄 힌트 (예: L42~L55)"
    )


class ReviewReport(BaseModel):
    """Reviewer Agent 산출물 — 심각도 분류 + 리뷰 코멘트."""

    decision: Literal["APPROVE", "REQUEST_CHANGES", "COMMENT"] = Field(
        ..., description="리뷰 결정"
    )
    comments: List[ReviewComment] = Field(
        default_factory=list,
        description="파일별 리뷰 코멘트 목록"
    )
    summary: str = Field(
        min_length=30,
        description="리뷰 총평 — 30자 이상"
    )

    def critical_comments(self) -> List[ReviewComment]:
        """Critical/High 심각도 코멘트만 반환한다."""
        return [
            c for c in self.comments
            if c.severity in (SeverityLevel.CRITICAL, SeverityLevel.HIGH)
        ]


# ── Notifier 출력 (최종 산출물) ───────────────────────────────────────────────

class CodeReviewReport(BaseModel):
    """Notifier Agent 최종 산출물 — 전체 리뷰 결과 + 티켓 발행 현황."""

    pr_id: str = Field(..., description="Pull Request 또는 빌드 식별자")
    decision: Literal["APPROVE", "REQUEST_CHANGES", "COMMENT"]
    overall_severity: SeverityLevel
    risk_count: int = Field(ge=0, description="탐지된 위험 총 수")
    comment_count: int = Field(ge=0, description="작성된 리뷰 코멘트 총 수")
    review_summary: str = Field(
        min_length=30,
        description="리뷰 최종 요약"
    )
    slack_message_id: Optional[str] = Field(
        default=None, description="Slack 메시지 ID"
    )
    jira_ticket_ids: List[str] = Field(
        default_factory=list,
        description="생성된 Jira 티켓 ID 목록"
    )
    channels_notified: List[str] = Field(
        default_factory=list,
        description="알림을 전송한 채널 목록"
    )

    def is_blocking(self) -> bool:
        return self.decision == "REQUEST_CHANGES"
