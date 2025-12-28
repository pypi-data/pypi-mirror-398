"""Playwright runner using pure Python."""

import asyncio
import json
import os
import signal
import socket
import subprocess
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import click
import structlog
from playwright.async_api import async_playwright

from inverseui.config import get_config, paths

log = structlog.get_logger(__name__)


def list_chrome_profiles() -> list[dict]:
    """List available Chrome profiles with their names and emails."""
    source_data_dir = get_chrome_user_data_dir()
    local_state_file = source_data_dir / "Local State"

    if not local_state_file.exists():
        return []

    try:
        with open(local_state_file, "r") as f:
            local_state = json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

    profiles_info = local_state.get("profile", {}).get("info_cache", {})
    profiles = []

    for profile_dir, info in profiles_info.items():
        name = info.get("name", profile_dir)
        email = info.get("user_name", "")
        gaia_name = info.get("gaia_name", "")

        # Use gaia_name (Google account name) if available, otherwise profile name
        display_name = gaia_name or name

        profiles.append({
            "dir": profile_dir,
            "name": display_name,
            "email": email,
        })

    return profiles


def prompt_profile_selection(profiles: list[dict]) -> str:
    """Prompt user to select a Chrome profile. Returns profile directory name."""
    click.echo("\nAvailable Chrome profiles:")
    click.echo("-" * 40)

    for i, profile in enumerate(profiles, 1):
        if profile["email"]:
            click.echo(f"  {i}. {profile['name']} ({profile['email']})")
        else:
            click.echo(f"  {i}. {profile['name']}")

    click.echo()

    while True:
        try:
            choice = click.prompt("Select profile", type=int, default=1)
            if 1 <= choice <= len(profiles):
                selected = profiles[choice - 1]
                click.echo(f"\nSelected: {selected['name']}")
                return selected["dir"]
            click.echo(f"Please enter a number between 1 and {len(profiles)}")
        except (ValueError, click.Abort):
            # Default to first profile
            return profiles[0]["dir"]


def find_free_port() -> int:
    """Find a free port using OS allocation (bind to port 0)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port


def wait_for_cdp_ready(port: int, timeout: float = 10.0) -> bool:
    """Wait for Chrome CDP to be ready on the given port."""
    import time
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.connect(("127.0.0.1", port))
                return True
        except (ConnectionRefusedError, socket.timeout, OSError):
            time.sleep(0.5)
    return False


def find_chrome_path() -> str:
    """Find Chrome executable path on the system."""
    if os.name == "nt":  # Windows
        possible_paths = [
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        ]
    elif os.uname().sysname == "Darwin":  # macOS
        possible_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        ]
    else:  # Linux
        possible_paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
        ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    raise RuntimeError("Chrome not found. Please install Google Chrome.")


def get_chrome_user_data_dir() -> Path:
    """Get the default Chrome user data directory."""
    if os.name == "nt":  # Windows
        return Path(os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data"))
    elif os.uname().sysname == "Darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "Google" / "Chrome"
    else:  # Linux
        return Path.home() / ".config" / "google-chrome"


def is_first_run() -> bool:
    """Check if this is the first run (no profile copied yet)."""
    inverseui_data_dir = paths.base / "chrome-data"
    if not inverseui_data_dir.exists():
        return True
    # Check if there's at least one profile
    return not ((inverseui_data_dir / "Default").exists() or any(inverseui_data_dir.glob("Profile *")))


def get_selected_profile() -> str | None:
    """Get the previously selected profile directory name."""
    profile_file = paths.base / "selected_profile"
    if profile_file.exists():
        return profile_file.read_text().strip()
    return None


def save_selected_profile(profile_dir: str) -> None:
    """Save the selected profile directory name."""
    profile_file = paths.base / "selected_profile"
    profile_file.parent.mkdir(parents=True, exist_ok=True)
    profile_file.write_text(profile_dir)


def ensure_profile_copied() -> tuple[Path, str]:
    """Ensure Chrome profile is copied on first run.

    Returns tuple of (user-data-dir path, profile directory name).
    """
    import shutil

    inverseui_data_dir = paths.base / "chrome-data"

    # Check if already copied
    if not is_first_run():
        selected = get_selected_profile() or "Default"
        log.info("profile_exists", path=str(inverseui_data_dir), profile=selected)
        return inverseui_data_dir, selected

    # First run - need to select and copy profile
    source_data_dir = get_chrome_user_data_dir()
    if not source_data_dir.exists():
        log.warning("chrome_data_not_found", path=str(source_data_dir))
        inverseui_data_dir.mkdir(parents=True, exist_ok=True)
        return inverseui_data_dir, "Default"

    # List available profiles and let user choose
    profiles = list_chrome_profiles()
    if not profiles:
        # No profiles found, use Default
        selected_profile = "Default"
    elif len(profiles) == 1:
        # Only one profile, use it automatically
        selected_profile = profiles[0]["dir"]
        click.echo(f"\nUsing profile: {profiles[0]['name']} ({profiles[0]['email']})")
    else:
        # Multiple profiles, let user choose
        selected_profile = prompt_profile_selection(profiles)

    log.info("copying_chrome_profile", source=str(source_data_dir), dest=str(inverseui_data_dir), profile=selected_profile)
    click.echo(f"Copying Chrome profile (first run)...")

    # Create destination directory
    inverseui_data_dir.mkdir(parents=True, exist_ok=True)

    # Copy only the selected profile and Local State
    items_to_copy = [selected_profile, "Local State"]

    for item_name in items_to_copy:
        source_item = source_data_dir / item_name
        dest_item = inverseui_data_dir / item_name

        if not source_item.exists():
            continue

        if source_item.is_dir():
            shutil.copytree(
                source_item,
                dest_item,
                ignore=shutil.ignore_patterns(
                    "Cache", "Code Cache", "GPUCache", "Service Worker",
                    "CacheStorage", "*.log", "*.tmp"
                ),
                dirs_exist_ok=True,
            )
        else:
            shutil.copy2(source_item, dest_item)

    # Save the selected profile for future runs
    save_selected_profile(selected_profile)

    log.info("profile_copied", path=str(inverseui_data_dir), profile=selected_profile)
    click.echo("Profile copied successfully.\n")
    return inverseui_data_dir, selected_profile


def ensure_extension() -> Path:
    """Ensure extension is downloaded from GitHub."""
    config = get_config()
    extension_dir = paths.extension_dir

    if extension_dir.exists() and (extension_dir / "manifest.json").exists():
        # Extension exists, try to update it
        log.info("updating_extension", path=str(extension_dir))
        try:
            subprocess.run(
                ["git", "-C", str(extension_dir), "pull", "--ff-only"],
                capture_output=True,
                check=False,
            )
        except Exception as e:
            log.warning("extension_update_failed", error=str(e))
        return extension_dir

    # Clone the extension
    log.info("cloning_extension", repo=config.extension_repo)
    extension_dir.parent.mkdir(parents=True, exist_ok=True)

    if extension_dir.exists():
        import shutil
        shutil.rmtree(extension_dir)

    result = subprocess.run(
        ["git", "clone", config.extension_repo, str(extension_dir)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to clone extension: {result.stderr}")

    log.info("extension_cloned", path=str(extension_dir))
    return extension_dir


def launch_chrome_with_extension(
    headless: bool = False,
    cdp_port: int | None = None,
) -> subprocess.Popen:
    """Launch Chrome with debugging and extension loaded.

    On first run, copies the user's Chrome profile to preserve login sessions.
    """
    config = get_config()
    cdp_port = cdp_port or config.cdp_port

    # Ensure extension is available
    extension_path = ensure_extension()

    # Find Chrome
    chrome_path = find_chrome_path()

    # Ensure profile is copied (first run copies user's Chrome profile)
    user_data_dir, profile_dir = ensure_profile_copied()

    # Build Chrome args
    args = [
        chrome_path,
        f"--remote-debugging-port={cdp_port}",
        f"--user-data-dir={user_data_dir}",
        f"--profile-directory={profile_dir}",
        f"--load-extension={extension_path}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-background-networking",
        "--disable-client-side-phishing-detection",
        "--disable-default-apps",
        "--disable-hang-monitor",
        "--disable-popup-blocking",
        "--disable-prompt-on-repost",
        "--disable-sync",
        "--disable-translate",
        "--metrics-recording-only",
        "--safebrowsing-disable-auto-update",
    ]

    if headless:
        args.append("--headless=new")

    log.info("launching_chrome", port=cdp_port, extension=str(extension_path))

    # Launch Chrome
    proc = subprocess.Popen(
        args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )

    # Save PID and port
    with open(paths.chrome_pid_file, "w") as f:
        f.write(str(proc.pid))
    with open(paths.chrome_port_file, "w") as f:
        f.write(str(cdp_port))

    return proc


def stop_chrome() -> bool:
    """Stop the Chrome process launched by InverseUI."""
    if not paths.chrome_pid_file.exists():
        return False

    try:
        with open(paths.chrome_pid_file) as f:
            pid = int(f.read().strip())

        os.kill(pid, signal.SIGTERM)
        paths.chrome_pid_file.unlink()
        if paths.chrome_port_file.exists():
            paths.chrome_port_file.unlink()
        log.info("chrome_stopped", pid=pid)
        return True
    except (ProcessLookupError, ValueError):
        # Process already dead
        if paths.chrome_pid_file.exists():
            paths.chrome_pid_file.unlink()
        if paths.chrome_port_file.exists():
            paths.chrome_port_file.unlink()
        return False


def get_chrome_port() -> int | None:
    """Get the CDP port of the running Chrome instance."""
    if not paths.chrome_port_file.exists():
        return None
    try:
        with open(paths.chrome_port_file) as f:
            return int(f.read().strip())
    except (ValueError, FileNotFoundError):
        return None


def is_chrome_running() -> bool:
    """Check if Chrome launched by InverseUI is running."""
    if not paths.chrome_pid_file.exists():
        return False

    try:
        with open(paths.chrome_pid_file) as f:
            pid = int(f.read().strip())

        os.kill(pid, 0)  # Check if process exists
        return True
    except (ProcessLookupError, ValueError, PermissionError):
        return False

# Default profile name (single profile for MVP)
DEFAULT_PROFILE = "default"


class PlaywrightRunner:
    """Manages Playwright execution with persistent profiles."""

    def __init__(self):
        self._profile_dir = paths.profile_dir(DEFAULT_PROFILE)
        self._config = get_config()

    def _create_run_dir(self) -> Path:
        """Create a new run directory for artifacts."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        run_id = str(uuid4())[:8]
        run_dir = paths.runs_dir / f"{timestamp}_{run_id}"
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    async def execute_code(
        self,
        code: str,
        cdp_port: int | None = None,
        mode: str = "production",
    ) -> dict[str, Any]:
        """Execute Python Playwright script as a subprocess.

        Args:
            code: Python code to execute
            cdp_port: CDP port to pass to script (None = script launches its own browser)
            mode: "debug" or "production" (affects timeouts in script)
        """
        run_id = str(uuid4())
        run_dir = self._create_run_dir()

        log.info(
            "executing_code",
            run_id=run_id,
            run_dir=str(run_dir),
            cdp_port=cdp_port,
            mode=mode,
        )

        # Write code to temp file
        script_path = run_dir / "script.py"
        with open(script_path, "w") as f:
            f.write(code)

        # Build command with arguments
        cmd = ["python", str(script_path)]
        if cdp_port:
            cmd.extend(["--port", str(cdp_port)])
        cmd.extend(["--mode", mode])

        # Run script as subprocess (use user's cwd for relative paths like resources/resume.pdf)
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            # Save output
            output_path = run_dir / "output.log"
            with open(output_path, "w") as f:
                f.write(f"=== STDOUT ===\n{result.stdout}\n")
                f.write(f"=== STDERR ===\n{result.stderr}\n")
                f.write(f"=== EXIT CODE: {result.returncode} ===\n")

            # Check for errors in output (script might catch exceptions but still fail)
            output_text = result.stdout + result.stderr
            has_error = any(pattern in output_text for pattern in [
                "Error", "Exception", "Timeout", "Traceback", "Failed"
            ])

            if result.returncode == 0 and not has_error:
                log.info("execution_success", run_id=run_id)
                return {
                    "status": "success",
                    "run_id": run_id,
                    "result": {"message": result.stdout or "Script executed"},
                    "artifacts": {
                        "script": str(script_path),
                        "output": str(output_path),
                    },
                }

            # Script failed or has error in output
            error_msg = result.stderr or result.stdout or f"Script exited with code {result.returncode}"
            log.warning("execution_failed", run_id=run_id, output=output_text[:500])
            return {
                "status": "error",
                "run_id": run_id,
                "error": {
                    "type": "execution_error",
                    "message": error_msg,
                    "traceback": output_text,
                },
                "artifacts": {
                    "script": str(script_path),
                    "output": str(output_path),
                },
            }

        except subprocess.TimeoutExpired:
            log.error("execution_timeout", run_id=run_id)
            return {
                "status": "error",
                "run_id": run_id,
                "error": {
                    "type": "timeout",
                    "message": "Script timed out after 5 minutes",
                },
            }
        except Exception as e:
            log.exception("execution_error", run_id=run_id)
            return {
                "status": "error",
                "run_id": run_id,
                "error": {
                    "type": "execution_error",
                    "message": str(e),
                    "traceback": traceback.format_exc(),
                },
            }

    async def open_profile_browser(self) -> None:
        """Open a browser for manual login (saves session to default profile)."""
        self._profile_dir.mkdir(parents=True, exist_ok=True)

        log.info("opening_profile_browser", profile=str(self._profile_dir))

        async with async_playwright() as p:
            context = await p.chromium.launch_persistent_context(
                user_data_dir=str(self._profile_dir),
                headless=False,
                channel="chrome",
                args=["--disable-blink-features=AutomationControlled"],
            )

            if not context.pages:
                await context.new_page()

            log.info("profile_browser_opened")

            # Wait for user to close the browser
            try:
                await context.wait_for_event("close", timeout=0)
            except Exception:
                pass

            log.info("profile_browser_closed")
