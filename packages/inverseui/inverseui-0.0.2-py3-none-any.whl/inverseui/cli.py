"""CLI entry point for InverseUI Runtime."""

import asyncio
import sys

import click
import structlog

from inverseui import __version__
from inverseui.auth import AuthManager
from inverseui.runner import (
    find_free_port,
    get_chrome_port,
    is_chrome_running,
    launch_chrome_with_extension,
    stop_chrome,
    wait_for_cdp_ready,
)

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ]
)
log = structlog.get_logger()


@click.group()
@click.version_option(version=__version__)
def main():
    """InverseUI Runtime - Local Agent Execution Environment."""
    pass


# ============== AUTH COMMANDS ==============


@main.command("login")
def login():
    """Login to InverseUI via browser."""
    auth = AuthManager()

    try:
        result = asyncio.run(auth.login())
        click.echo(f"\nLogged in as: {result.get('user', 'unknown')}")
    except KeyboardInterrupt:
        click.echo("\n\nLogin cancelled.")
        sys.exit(0)
    except EOFError:
        click.echo("\n\nLogin cancelled.")
        sys.exit(0)
    except RuntimeError as e:
        click.echo(f"\nLogin failed: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"\nLogin failed: {e}", err=True)
        sys.exit(1)


@main.command("logout")
def logout():
    """Logout from InverseUI."""
    auth = AuthManager()
    auth.logout()
    click.echo("Logged out.")


# ============== CHROME HELPER ==============


def _ensure_chrome_running() -> int:
    """Ensure Chrome is running with InverseUI profile, return CDP port."""
    if is_chrome_running():
        port = get_chrome_port()
        if port and wait_for_cdp_ready(port, timeout=2):
            return port
        # Chrome running but CDP not ready, stop and restart
        stop_chrome()

    # Launch Chrome with auto-assigned port
    port = find_free_port()
    proc = launch_chrome_with_extension(headless=False, cdp_port=port)

    # Wait for CDP to be ready
    if not wait_for_cdp_ready(port, timeout=15):
        proc.kill()
        raise RuntimeError("Chrome CDP failed to start (timeout)")

    if proc.poll() is not None:
        raise RuntimeError("Chrome failed to start")
    return port


# ============== FIX COMMAND (core functionality) ==============


@main.command("fix")
@click.argument("track_id")
@click.option("--max-retries", "-r", default=5, help="Max fix attempts")
@click.option("--production", is_flag=True, help="Use production mode (longer timeouts)")
def fix(track_id: str, max_retries: int, production: bool):
    """Fix and validate a track locally.

    Fetches generated code, executes it, and automatically requests fixes
    from the backend if execution fails. Repeats until success or max retries.
    Automatically launches Chrome with InverseUI profile.

    Example: inverseui fix track-abc123
    """
    from inverseui.executor import run_fix_loop

    mode = "production" if production else "debug"

    # Auto-launch Chrome
    try:
        port = _ensure_chrome_running()
        click.echo(f"Chrome ready (port {port})")
    except Exception as e:
        click.echo(f"Failed to launch Chrome: {e}", err=True)
        sys.exit(1)

    click.echo(f"Track: {track_id}")
    click.echo(f"Max retries: {max_retries}")
    click.echo(f"Mode: {mode}")
    click.echo()

    def on_progress(iteration: int, max_iter: int, status: str, message: str):
        """Progress callback for CLI output."""
        if status == "fetching":
            click.echo("Fetching generated code...")
        elif status == "executing":
            click.echo(f"Executing (attempt {iteration}/{max_iter})...")
        elif status == "failed":
            click.echo(f"  Failed: {message}")
        elif status == "fixing":
            click.echo("  Requesting fix from backend...")
        elif status == "fix_applied":
            click.echo(f"  Fix: {message}")
        elif status == "success":
            click.echo(f"Success!")
        elif status == "exhausted":
            click.echo(f"Failed after {iteration} attempts")

    try:
        result = asyncio.run(run_fix_loop(
            track_id=track_id,
            max_retries=max_retries,
            cdp_port=port,
            mode=mode,
            on_progress=on_progress,
        ))

        click.echo()

        if result.success:
            click.echo(f"Completed in {result.iterations} iteration(s)")
            if result.fix_explanations:
                click.echo("\nFixes applied:")
                for i, explanation in enumerate(result.fix_explanations, 1):
                    click.echo(f"  {i}. {explanation}")
        else:
            click.echo(f"Failed after {result.iterations} iteration(s)", err=True)
            if result.final_error:
                click.echo(f"Error: {result.final_error}", err=True)
            sys.exit(1)

    except RuntimeError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n\nCancelled.")
        sys.exit(0)


# ============== RUN COMMAND (single execution) ==============


@main.command("run")
@click.argument("track_id")
@click.option("--production", is_flag=True, help="Use production mode (longer timeouts)")
def run(track_id: str, production: bool):
    """Run a track once without fix loop.

    Fetches generated code and executes it. Does not attempt fixes on failure.
    Automatically launches Chrome with InverseUI profile.

    Example: inverseui run track-abc123
    """
    from inverseui.executor import run_track

    mode = "production" if production else "debug"

    # Auto-launch Chrome
    try:
        port = _ensure_chrome_running()
        click.echo(f"Chrome ready (port {port})")
    except Exception as e:
        click.echo(f"Failed to launch Chrome: {e}", err=True)
        sys.exit(1)

    click.echo(f"Track: {track_id}")
    click.echo(f"Mode: {mode}")
    click.echo()

    click.echo("Fetching generated code...")

    try:
        result = asyncio.run(run_track(
            track_id=track_id,
            cdp_port=port,
            mode=mode,
        ))

        if result.success:
            click.echo("Success!")
        else:
            click.echo(f"Failed: {result.error}", err=True)
            sys.exit(1)

    except RuntimeError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n\nCancelled.")
        sys.exit(0)


if __name__ == "__main__":
    main()
