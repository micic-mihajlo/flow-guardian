"""Local state persistence between CLI invocations."""
import json
from pathlib import Path
from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class FlowConfig(BaseModel):
    personal_assistant_id: str
    personal_thread_id: str
    team_assistant_id: Optional[str] = None
    team_thread_id: Optional[str] = None
    username: str


class LastCapture(BaseModel):
    timestamp: str
    branch: str
    files: list[str]
    summary: str
    git_head: str


def get_flow_dir() -> Path:
    """Get or create .flowguardian directory in project root."""
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (parent / ".git").exists():
            flow_dir = parent / ".flowguardian"
            flow_dir.mkdir(exist_ok=True)
            return flow_dir
    flow_dir = cwd / ".flowguardian"
    flow_dir.mkdir(exist_ok=True)
    return flow_dir


def load_config() -> Optional[FlowConfig]:
    config_path = get_flow_dir() / "config.json"
    if config_path.exists():
        return FlowConfig.model_validate_json(config_path.read_text())
    return None


def save_config(config: FlowConfig):
    config_path = get_flow_dir() / "config.json"
    config_path.write_text(config.model_dump_json(indent=2))


def load_last_capture() -> Optional[LastCapture]:
    capture_path = get_flow_dir() / "last_capture.json"
    if capture_path.exists():
        return LastCapture.model_validate_json(capture_path.read_text())
    return None


def save_last_capture(capture: LastCapture):
    capture_path = get_flow_dir() / "last_capture.json"
    capture_path.write_text(capture.model_dump_json(indent=2))
