"""Track execution with fix loop."""

import base64
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import structlog

from inverseui.auth import AuthManager
from inverseui.backend import BackendClient
from inverseui.runner import PlaywrightRunner

log = structlog.get_logger(__name__)


async def ensure_resources(backend: "BackendClient", track_id: str) -> None:
    """Fetch and create resource files (e.g., resume.pdf) for a track."""
    try:
        result = await backend.get_track_resources(track_id)
        resources = result.get("resources", [])

        if not resources:
            return

        for resource in resources:
            resource_path = Path(resource.get("path", ""))
            if not resource_path:
                continue

            # Create parent directories
            resource_path.parent.mkdir(parents=True, exist_ok=True)

            # Create empty placeholder file if it doesn't exist
            if not resource_path.exists():
                resource_path.touch()
                log.info("created_resource", path=str(resource_path))

    except Exception as e:
        log.warning("fetch_resources_failed", track_id=track_id, error=str(e))


@dataclass
class RunResult:
    """Result of a single track execution."""

    success: bool
    track_id: str
    error: str | None = None
    result: dict[str, Any] | None = None


@dataclass
class FixResult:
    """Result of a fix loop execution."""

    success: bool
    track_id: str
    iterations: int
    fix_explanations: list[str] = field(default_factory=list)
    final_error: str | None = None
    result: dict[str, Any] | None = None


async def run_track(
    track_id: str,
    cdp_port: int | None = None,
    mode: str = "production",
) -> RunResult:
    """Execute a track once without fix loop.

    1. POST /generate/<track_id> → Get code
    2. Execute with Playwright
    3. Return result (no fix attempts)

    Args:
        track_id: The track ID to execute
        cdp_port: CDP port for browser connection (None = script launches own browser)
        mode: "debug" or "production"

    Returns:
        RunResult with execution details
    """
    auth = AuthManager()
    backend = BackendClient(auth_manager=auth)
    runner = PlaywrightRunner()

    # Check authentication
    if not auth.is_authenticated():
        raise RuntimeError("Not authenticated. Run: inverseui login")

    # Ensure resource files exist (e.g., resume.pdf)
    await ensure_resources(backend, track_id)

    # Get generated code
    log.info("fetching_code", track_id=track_id)

    try:
        generate_result = await backend.get_generated_code(track_id)
        code = generate_result.get("code")
        if not code:
            raise RuntimeError("No code returned from generate endpoint")
    except Exception as e:
        log.error("get_generated_code_failed", track_id=track_id, error=str(e))
        return RunResult(
            success=False,
            track_id=track_id,
            error=str(e),
        )

    # Execute the code
    log.info("executing_track", track_id=track_id, cdp_port=cdp_port, mode=mode)
    result = await runner.execute_code(code=code, cdp_port=cdp_port, mode=mode)

    if result.get("status") == "success":
        log.info("execution_success", track_id=track_id)
        return RunResult(
            success=True,
            track_id=track_id,
            result=result.get("result"),
        )

    # Execution failed
    error_info = result.get("error", {})
    error_message = error_info.get("message", "Unknown error")
    log.warning("execution_failed", track_id=track_id, error=error_message)

    return RunResult(
        success=False,
        track_id=track_id,
        error=error_message,
    )


async def run_fix_loop(
    track_id: str,
    max_retries: int = 5,
    cdp_port: int | None = None,
    mode: str = "production",
    on_progress: callable = None,
) -> FixResult:
    """Execute a track with automatic fix loop.

    1. POST /generate/<track_id> → Get initial code
    2. Execute with Playwright
    3. If fails, POST /generate/<track_id>/fix → Get fixed code
    4. Repeat until success or max_retries reached
    5. POST /generate/<track_id>/result → Report final result

    Args:
        track_id: The track ID to execute
        max_retries: Maximum number of fix attempts
        cdp_port: CDP port for browser connection (None = script launches own browser)
        mode: "debug" or "production"
        on_progress: Optional callback(iteration, max_retries, status, message)

    Returns:
        FixResult with execution details
    """
    auth = AuthManager()
    backend = BackendClient(auth_manager=auth)
    runner = PlaywrightRunner()

    fix_explanations = []
    iteration = 0
    last_error = None

    def progress(status: str, message: str = ""):
        if on_progress:
            on_progress(iteration, max_retries, status, message)

    # Check authentication
    if not auth.is_authenticated():
        raise RuntimeError("Not authenticated. Run: inverseui login")

    # Ensure resource files exist (e.g., resume.pdf)
    await ensure_resources(backend, track_id)

    # 1. Get initial generated code
    progress("fetching", "Getting generated code...")
    log.info("fetching_code", track_id=track_id)

    try:
        generate_result = await backend.get_generated_code(track_id)
        code = generate_result.get("code")
        if not code:
            raise RuntimeError("No code returned from generate endpoint")
    except Exception as e:
        log.error("get_generated_code_failed", track_id=track_id, error=str(e))
        return FixResult(
            success=False,
            track_id=track_id,
            iterations=0,
            final_error=str(e),
        )

    # 2. Execute and retry loop
    while iteration < max_retries:
        iteration += 1
        progress("executing", f"Attempt {iteration}/{max_retries}")
        log.info("executing_iteration", track_id=track_id, iteration=iteration)

        # Execute the code
        result = await runner.execute_code(code=code, cdp_port=cdp_port, mode=mode)

        if result.get("status") == "success":
            # Success!
            log.info("execution_success", track_id=track_id, iterations=iteration)
            progress("success", "Execution succeeded!")

            # Report success to backend
            try:
                await backend.report_track_result(
                    track_id=track_id,
                    success=True,
                    iterations=iteration,
                )
            except Exception as e:
                log.warning("report_result_failed", error=str(e))

            return FixResult(
                success=True,
                track_id=track_id,
                iterations=iteration,
                fix_explanations=fix_explanations,
                result=result.get("result"),
            )

        # Execution failed
        error_info = result.get("error", {})
        error_message = error_info.get("message", "Unknown error")
        error_trace = error_info.get("traceback", "")
        last_error = error_message

        log.warning(
            "execution_failed",
            track_id=track_id,
            iteration=iteration,
            error=error_message,
        )
        progress("failed", f"Failed: {error_message[:50]}...")

        # Check if we've exhausted retries
        if iteration >= max_retries:
            break

        # 3. Request fix from backend
        progress("fixing", "Requesting fix from backend...")
        log.info("requesting_fix", track_id=track_id, iteration=iteration)

        # Read screenshot if available
        screenshot_base64 = None
        artifacts = result.get("artifacts", {})
        screenshot_path = artifacts.get("screenshot")
        if screenshot_path:
            try:
                with open(screenshot_path, "rb") as f:
                    screenshot_base64 = base64.b64encode(f.read()).decode("utf-8")
            except Exception as e:
                log.warning("screenshot_read_failed", error=str(e))

        try:
            fix_result = await backend.request_fix(
                track_id=track_id,
                error_message=error_message,
                error_trace=error_trace,
                previous_code=code,
                iteration=iteration,
                screenshot_base64=screenshot_base64,
            )

            if not fix_result.get("success"):
                log.error("fix_request_failed", track_id=track_id)
                last_error = "Backend could not generate a fix"
                break

            # Update code for next iteration
            code = fix_result.get("code")
            if not code:
                log.error("fix_returned_no_code", track_id=track_id)
                last_error = "Fix response contained no code"
                break

            fix_explanation = fix_result.get("fix_explanation", "")
            if fix_explanation:
                fix_explanations.append(fix_explanation)
                log.info("fix_applied", explanation=fix_explanation)
                progress("fix_applied", fix_explanation[:50])

        except Exception as e:
            log.error("request_fix_failed", track_id=track_id, error=str(e))
            last_error = f"Fix request failed: {e}"
            break

    # All retries exhausted
    log.warning("execution_exhausted", track_id=track_id, iterations=iteration)
    progress("exhausted", f"Failed after {iteration} attempts")

    # Report failure to backend
    try:
        await backend.report_track_result(
            track_id=track_id,
            success=False,
            iterations=iteration,
            final_error=last_error,
        )
    except Exception as e:
        log.warning("report_result_failed", error=str(e))

    return FixResult(
        success=False,
        track_id=track_id,
        iterations=iteration,
        fix_explanations=fix_explanations,
        final_error=last_error,
    )
