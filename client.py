"""MediaOps-CRM-Env Client."""
from typing import Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

from .models import MediaOpsAction, MediaOpsObservation


class MediaOpsCRMEnv(EnvClient[MediaOpsAction, MediaOpsObservation, State]):
    """
    Async WebSocket client for MediaOps-CRM-Env.

    Usage (sync context manager):
        with MediaOpsCRMEnv(base_url="http://localhost:8000") as env:
            result = env.reset(task_id=1)
            result = env.step(MediaOpsAction(action_type="list_emails"))

    Usage (async, from inference script):
        env = await MediaOpsCRMEnv.from_docker_image("mediaops-crm-env:latest")
        result = await env.reset()
        result = await env.step(MediaOpsAction(action_type="list_emails", params={}))
    """

    def _step_payload(self, action: MediaOpsAction) -> Dict:
        return {
            "action_type": action.action_type,
            "params": action.params,
        }

    def _parse_result(self, payload: Dict) -> StepResult[MediaOpsObservation]:
        obs_data = payload.get("observation", {})
        observation = MediaOpsObservation(
            done=payload.get("done", False),
            reward=payload.get("reward"),
            message=obs_data.get("message", ""),
            inbox=obs_data.get("inbox", []),
            current_email=obs_data.get("current_email"),
            current_file=obs_data.get("current_file"),
            storage_used_gb=obs_data.get("storage_used_gb", 0.0),
            storage_limit_gb=obs_data.get("storage_limit_gb", 10.0),
            crm_snapshot=obs_data.get("crm_snapshot", []),
            available_actions=obs_data.get("available_actions", []),
            task_progress=obs_data.get("task_progress", {}),
            reward_breakdown=obs_data.get("reward_breakdown", {}),
        )
        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )
