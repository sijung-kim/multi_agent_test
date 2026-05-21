"""MCP(Model Context Protocol) 통합 도구.

MCP 서버를 통한 외부 시스템 호출을 Worker가 직접 호출 가능한 @tool 로 래핑한다.
본 예시는 Filesystem MCP 서버를 기준으로 작성되었으며, GitHub·Slack·Postgres MCP 도 동일 패턴으로 추가할 수 있다.
"""

import os
import subprocess
import json
from typing import List, Optional

try:
    from crewai_tools import tool
except ImportError:  # CrewAI/CrewAI Tools 버전 호환
    from crewai.tools import tool


# MCP 서버 호출 헬퍼
def _mcp_call(server_name: str, command: str, args: List[str], timeout: int = 30) -> str:
    """MCP 서버를 subprocess로 호출하고 결과를 반환한다.

    실제 운영에서는 MCP SDK의 client 라이브러리를 사용하는 것이 권장된다.
    본 예시는 학습 목적의 최소 호출 형태다.
    """
    try:
        result = subprocess.run(
            ["mcp-client", server_name, command, *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
        )
        if result.returncode != 0:
            return f"[MCP ERROR] {server_name}/{command}: {result.stderr[:200]}"
        return result.stdout
    except subprocess.TimeoutExpired:
        return f"[MCP TIMEOUT] {server_name}/{command} after {timeout}s"
    except FileNotFoundError:
        return (
            f"[MCP UNAVAILABLE] mcp-client 가 설치되지 않았습니다. "
            f"npm install -g @modelcontextprotocol/cli 로 설치하세요."
        )
    except Exception as e:
        return f"[MCP ERROR] {type(e).__name__}: {e}"


@tool("Filesystem Search")
def fs_search(query: str, root: Optional[str] = None) -> str:
    """파일시스템 MCP를 통한 코드 검색.

    Args:
        query: 검색어 (정규식 가능)
        root: 검색 루트 디렉터리 (기본은 환경변수 MCP_FILESYSTEM_ROOT)
    """
    if root is None:
        root = os.getenv("MCP_FILESYSTEM_ROOT", "./crew")
    return _mcp_call(
        "filesystem", "search",
        ["--query", query, "--root", root]
    )


@tool("Filesystem Read")
def fs_read(path: str) -> str:
    """MCP를 통한 안전한 파일 읽기 (권한 제어 우회 방지).

    Args:
        path: 읽을 파일의 경로 (MCP_FILESYSTEM_ROOT 하위로 제한됨)
    """
    return _mcp_call("filesystem", "read", ["--path", path])


@tool("Filesystem List")
def fs_list(directory: str = ".") -> str:
    """디렉터리 내 파일 목록을 반환한다.

    Args:
        directory: 대상 디렉터리 (기본은 현재 디렉터리)
    """
    return _mcp_call("filesystem", "list", ["--dir", directory])


@tool("GitHub Issue Search")
def github_issue_search(repo: str, query: str) -> str:
    """GitHub MCP를 통한 이슈 검색 (선택적 — GitHub MCP 서버 설치 필요).

    Args:
        repo: 'owner/repo' 형식
        query: 이슈 검색 쿼리
    """
    return _mcp_call(
        "github", "search-issues",
        ["--repo", repo, "--q", query]
    )


# 도구 카탈로그 (Worker 등록용 헬퍼)
MCP_TOOLS_FILESYSTEM = [fs_search, fs_read, fs_list]
MCP_TOOLS_GITHUB = [github_issue_search]
MCP_TOOLS_ALL = MCP_TOOLS_FILESYSTEM + MCP_TOOLS_GITHUB
