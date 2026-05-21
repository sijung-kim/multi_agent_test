"""@tool 데코레이터 기반 외부 도구 — 예시 1 빌드 리뷰.

실제 운영에서는 GitHub API, Jira REST API, Slack API로 교체한다.
학습 목적으로 파일 I/O와 시뮬레이션 구현을 사용한다.
"""

import json
import re
from pathlib import Path
from typing import Dict, List

from crewai.tools import tool


@tool("Code Diff Reader")
def code_diff_reader(path: str) -> str:
    """소스코드 diff 파일을 읽고 전체 내용을 반환한다.

    Args:
        path: diff 파일의 절대 또는 상대 경로

    Returns:
        diff 파일 전체 텍스트
    """
    p = Path(path)
    if not p.exists():
        return f"[ERROR] diff file not found: {path}"
    if p.stat().st_size > 5_000_000:
        return f"[ERROR] diff file too large (>5MB): {path}"
    return p.read_text(encoding="utf-8", errors="replace")


@tool("Guideline Reader")
def guideline_reader(guideline_path: str) -> str:
    """개발 가이드라인 문서를 읽어 반환한다.

    코딩 컨벤션, 보안 체크리스트, 성능 기준 등을 포함한 가이드라인 파일을 로드한다.

    Args:
        guideline_path: 가이드라인 파일 경로 (.md, .txt, .pdf 등)

    Returns:
        가이드라인 전체 텍스트
    """
    p = Path(guideline_path)
    if not p.exists():
        # 가이드라인 파일이 없을 경우 기본 Galaxy 앱 개발 가이드라인을 반환
        return (
            "# Galaxy 앱 개발 가이드라인 (기본)\n\n"
            "## 보안\n"
            "- API 키, 비밀번호, 토큰을 소스코드에 하드코딩 금지\n"
            "- 사용자 입력은 반드시 검증 후 처리\n"
            "- HTTPS 사용 필수 (HTTP 사용 금지)\n\n"
            "## 성능\n"
            "- 메인 스레드에서 네트워크/DB 호출 금지\n"
            "- 중첩 루프 최소화 (O(n²) 이상 경고)\n"
            "- 메모리 누수 방지 (WeakReference 활용)\n\n"
            "## 호환성\n"
            "- minSdk 26 (Android 8.0) 이상 호환성 보장\n"
            "- deprecated API 사용 금지\n"
            "- AndroidX 마이그레이션 완료 필수\n\n"
            "## 코드 품질\n"
            "- 하드코딩 문자열은 strings.xml 에 등록\n"
            "- 함수 길이 80줄 이하 권장\n"
            "- 단위 테스트 커버리지 70% 이상\n"
        )
    return p.read_text(encoding="utf-8", errors="replace")


@tool("Risk Pattern Scanner")
def risk_pattern_scanner(diff_text: str) -> Dict[str, List[str]]:
    """diff 텍스트에서 보안·성능·호환성 위험 패턴을 스캔한다.

    정규식 기반 1차 스캔 — 운영 환경에서는 정적 분석 도구로 대체 가능.

    Args:
        diff_text: code_diff_reader 가 반환한 diff 텍스트

    Returns:
        카테고리별 탐지된 패턴 목록 dict
    """
    patterns: Dict[str, List[str]] = {
        "Security": [
            r'password\s*=\s*["\'][^"\']+["\']',
            r'api[_-]?key\s*=\s*["\'][^"\']+["\']',
            r'token\s*=\s*["\'][^"\']+["\']',
            r'secret\s*=\s*["\'][^"\']+["\']',
            r'\beval\s*\(',
            r'\bexec\s*\(',
            r'http://(?!localhost)',          # HTTP (비 HTTPS)
            r'Log\.[dviwe]\s*\(.*password',   # 로그에 민감정보
        ],
        "Performance": [
            r'for\s+\w+\s+in\s+.*:\s*\n\s+for\s+\w+\s+in',   # 중첩 루프
            r'runOnUiThread.*\b(network|http|db|database)\b',   # UI 스레드 IO
            r'Thread\.sleep\s*\(',
            r'\.size\s*>\s*0',               # isEmpty() 대신 size>0 사용
        ],
        "Compatibility": [
            r'@RequiresApi\s*\(\s*Build\.VERSION_CODES\.',
            r'Build\.VERSION\.SDK_INT\s*<\s*\d+',
            r'@Deprecated',
            r'import\s+android\.support\.',  # AndroidX 미전환
        ],
    }

    results: Dict[str, List[str]] = {}
    for category, pats in patterns.items():
        matches = []
        for pat in pats:
            found = re.findall(pat, diff_text, re.IGNORECASE | re.MULTILINE)
            if found:
                matches.extend([f"패턴 `{pat[:40]}`: {str(m)[:60]}" for m in found[:2]])
        if matches:
            results[category] = matches

    if not results:
        results["Info"] = ["명시적 위험 패턴 없음 — LLM 기반 심층 분석 권장"]

    return results


@tool("Slack Notifier")
def slack_notifier(channel: str, message: str) -> str:
    """Slack 채널에 리뷰 결과를 전송한다 (시뮬레이션).

    실제 운영에서는 slack_sdk 또는 Webhook URL로 교체한다.

    Args:
        channel: Slack 채널명 (예: code-review-alerts)
        message: 전송할 메시지 본문

    Returns:
        전송 결과 JSON 문자열
    """
    msg_id = f"slack-{abs(hash(message)) % 100_000:05d}"
    return json.dumps({
        "ok": True,
        "channel": channel,
        "message_id": msg_id,
        "preview": message[:100] + ("..." if len(message) > 100 else ""),
        "note": "[SIMULATED] 실제 Slack API 호출 없음",
    }, ensure_ascii=False)


@tool("Jira Ticket Creator")
def jira_ticket_creator(
    project: str,
    description: str,
    severity: str,
    title: str = "",
) -> str:
    """Jira 프로젝트에 이슈 티켓을 생성한다 (시뮬레이션).

    실제 운영에서는 jira-python 라이브러리 또는 REST API로 교체한다.

    Args:
        project: Jira 프로젝트 키 (예: GALAXYAPP)
        description: 이슈 상세 설명 (파일 경로, 위험 내용, 권장 조치 포함)
        severity: 심각도 (Critical / High / Medium / Low / Info)
        title: 이슈 제목 (생략 시 description 앞 60자 자동 사용)

    Returns:
        생성된 티켓 정보 JSON 문자열
    """
    if not title:
        title = description[:60].replace("\n", " ")
    ticket_id = f"{project}-{abs(hash(title)) % 9_000 + 1_000}"
    return json.dumps({
        "id": ticket_id,
        "key": ticket_id,
        "project": project,
        "title": title,
        "severity": severity,
        "status": "Open",
        "url": f"https://jira.example.com/browse/{ticket_id}",
        "note": "[SIMULATED] 실제 Jira API 호출 없음",
    }, ensure_ascii=False)
