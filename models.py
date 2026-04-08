"""
MediaOps-CRM-Env — Typed Models
Action, Observation using OpenEnv base classes (Pydantic).
"""
from typing import Any, Dict, List, Optional

from openenv.core.env_server.types import Action, Observation
from pydantic import Field


class MediaOpsAction(Action):
    """
    Action submitted by the agent each step.

    action_type: one of:
        list_emails     — show inbox summary
        read_email      — read email by id (params: email_id)
        triage_email    — classify + route (params: email_id, category, route, priority)
        search_file     — search files (params: filename or client_id)
        check_storage   — report storage stats
        render_video    — process a file (params: file_id or file_name)
        delete_logs     — free storage (params: log_id or delete_all=true)
        send_reply      — email client (params: email_id, message)
        update_crm      — update CRM record (params: client_id, updates={})
        escalate        — escalate to human (params: email_id, reason)
        mark_resolved   — close email (params: email_id)

    params: action-specific key/value pairs.
    """

    action_type: str = Field(..., description="Action to perform")
    params: Dict[str, Any] = Field(default_factory=dict, description="Action parameters")


class MediaOpsObservation(Observation):
    """
    Observation returned after every step.
    `done` and `reward` are inherited from Observation base.
    """

    message: str = Field(default="", description="Human-readable result of last action")
    inbox: List[Dict[str, Any]] = Field(default_factory=list, description="Email inbox summary")
    current_email: Optional[Dict[str, Any]] = Field(default=None, description="Full email just read")
    current_file: Optional[Dict[str, Any]] = Field(default=None, description="File found by search")
    storage_used_gb: float = Field(default=0.0, description="Storage used (GB)")
    storage_limit_gb: float = Field(default=10.0, description="Storage limit (GB)")
    crm_snapshot: List[Dict[str, Any]] = Field(default_factory=list, description="CRM client overview")
    available_actions: List[str] = Field(default_factory=list, description="Valid action_type values")
    task_progress: Dict[str, Any] = Field(default_factory=dict, description="Task completion metrics")
    reward_breakdown: Dict[str, float] = Field(default_factory=dict, description="Per-component rewards")
