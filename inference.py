"""
MediaOps-CRM-Env — Baseline Inference Script

Runs an LLM agent against all 3 tasks and emits structured logs
in the mandatory [START] / [STEP] / [END] format required by the hackathon.

Environment variables required:
    API_BASE_URL   — OpenAI-compatible API endpoint
    MODEL_NAME     — Model identifier (e.g. "gpt-4o-mini")
    HF_TOKEN       — Hugging Face token (also used as API key if OPENAI_API_KEY not set)
    OPENAI_API_KEY — (optional) override API key
    IMAGE_NAME     — Docker image name (optional; if set, spins up container)
    HF_SPACE_URL   — HF Space URL to connect to (optional fallback)
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

from openai import OpenAI

# ─── Config ───────────────────────────────────────────────────────────────────

API_BASE_URL: str = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME: str = os.environ.get("MODEL_NAME", "gpt-4o-mini")
API_KEY: str = os.environ.get("OPENAI_API_KEY") or os.environ.get("HF_TOKEN", "")
IMAGE_NAME: str = os.environ.get("IMAGE_NAME", "")
HF_SPACE_URL: str = os.environ.get("HF_SPACE_URL", "http://localhost:8000")

BENCHMARK = "mediaops-crm-env"
MAX_STEPS = 25          # per task
MAX_TOTAL_REWARD = 1.0  # grader always returns 0–1
SUCCESS_SCORE_THRESHOLD = 0.6

TASK_NAMES = {
    1: "email_triage",
    2: "video_delivery_pipeline",
    3: "sla_crisis_management",
}

# ─── Logging helpers (mandatory format) ───────────────────────────────────────

def log_start(*, task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(*, step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_str = f" error={error}" if error else ""
    print(
        f"[STEP] step={step} action={json.dumps(action)} reward={reward:.4f} done={done}{error_str}",
        flush=True,
    )


def log_end(*, success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = "[" + ", ".join(f"{r:.4f}" for r in rewards) + "]"
    print(
        f"[END] success={success} steps={steps} score={score:.4f} rewards={rewards_str}",
        flush=True,
    )


# ─── System prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert media agency operations manager AI agent.

You interact with the MediaOps-CRM environment via structured actions.
Each action is a JSON object with:
  - "action_type": one of [list_emails, read_email, triage_email, search_file,
                            check_storage, render_video, delete_logs, send_reply,
                            update_crm, escalate, mark_resolved]
  - "params": a dict of parameters for that action

RULES:
1. Always start by calling list_emails to see the inbox.
2. Read each email before triaging it.
3. For render_video: check_storage first; if storage > 75%, delete_logs first.
4. For Task 1 (triage): categories are [billing, technical, general],
   routes are [billing_queue, technical_queue, account_manager_queue, production_queue],
   priorities are [low, medium, high, urgent, critical].
5. For Task 2 (delivery): read_email → search_file → check_storage → (delete_logs if needed)
   → render_video → send_reply → update_crm with {"delivery_status": "delivered"}.
6. For Task 3 (crisis): escalate the 15-min SLA email FIRST, then handle others.
7. Always respond with ONLY a valid JSON object — no markdown, no prose.

Example response:
{"action_type": "list_emails", "params": {}}
"""


def build_user_message(
    step: int,
    observation: str,
    reward: float,
    history: List[str],
) -> str:
    hist = "\n".join(history[-6:]) if history else "No history yet."
    return (
        f"Step {step} | Last reward: {reward:+.4f}\n\n"
        f"=== OBSERVATION ===\n{observation}\n\n"
        f"=== RECENT HISTORY ===\n{hist}\n\n"
        "Respond with a JSON action object."
    )


def get_agent_action(
    client: OpenAI,
    step: int,
    observation: str,
    reward: float,
    history: List[str],
) -> Dict[str, Any]:
    """Call the LLM and parse its action. Falls back to list_emails on failure."""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": build_user_message(step, observation, reward, history)},
            ],
            temperature=0.2,
            max_tokens=256,
        )
        raw = response.choices[0].message.content.strip()
        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        action = json.loads(raw.strip())
        if "action_type" not in action:
            raise ValueError("Missing action_type")
        return action
    except Exception as exc:
        print(f"[DEBUG] LLM parse error at step {step}: {exc}", flush=True)
        return {"action_type": "list_emails", "params": {}}


# ─── Environment interaction ───────────────────────────────────────────────────

async def run_task(
    task_id: int,
    client: OpenAI,
    env_url: str,
) -> float:
    """Run one task and return the final score."""
    from client import MediaOpsCRMEnv
    from models import MediaOpsAction

    task_name = TASK_NAMES[task_id]
    rewards: List[float] = []
    history: List[str] = []
    steps_taken = 0
    score = 0.0
    success = False

    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)

    # Connect to environment
    if IMAGE_NAME:
        env = await MediaOpsCRMEnv.from_docker_image(IMAGE_NAME)
    else:
        env = MediaOpsCRMEnv(base_url=env_url)

    try:
        # Reset with task_id
        result = await env.reset(task_id=task_id)
        obs_msg = result.observation.message if hasattr(result, "observation") else str(result)
        last_reward = 0.0

        for step in range(1, MAX_STEPS + 1):
            done = getattr(result, "done", False)
            if done:
                break

            action_dict = get_agent_action(client, step, obs_msg, last_reward, history)
            action_str = json.dumps(action_dict)
            error_msg = None

            try:
                result = await env.step(
                    MediaOpsAction(
                        action_type=action_dict.get("action_type", "list_emails"),
                        params=action_dict.get("params", {}),
                    )
                )
                obs = result.observation
                obs_msg = obs.message
                reward = result.reward or 0.0
                done = result.done
            except Exception as exc:
                error_msg = str(exc)
                reward = -0.05
                done = False
                obs_msg = f"Error: {error_msg}"

            rewards.append(reward)
            last_reward = reward
            steps_taken = step

            log_step(step=step, action=action_str, reward=reward, done=done, error=error_msg)
            history.append(f"Step {step}: {action_str} → reward {reward:+.4f}")

            if done:
                break

        # Final score = last reward if episode-end was reached (grader score),
        # else sum-based normalisation
        if rewards:
            # The grader emits a terminal reward on done=True; pick that.
            score = rewards[-1] if steps_taken < MAX_STEPS else sum(rewards) / MAX_TOTAL_REWARD
            score = min(max(score, 0.0), 1.0)
        success = score >= SUCCESS_SCORE_THRESHOLD

    finally:
        try:
            await env.close()
        except Exception as exc:
            print(f"[DEBUG] env.close() error: {exc}", flush=True)
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

    return score


async def main() -> None:
    if not API_KEY:
        print("ERROR: Set OPENAI_API_KEY or HF_TOKEN", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    env_url = HF_SPACE_URL

    print(f"\n{'='*60}", flush=True)
    print(f" MediaOps-CRM-Env Baseline Inference", flush=True)
    print(f" Model : {MODEL_NAME}", flush=True)
    print(f" Server: {env_url}", flush=True)
    print(f"{'='*60}\n", flush=True)

    all_scores: Dict[int, float] = {}
    for task_id in [1, 2, 3]:
        print(f"\n--- Running Task {task_id}: {TASK_NAMES[task_id]} ---", flush=True)
        t0 = time.time()
        score = await run_task(task_id, client, env_url)
        elapsed = time.time() - t0
        all_scores[task_id] = score
        print(f"    Score: {score:.4f}  ({elapsed:.1f}s)\n", flush=True)

    avg = sum(all_scores.values()) / len(all_scores)
    print(f"\n{'='*60}", flush=True)
    print(f" FINAL RESULTS", flush=True)
    for tid, sc in all_scores.items():
        print(f"   Task {tid} ({TASK_NAMES[tid]}): {sc:.4f}", flush=True)
    print(f"   Average score: {avg:.4f}", flush=True)
    print(f"{'='*60}\n", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
