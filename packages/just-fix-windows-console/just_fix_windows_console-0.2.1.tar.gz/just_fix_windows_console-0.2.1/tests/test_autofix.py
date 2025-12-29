import json
import subprocess
import sys
import pytest

pytestmark = pytest.mark.skipif(
    sys.platform != "win32",
    reason="Windows-only startup hook (.pth) test",
)


def _run_python(code: str) -> str:
    """
    Run a fresh Python interpreter and return stdout.
    """
    proc = subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        capture_output=True,
        text=True,
    )
    return proc.stdout.strip()


def test_pth_autorun_imports_package_on_startup():
    """
    The .pth file should cause `just_fix_windows_console` to be imported
    at interpreter startup, without any explicit import by user code.
    """
    out = _run_python(
        r"""
import sys, json
print(json.dumps({
    "imported": "just_fix_windows_console" in sys.modules
}))
"""
    )
    data = json.loads(out)
    assert data["imported"] is True, (
        "Expected just_fix_windows_console to be imported via .pth at startup"
    )


def test_vt_status_exists_on_startup():
    """
    Importing the package (via .pth) should create VT_STATUS in the module.
    Do NOT assert its value, as stdout/stderr may not be real consoles in CI.
    """
    out = _run_python(
        r"""
import json, just_fix_windows_console
print(json.dumps({
    "has_vt_status": hasattr(just_fix_windows_console, "VT_STATUS"),
    "keys": sorted(just_fix_windows_console.VT_STATUS.keys())
}))
"""
    )
    data = json.loads(out)
    assert data["has_vt_status"] is True
    assert data["keys"] == ["stderr", "stdout"]


def test_no_site_disables_pth():
    """
    When Python is started with -S, the site module is not imported,
    so .pth files are not processed.
    """
    proc = subprocess.run(
        [
            sys.executable,
            "-S",
            "-c",
            r'import sys; print("just_fix_windows_console" in sys.modules)',
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert proc.stdout.strip() == "False"
