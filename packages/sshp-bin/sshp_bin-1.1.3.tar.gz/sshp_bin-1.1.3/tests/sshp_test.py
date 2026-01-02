# flake8: noqa: S603
from __future__ import annotations

import logging
import re
import subprocess
import sys
from importlib.metadata import version
from pathlib import Path

logger = logging.getLogger(__name__)


def test_help() -> None:
    sshp_bin = Path(sys.executable).parent / "sshp"
    assert sshp_bin.exists(), f"sshp binary not found at {sshp_bin}"
    result = subprocess.run([sshp_bin, "--help"], check=False, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error(result.stderr)
        msg = f"Error running {sshp_bin} --help"
        raise AssertionError(msg)
    assert "Parallel SSH Executor" in result.stdout

    with open("./sshp/src/sshp.c") as f:
        source_code = f.read()
    version_match = re.search(r'#define\s+PROG_VERSION\s+"([^"]+)"', source_code)
    assert version_match is not None, "Version string not found in source code"
    current_version = "v" + version("sshp-bin")
    assert version_match.group(1) == current_version, (
        "Version mismatch between binary and source code"
    )

    using_tool = re.search(r"\(using (\w+)\)", result.stdout)
    assert using_tool is not None, "Could not determine underlying tool from help output"
    assert using_tool.group(1) in ("epoll", "kqueue"), "Unexpected underlying tool"

    if sys.platform == "darwin":
        expected_tool = "kqueue"
    else:
        expected_tool = "epoll"

    assert using_tool.group(1) == expected_tool, (
        f"Expected underlying tool to be {expected_tool} on {sys.platform}"
    )
