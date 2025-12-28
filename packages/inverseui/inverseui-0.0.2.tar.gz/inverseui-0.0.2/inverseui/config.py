"""Configuration management for InverseUI Runtime."""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class Config(BaseModel):
    """Runtime configuration."""

    api_base_url: str = "https://api.inverseui.com"
    web_base_url: str = "https://inverseui.com"
    callback_port: int = 17321
    poll_interval_seconds: int = 5
    max_retry_attempts: int = 3

    # Chrome/CDP settings
    cdp_port: int = 9222
    extension_repo: str = "https://github.com/InverseUI/InverseUI-Recorder.git"


class Paths:
    """Standard paths for InverseUI runtime data."""

    def __init__(self, base_dir: Path | None = None):
        self.base = base_dir or Path.home() / ".inverseui"

    @property
    def daemon_socket(self) -> Path:
        return self.base / "daemon.sock"

    @property
    def daemon_pid(self) -> Path:
        return self.base / "daemon.pid"

    @property
    def config_file(self) -> Path:
        return self.base / "config.json"

    @property
    def profiles_dir(self) -> Path:
        return self.base / "profiles"

    @property
    def workflows_dir(self) -> Path:
        return self.base / "workflows"

    @property
    def runs_dir(self) -> Path:
        return self.base / "runs"

    @property
    def logs_dir(self) -> Path:
        return self.base / "logs"

    @property
    def daemon_log(self) -> Path:
        return self.logs_dir / "daemon.log"

    @property
    def extension_dir(self) -> Path:
        return self.base / "extension"

    @property
    def chrome_pid_file(self) -> Path:
        return self.base / "chrome.pid"

    @property
    def chrome_port_file(self) -> Path:
        return self.base / "chrome.port"

    def profile_dir(self, agent_id: str) -> Path:
        return self.profiles_dir / agent_id

    def workflow_dir(self, agent_id: str) -> Path:
        return self.workflows_dir / agent_id

    def ensure_dirs(self) -> None:
        """Create all necessary directories."""
        self.base.mkdir(parents=True, exist_ok=True)
        self.profiles_dir.mkdir(exist_ok=True)
        self.workflows_dir.mkdir(exist_ok=True)
        self.runs_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)


# Global paths instance
paths = Paths()


def load_config() -> Config:
    """Load configuration from file or return defaults."""
    config_file = paths.config_file
    if config_file.exists():
        with open(config_file) as f:
            data = json.load(f)
        return Config(**data)
    return Config()


def save_config(config: Config) -> None:
    """Save configuration to file."""
    paths.ensure_dirs()
    with open(paths.config_file, "w") as f:
        json.dump(config.model_dump(), f, indent=2)


def get_config() -> Config:
    """Get current configuration (cached)."""
    return load_config()
