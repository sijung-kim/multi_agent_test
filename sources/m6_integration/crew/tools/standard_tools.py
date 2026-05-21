"""@tool 다중 도구 정의 — 외부 시스템 호출을 표준 인터페이스로 통합한다.

본 모듈의 도구들은 M5의 Worker에 등록되어 동작 컨텍스트를 풍부하게 만든다.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any

import requests

try:
    from crewai_tools import tool
except ImportError:  # CrewAI/CrewAI Tools 버전 호환
    from crewai.tools import tool


@tool("Diff Reader")
def diff_reader(path: str) -> str:
    """build diff 파일을 읽고 전체 텍스트를 반환한다.

    Args:
        path: diff 파일의 절대/상대 경로
    """
    p = Path(path)
    if not p.exists():
        return f"[ERROR] diff file not found: {path}"
    if p.stat().st_size > 5_000_000:
        return f"[ERROR] diff file too large (>5MB): {path}"
    return p.read_text(encoding="utf-8", errors="replace")


@tool("Area Classifier")
def area_classifier(diff_text: str, domains: List[str] = None) -> Dict[str, List[str]]:
    """diff 텍스트를 도메인별로 분류해 영향 매트릭스를 반환한다.

    Args:
        diff_text: diff_reader 가 반환한 텍스트
        domains: 분류할 도메인 목록 (기본 5종)
    """
    if domains is None:
        domains = ["UI", "Perf", "Compat", "L10n", "Knox"]

    matrix: Dict[str, List[str]] = {d: [] for d in domains}
    patterns = {
        "UI":     ["ui/", "view/", "layout/", "drawable"],
        "Perf":   ["perf/", "render", "thread", "benchmark"],
        "Compat": ["compat/", "manifest", "sdk/"],
        "L10n":   ["i18n/", "values-", "locale"],
        "Knox":   ["knox/", "crypto/", "security/", "auth/"],
    }

    for block in diff_text.split("diff --git"):
        if not block.strip():
            continue
        head = block[:300].lower()
        for domain in domains:
            ps = patterns.get(domain, [])
            if any(kw.lower() in head for kw in ps):
                # 파일 경로 추출
                first = block.splitlines()[0] if block.splitlines() else ""
                import re
                m = re.search(r"a/([^\s]+)", first)
                if m:
                    matrix[domain].append(m.group(1))

    return {d: sorted(set(files)) for d, files in matrix.items()}


@tool("Slack Notifier")
def slack_notifier(channel: str, message: str) -> str:
    """결과를 Slack 채널에 전송한다.

    환경변수 SLACK_BOT_TOKEN 이 필요하다. 운영 환경에서는 PagerDuty 등으로 확장.

    Args:
        channel: 채널 ID 또는 이름 (예: #build-triage)
        message: 전송할 메시지 (마크다운 지원)
    """
    token = os.getenv("SLACK_BOT_TOKEN", "")
    if not token:
        return f"[SKIP] SLACK_BOT_TOKEN not configured · channel={channel}"

    try:
        resp = requests.post(
            "https://slack.com/api/chat.postMessage",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json; charset=utf-8",
            },
            json={"channel": channel, "text": message},
            timeout=10,
        )
        data = resp.json()
        if data.get("ok"):
            return f"[OK] sent · channel={channel} · ts={data.get('ts')}"
        return f"[FAIL] {data.get('error')} · channel={channel}"
    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {e}"


@tool("Build Report Writer")
def build_report_writer(
    report_path: str,
    report_content: str,
) -> str:
    """Build Triage 리포트를 파일로 저장한다.

    Args:
        report_path: 저장 경로 (예: ./reports/build-2026-05-20.md)
        report_content: 마크다운 형식 리포트 내용
    """
    p = Path(report_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    try:
        p.write_text(report_content, encoding="utf-8")
        return f"[OK] saved · {p} · {len(report_content)} bytes"
    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {e}"


@tool("JSON Dump")
def json_dump(payload: Dict[str, Any], path: str) -> str:
    """Python dict을 JSON 파일로 저장한다.

    Args:
        payload: 직렬화할 dict
        path: 저장 경로
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    try:
        p.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        return f"[OK] saved · {p}"
    except Exception as e:
        return f"[ERROR] {type(e).__name__}: {e}"
