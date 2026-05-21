"""@tool 데코레이터 기반 외부 도구.

본 모듈의 도구들은 Worker가 동작에 필요한 외부 컨텍스트를 가져오기 위해 호출된다.
"""

from pathlib import Path
from typing import List, Dict
import re

try:
    from crewai_tools import tool
except ImportError:  # CrewAI/CrewAI Tools 버전 호환
    from crewai.tools import tool


@tool("Diff Reader")
def diff_reader(path: str) -> str:
    """build diff 파일을 읽고 전체 내용을 반환한다.

    Args:
        path: diff 파일의 절대 또는 상대 경로

    Returns:
        diff 파일 전체 텍스트
    """
    p = Path(path)
    if not p.exists():
        return f"[ERROR] diff file not found: {path}"
    if p.stat().st_size > 5_000_000:   # 5MB 가드
        return f"[ERROR] diff file too large (>5MB): {path}"
    return p.read_text(encoding="utf-8", errors="replace")


@tool("Area Classifier")
def area_classifier(diff_text: str) -> Dict[str, List[str]]:
    """diff 텍스트를 도메인별로 분류해 영향 매트릭스를 반환한다.

    경로 패턴 기반 분류 — 운영 환경에서는 LLM 분류로 대체 가능.

    Args:
        diff_text: diff_reader 가 반환한 전체 텍스트

    Returns:
        도메인별 영향 파일 목록 dict
    """
    domain_patterns = {
        "UI":     [r"\bui/", r"\bview/", r"\blayout/", r"\bres/drawable"],
        "Perf":   [r"\bperf/", r"\bbenchmark/", r"render/", r"thread"],
        "Compat": [r"\bcompat/", r"sdk/", r"androidx/", r"manifest"],
        "L10n":   [r"\bi18n/", r"\blocale/", r"values-"],
        "Knox":   [r"\bknox/", r"security/", r"crypto/", r"auth/"],
    }

    matrix: Dict[str, List[str]] = {d: [] for d in domain_patterns}

    # diff blocks separator: "diff --git"
    for block in diff_text.split("diff --git"):
        if not block.strip():
            continue
        # 첫 줄에서 파일 경로 추출
        first_line = block.splitlines()[0] if block.splitlines() else ""
        for domain, patterns in domain_patterns.items():
            if any(re.search(p, block[:500], re.IGNORECASE) for p in patterns):
                # 파일 경로 추출 (간략)
                m = re.search(r"a/([^\s]+)", first_line)
                if m:
                    matrix[domain].append(m.group(1))

    # 중복 제거
    return {d: sorted(set(files)) for d, files in matrix.items()}


@tool("Module Lookup")
def module_lookup(module_path: str, project_root: str = ".") -> str:
    """모듈 경로를 받아 모듈의 짧은 메타데이터(파일 존재·라인 수)를 반환한다.

    Worker가 영향 평가 시 모듈의 실제 존재 여부와 규모를 확인하는 용도다.

    Args:
        module_path: 'ui/dark_mode/ToggleView.kt' 등의 상대 경로
        project_root: 프로젝트 루트 디렉터리

    Returns:
        모듈 메타데이터 요약 문자열
    """
    full = Path(project_root) / module_path
    if not full.exists():
        return f"[NOT FOUND] {module_path}"
    try:
        lines = full.read_text(encoding="utf-8", errors="replace").count("\n")
        return f"[OK] {module_path} · {lines} lines · {full.stat().st_size} bytes"
    except Exception as e:
        return f"[ERROR] {module_path} · {type(e).__name__}: {e}"


@tool("Severity Estimator")
def severity_estimator(domain: str, affected_modules: List[str]) -> int:
    """도메인과 영향 모듈 수로 기본 severity를 추정한다.

    Worker가 최종 판정을 내리기 전 1차 추정치를 제공하는 보조 도구.
    Worker가 도메인 컨텍스트와 결합해 최종 severity를 결정한다.

    Args:
        domain: 평가 도메인 (UI · Perf · Compat · L10n · Knox)
        affected_modules: 영향받는 모듈 경로 목록

    Returns:
        1~5 사이의 severity 추정치
    """
    n = len(affected_modules)
    base = {
        "UI": 2, "Perf": 3, "Compat": 3, "L10n": 2, "Knox": 4,
    }.get(domain, 2)

    if n == 0:
        return 1
    if n <= 2:
        return min(5, base)
    if n <= 5:
        return min(5, base + 1)
    return 5
