#!/usr/bin/env python3
"""
MuukTest Repair MCP Server
Analyzes E2E test failures and provides repair suggestions.
"""
import asyncio
import base64
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

app = Server("muuk-test-repair")

# API Configuration
API_URL = os.getenv(
    "MUUK_API_URL",
    "https://bm5s428g6e.execute-api.us-east-2.amazonaws.com/staging",
)
MUUK_API_KEY = os.getenv("MUUK_API_KEY", "")

REQUEST_TIMEOUT_SECS = int(os.getenv("MUUK_TIMEOUT_SECS", "300"))
MAX_SCREENSHOT_BYTES = int(os.getenv("MUUK_MAX_SCREENSHOT_BYTES", str(8 * 1024 * 1024)))
MAX_FILES = int(os.getenv("MUUK_MAX_FILES", "25"))
MAX_CHARS_PER_FILE = int(os.getenv("MUUK_MAX_CHARS_PER_FILE", "120000"))
EXCLUDE_DIRS = {"node_modules", ".git", "dist", "build", "playwright-report", ".next", "__pycache__", ".pytest_cache"}
SUPPORTED_TEST_EXTS = {".ts", ".tsx", ".js", ".jsx", ".json", ".py"}


def _norm_path(p: str) -> Path:
    """Normalize path to absolute."""
    path = Path(p).expanduser()
    if not path.is_absolute():
        path = Path.cwd() / path
    return path.resolve()


def _read_text_file(path: Path) -> str:
    """Read text file content."""
    return path.read_text(encoding="utf-8")


def _read_json_file(path: Path) -> Any:
    """Read and parse JSON file."""
    return json.loads(_read_text_file(path))


def _encode_image_to_base64(image_path: Path) -> str:
    """Encode image file to base64 string."""
    size = image_path.stat().st_size
    if size <= 0:
        raise ValueError(f"Screenshot is empty: {image_path}")
    if size > MAX_SCREENSHOT_BYTES:
        raise ValueError(
            f"Screenshot too large ({size} bytes). Max: {MAX_SCREENSHOT_BYTES} bytes. "
            f"Consider compressing: {image_path}"
        )
    return base64.b64encode(image_path.read_bytes()).decode("utf-8")


def _is_excluded(path: Path) -> bool:
    """Check if path should be excluded."""
    return any(part in EXCLUDE_DIRS for part in path.parts)


def _collect_test_files(test_path: Path) -> Dict[str, str]:
    """Collect test files from path."""
    if not test_path.exists():
        raise FileNotFoundError(f"Test path not found: {test_path}")

    candidates: List[Path] = []
    
    if test_path.is_dir():
        root = test_path
        for p in root.rglob("*"):
            if _is_excluded(p):
                continue
            if p.is_file() and p.suffix.lower() in SUPPORTED_TEST_EXTS:
                candidates.append(p)
    else:
        if test_path.suffix.lower() not in SUPPORTED_TEST_EXTS:
            raise ValueError(f"Unsupported file type: {test_path}")
        root = test_path.parent
        candidates = [test_path]
        for ext in SUPPORTED_TEST_EXTS:
            for p in root.glob(f"*{ext}"):
                if p != test_path and not _is_excluded(p):
                    candidates.append(p)

    test_files: Dict[str, str] = {}
    for p in candidates[:MAX_FILES]:
        if not p.exists() or not p.is_file():
            continue
        try:
            key = str(p.relative_to(root))
        except ValueError:
            key = p.name
        if key in test_files:
            key = str(p)
        content = _read_text_file(p)
        if len(content) > MAX_CHARS_PER_FILE:
            content = content[:MAX_CHARS_PER_FILE] + "\n/* ...truncated... */\n"
        test_files[key] = content

    if not test_files:
        raise ValueError(f"No supported files found at: {test_path}")
    return test_files


def _validate_inputs(
    test_file_path: str,
    failure_info_path: str,
    dom_elements_path: str,
    screenshot_path: str,
) -> Tuple[Path, Path, Path, Path]:
    """Validate and normalize input paths."""
    test_path = _norm_path(test_file_path)
    failure_path = _norm_path(failure_info_path)
    dom_path = _norm_path(dom_elements_path)
    screenshot_path_obj = _norm_path(screenshot_path)

    missing = [str(p) for p in [test_path, failure_path, dom_path, screenshot_path_obj] if not p.exists()]
    if missing:
        raise FileNotFoundError(f"Missing file(s): {', '.join(missing)}")

    if test_path.is_file() and test_path.suffix.lower() not in SUPPORTED_TEST_EXTS:
        raise ValueError(f"Unsupported test file type: {test_path}")

    if screenshot_path_obj.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise ValueError(f"Unsupported image type: {screenshot_path_obj}")

    return test_path, failure_path, dom_path, screenshot_path_obj


def _analyze_impl(
    test_file_path: str,
    failure_info_path: str,
    dom_elements_path: str,
    screenshot_path: str,
    preset: str = "claude",
    model_variant: str = "claude-sonnet-4-20250514",
) -> str:
    """Execute test failure analysis."""
    if not MUUK_API_KEY:
        return json.dumps({
            "error": "MUUK_API_KEY not configured",
            "hint": "Set MUUK_API_KEY environment variable"
        }, indent=2)
    
    test_path, failure_path, dom_path, screenshot_path_obj = _validate_inputs(
        test_file_path, failure_info_path, dom_elements_path, screenshot_path
    )

    payload = {
        "config": {
            "preset": preset,
            "model_variant": model_variant,
            "temperature": 0.0,
        },
        "test_files": _collect_test_files(test_path),
        "failure_json": _read_json_file(failure_path),
        "dom_snapshot_json": _read_json_file(dom_path),
        "screenshot_base64": _encode_image_to_base64(screenshot_path_obj),
    }

    headers = {
        "Content-Type": "application/json",
        "x-api-key": MUUK_API_KEY,
    }

    try:
        r = requests.post(API_URL, json=payload, headers=headers, timeout=REQUEST_TIMEOUT_SECS)
    except requests.exceptions.Timeout:
        return json.dumps({"error": "Request timed out"}, indent=2)
    except requests.exceptions.RequestException as e:
        return json.dumps({"error": "Connection error", "details": str(e)}, indent=2)

    if r.status_code == 200:
        try:
            data = r.json()
            report = data.get("report", data)
            return report if isinstance(report, str) else json.dumps(report, indent=2)
        except Exception:
            return json.dumps({"error": "Invalid API response", "raw": r.text[:1000]}, indent=2)

    return json.dumps({
        "error": f"API error ({r.status_code})",
        "details": r.text[:2000],
    }, indent=2)


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools."""
    return [
        Tool(
            name="analyze_test_failure",
            description=(
                "Analyze an E2E test failure and get repair suggestions. "
                "Provide paths to test file, failure info JSON, DOM snapshot JSON, and screenshot."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "test_file_path": {
                        "type": "string",
                        "description": "Path to test file or directory (e.g., ./tests/login.spec.ts)",
                    },
                    "failure_info_path": {
                        "type": "string",
                        "description": "Path to failure info JSON file",
                    },
                    "dom_elements_path": {
                        "type": "string",
                        "description": "Path to DOM elements/snapshot JSON file",
                    },
                    "screenshot_path": {
                        "type": "string",
                        "description": "Path to failure screenshot (.png/.jpg)",
                    },
                    "preset": {
                        "type": "string",
                        "default": "claude",
                        "description": "AI preset: claude, openai, gemini, deepseek, mistral",
                    },
                    "model_variant": {
                        "type": "string",
                        "default": "claude-sonnet-4-20250514",
                        "description": "Model variant to use",
                    },
                },
                "required": ["test_file_path", "failure_info_path", "dom_elements_path", "screenshot_path"],
            },
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls."""
    if name != "analyze_test_failure":
        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

    required = ["test_file_path", "failure_info_path", "dom_elements_path", "screenshot_path"]
    missing = [k for k in required if not arguments.get(k)]
    if missing:
        return [TextContent(type="text", text=json.dumps({
            "error": "Missing required arguments",
            "missing": missing,
        }, indent=2))]

    try:
        result = await asyncio.to_thread(
            _analyze_impl,
            test_file_path=arguments["test_file_path"],
            failure_info_path=arguments["failure_info_path"],
            dom_elements_path=arguments["dom_elements_path"],
            screenshot_path=arguments["screenshot_path"],
            preset=arguments.get("preset", "claude"),
            model_variant=arguments.get("model_variant", "claude-sonnet-4-20250514"),
        )
    except Exception as e:
        result = json.dumps({"error": "Execution failed", "details": str(e)}, indent=2)

    return [TextContent(type="text", text=result)]


async def _main():
    """Async main entry point."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


def main():
    """Main entry point."""
    asyncio.run(_main())


if __name__ == "__main__":
    main()