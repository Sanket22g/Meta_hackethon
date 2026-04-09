"""
MediaOps-CRM-Env — Core Environment Logic

Three tasks of increasing difficulty:
  Task 1 (easy)   — Email Triage & Classification
  Task 2 (medium) — Video Delivery Pipeline
  Task 3 (hard)   — Multi-Client SLA Crisis Management
"""

import uuid
from typing import Any, Dict, List, Optional, Tuple

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import MediaOpsAction, MediaOpsObservation
except ImportError:
    from models import MediaOpsAction, MediaOpsObservation


# ─── Constants ────────────────────────────────────────────────────────────────

TASK_CONFIGS: Dict[int, Dict] = {
    1: {
        "name": "email_triage",
        "display_name": "Email Triage & Classification (Easy)",
        "max_steps": 25,
        "description": (
            "Classify and route 5 client emails to the correct department. "
            "Use: list_emails → read_email → triage_email for each email."
        ),
    },
    2: {
        "name": "video_delivery_pipeline",
        "display_name": "Video Delivery Pipeline (Medium)",
        "max_steps": 20,
        "description": (
            "Process a client video delivery request end-to-end. "
            "read_email → search_file → check_storage → render_video → send_reply → update_crm."
        ),
    },
    3: {
        "name": "sla_crisis_management",
        "display_name": "Multi-Client SLA Crisis (Hard)",
        "max_steps": 35,
        "description": (
            "Handle 3 overlapping client crises with storage pressure and SLA deadlines. "
            "Triage urgency, free storage, escalate critical cases, deliver files."
        ),
    },
}

AVAILABLE_ACTIONS: List[str] = [
    "list_emails",
    "read_email",
    "triage_email",
    "search_file",
    "check_storage",
    "render_video",
    "delete_logs",
    "send_reply",
    "update_crm",
    "escalate",
    "mark_resolved",
]


# ─── Initial State Factories ──────────────────────────────────────────────────

def _task1_state() -> Dict:
    return {
        "task_id": 1,
        "task_name": "email_triage",
        "max_steps": 25,
        "emails": [
            {
                "id": "e001", "from": "alice@starproductions.com", "client_id": "CLI001",
                "subject": "Invoice #4421 - Payment Discrepancy",
                "body": (
                    "Hi, I noticed a discrepancy in invoice #4421. "
                    "The amount charged ($4,200) doesn't match our PO of $3,800. Please advise."
                ),
                "read": False, "triaged": False, "replied": False, "escalated": False, "resolved": False,
                "correct_category": "billing", "correct_route": "billing_queue", "correct_priority": "high",
            },
            {
                "id": "e002", "from": "bob@nexusmedia.com", "client_id": "CLI002",
                "subject": "Video render keeps crashing at 73%",
                "body": (
                    "Our render for Project_X fails at 73%% with ERR_CODEC_UNSUPPORTED. "
                    "Deadline is tomorrow!"
                ),
                "read": False, "triaged": False, "replied": False, "escalated": False, "resolved": False,
                "correct_category": "technical", "correct_route": "technical_queue", "correct_priority": "urgent",
            },
            {
                "id": "e003", "from": "carol@lightspeed.io", "client_id": "CLI003",
                "subject": "When is our campaign going live?",
                "body": "Just checking in on the timeline for our Q2 campaign launch. Any updates?",
                "read": False, "triaged": False, "replied": False, "escalated": False, "resolved": False,
                "correct_category": "general", "correct_route": "account_manager_queue", "correct_priority": "low",
            },
            {
                "id": "e004", "from": "david@goldenmix.net", "client_id": "CLI004",
                "subject": "URGENT: Wrong audio in delivered video!",
                "body": (
                    "The video we received has the wrong audio track. "
                    "Product launch is Friday. PLEASE FIX IMMEDIATELY."
                ),
                "read": False, "triaged": False, "replied": False, "escalated": False, "resolved": False,
                "correct_category": "technical", "correct_route": "technical_queue", "correct_priority": "urgent",
            },
            {
                "id": "e005", "from": "eve@horizon.com", "client_id": "CLI005",
                "subject": "Thank you for the great work!",
                "body": "Just wanted to say the promo video exceeded expectations. The team loves it!",
                "read": False, "triaged": False, "replied": False, "escalated": False, "resolved": False,
                "correct_category": "general", "correct_route": "account_manager_queue", "correct_priority": "low",
            },
        ],
        "files": {"staging": [], "delivery": [], "logs": []},
        "crm": {
            "CLI001": {"name": "Star Productions", "payment_status": "outstanding", "sla_tier": "standard"},
            "CLI002": {"name": "Nexus Media", "payment_status": "current", "sla_tier": "premium"},
            "CLI003": {"name": "Lightspeed.io", "payment_status": "current", "sla_tier": "standard"},
            "CLI004": {"name": "Golden Mix", "payment_status": "current", "sla_tier": "platinum"},
            "CLI005": {"name": "Horizon Co", "payment_status": "current", "sla_tier": "standard"},
        },
        "storage_used_gb": 4.2,
        "storage_limit_gb": 10.0,
        "completed_actions": [],
        "reward_breakdown": {},
        "error_count": 0,
        "total_reward": 0.0,
        "episode_done": False,
    }


def _task2_state() -> Dict:
    return {
        "task_id": 2,
        "task_name": "video_delivery_pipeline",
        "max_steps": 20,
        "emails": [
            {
                "id": "e101", "from": "bob@nexusmedia.com", "client_id": "CLI002",
                "subject": "Please deliver Project_Phoenix_Final.mp4",
                "body": (
                    "Hi Team, we need the final delivery of Project_Phoenix_Final.mp4. "
                    "Client presentation is at 5 PM today."
                ),
                "referenced_file": "Project_Phoenix_Final.mp4",
                "read": False, "triaged": False, "replied": False, "escalated": False, "resolved": False,
                "correct_category": "technical", "correct_route": "production_queue", "correct_priority": "high",
            },
        ],
        "files": {
            "staging": [
                {"id": "f201", "name": "Project_Phoenix_Final.mp4", "client_id": "CLI002",
                 "size_gb": 2.1, "status": "ready"},
                {"id": "f202", "name": "Project_Alpha_Draft.mp4", "client_id": "CLI001",
                 "size_gb": 1.4, "status": "draft"},
            ],
            "delivery": [],
            "logs": [
                {"id": "l301", "name": "render_log_20260407.log", "size_gb": 0.8, "age_days": 1},
                {"id": "l302", "name": "render_log_20260406.log", "size_gb": 1.1, "age_days": 2},
            ],
        },
        "crm": {
            "CLI002": {
                "name": "Nexus Media", "payment_status": "current", "sla_tier": "premium",
                "delivery_status": "pending", "notes": "",
            },
        },
        "storage_used_gb": 7.2,   # tight — agent needs to delete logs before render
        "storage_limit_gb": 10.0,
        "completed_actions": [],
        "reward_breakdown": {},
        "error_count": 0,
        "total_reward": 0.0,
        "episode_done": False,
    }


def _task3_state() -> Dict:
    return {
        "task_id": 3,
        "task_name": "sla_crisis_management",
        "max_steps": 35,
        "emails": [
            {
                "id": "e301", "from": "platinum@vipstudios.com", "client_id": "CLIV01",
                "subject": "CRITICAL: Broadcast deadline in 15 min",
                "body": (
                    "Our broadcast slot is in 15 minutes! We NEED National_Broadcast_Final.mp4 NOW "
                    "or we lose the slot worth $500K."
                ),
                "referenced_file": "National_Broadcast_Final.mp4",
                "sla_minutes_remaining": 15,
                "read": False, "triaged": False, "replied": False, "escalated": False, "resolved": False,
                "correct_category": "technical", "correct_route": "production_queue",
                "correct_priority": "critical",
            },
            {
                "id": "e302", "from": "finance@elitefilm.com", "client_id": "CLIV02",
                "subject": "Invoice dispute — account on hold",
                "body": (
                    "We have been overcharged by $12,000 on our last 3 invoices. "
                    "We are pausing all future projects until resolved."
                ),
                "sla_minutes_remaining": 120,
                "read": False, "triaged": False, "replied": False, "escalated": False, "resolved": False,
                "correct_category": "billing", "correct_route": "billing_queue", "correct_priority": "high",
            },
            {
                "id": "e303", "from": "ops@studiob.com", "client_id": "CLIV03",
                "subject": "Project_Rio render failing — storage errors",
                "body": (
                    "Project_Rio render fails with storage errors. "
                    "We need delivery by end of business today."
                ),
                "referenced_file": "Project_Rio_Final.mp4",
                "sla_minutes_remaining": 480,
                "read": False, "triaged": False, "replied": False, "escalated": False, "resolved": False,
                "correct_category": "technical", "correct_route": "technical_queue", "correct_priority": "high",
            },
        ],
        "files": {
            "staging": [
                {"id": "f401", "name": "National_Broadcast_Final.mp4", "client_id": "CLIV01",
                 "size_gb": 1.6, "status": "ready"},
                {"id": "f402", "name": "Project_Rio_Final.mp4", "client_id": "CLIV03",
                 "size_gb": 2.2, "status": "ready"},
            ],
            "delivery": [],
            "logs": [
                {"id": "l501", "name": "render_batch_01.log", "size_gb": 0.9, "age_days": 3},
                {"id": "l502", "name": "render_batch_02.log", "size_gb": 1.1, "age_days": 5},
                {"id": "l503", "name": "system_health_20260405.log", "size_gb": 0.4, "age_days": 3},
            ],
        },
        "crm": {
            "CLIV01": {"name": "VIP Studios", "payment_status": "current", "sla_tier": "platinum",
                       "delivery_status": "pending", "escalated": False},
            "CLIV02": {"name": "Elite Film", "payment_status": "disputed", "sla_tier": "premier",
                       "delivery_status": "on_hold", "escalated": False},
            "CLIV03": {"name": "Studio B", "payment_status": "current", "sla_tier": "standard",
                       "delivery_status": "pending", "escalated": False},
        },
        "storage_used_gb": 7.8,   # very tight — must delete logs to render
        "storage_limit_gb": 10.0,
        "completed_actions": [],
        "reward_breakdown": {},
        "error_count": 0,
        "total_reward": 0.0,
        "episode_done": False,
    }


STATE_FACTORIES = {1: _task1_state, 2: _task2_state, 3: _task3_state}


# ─── Action Handlers ──────────────────────────────────────────────────────────

def _handle_list_emails(s: Dict, p: Dict) -> Tuple[str, float]:
    unread = sum(1 for e in s["emails"] if not e["read"])
    lines = [f"  [{e['id']}] {e['subject']} (from {e['from']}) {'[READ]' if e['read'] else '[UNREAD]'}"
             for e in s["emails"]]
    return f"📬 Inbox ({unread} unread):\n" + "\n".join(lines), 0.0


def _handle_read_email(s: Dict, p: Dict) -> Tuple[str, float, Optional[Dict]]:
    eid = p.get("email_id", "")
    email = next((e for e in s["emails"] if e["id"] == eid), None)
    if not email:
        return f"❌ Email '{eid}' not found.", -0.05, None
    email["read"] = True
    body = (
        f"📧 FROM: {email['from']}\n"
        f"   SUBJECT: {email['subject']}\n"
        f"   BODY: {email['body']}"
    )
    if email.get("referenced_file"):
        body += f"\n   REFERENCED FILE: {email['referenced_file']}"
    if email.get("sla_minutes_remaining"):
        body += f"\n   ⚠️  SLA: {email['sla_minutes_remaining']} minutes remaining!"
    return body, 0.05, email


def _handle_triage_email(s: Dict, p: Dict) -> Tuple[str, float]:
    eid = p.get("email_id", "")
    category = p.get("category", "").lower().strip()
    route = p.get("route", "").lower().strip()
    priority = p.get("priority", "medium").lower().strip()

    email = next((e for e in s["emails"] if e["id"] == eid), None)
    if not email:
        return f"❌ Email '{eid}' not found.", -0.05
    if not email["read"]:
        return f"⚠️  Read email '{eid}' first before triaging.", -0.02
    if email["triaged"]:
        return f"⚠️  Email '{eid}' already triaged.", -0.01

    reward = 0.0
    feedback = []

    if category == email["correct_category"]:
        reward += 0.06
        feedback.append(f"✅ category='{category}'")
    else:
        feedback.append(f"❌ category: got '{category}', expected '{email['correct_category']}'")

    if route == email["correct_route"]:
        reward += 0.06
        feedback.append(f"✅ route='{route}'")
    else:
        feedback.append(f"❌ route: got '{route}', expected '{email['correct_route']}'")

    if priority == email["correct_priority"]:
        reward += 0.03
        feedback.append(f"✅ priority='{priority}'")
    else:
        feedback.append(f"⚠️  priority: got '{priority}', expected '{email['correct_priority']}'")

    email["triaged"] = True
    email["assigned_category"] = category
    email["assigned_route"] = route
    email["assigned_priority"] = priority
    s["reward_breakdown"][f"triage_{eid}"] = reward

    done_count = sum(1 for e in s["emails"] if e["triaged"])
    return " | ".join(feedback) + f"  ({done_count}/{len(s['emails'])} triaged)", reward


def _handle_search_file(s: Dict, p: Dict) -> Tuple[str, float, Optional[Dict]]:
    fname = p.get("filename", "").lower()
    cid = p.get("client_id", "")
    for directory, files in s["files"].items():
        for f in files:
            match_name = fname and fname in f["name"].lower()
            match_client = cid and f.get("client_id") == cid
            if match_name or match_client:
                s["reward_breakdown"]["search_success"] = 0.1
                return f"🔍 Found '{f['name']}' in /{directory}/ (id={f['id']})", 0.1, f
    return f"❌ File not found (name='{fname}', client_id='{cid}')", -0.05, None


def _handle_check_storage(s: Dict, p: Dict) -> Tuple[str, float]:
    used = s["storage_used_gb"]
    limit = s["storage_limit_gb"]
    pct = (used / limit) * 100
    status = "🔴 CRITICAL" if pct >= 90 else ("🟡 WARNING" if pct >= 75 else "🟢 OK")
    logs_gb = sum(l["size_gb"] for l in s["files"].get("logs", []))
    return (
        f"💾 Storage: {used:.1f}GB / {limit:.1f}GB ({pct:.0f}%) [{status}]\n"
        f"   Log files: {logs_gb:.1f}GB recoverable by delete_logs"
    ), 0.02


def _handle_render_video(s: Dict, p: Dict) -> Tuple[str, float]:
    fid = p.get("file_id", "")
    fname = p.get("file_name", "").lower()

    target = None
    tdir = None
    for directory, files in s["files"].items():
        for f in files:
            if (fid and f["id"] == fid) or (fname and fname in f["name"].lower()):
                target = f
                tdir = directory
                break
        if target:
            break

    if not target:
        return "❌ File not found. Use search_file first to locate the file.", -0.1
    if tdir != "staging":
        return f"❌ File is in /{tdir}/, not /staging/. Cannot render.", -0.05
    if target["status"] not in ("ready", "pending"):
        return f"⚠️  File status='{target['status']}' — already processed.", -0.02

    # Storage check: rendering needs headroom
    needed = target["size_gb"] * 0.5
    free = s["storage_limit_gb"] - s["storage_used_gb"]
    if free < needed:
        return (
            f"💥 STORAGE FULL: need {needed:.1f}GB free, only {free:.1f}GB available. "
            "Run delete_logs to free space first."
        ), -0.1

    # Success
    target["status"] = "rendered"
    s["files"]["staging"].remove(target)
    s["files"]["delivery"].append(target)
    s["storage_used_gb"] += 0.05
    s["reward_breakdown"]["render_success"] = 0.3
    return f"✅ Rendered '{target['name']}' → moved to /delivery/", 0.3


def _handle_delete_logs(s: Dict, p: Dict) -> Tuple[str, float]:
    delete_all = p.get("delete_all", False)
    lid = p.get("log_id", "")
    logs = s["files"]["logs"]

    if delete_all:
        freed = sum(l["size_gb"] for l in logs)
        count = len(logs)
        s["files"]["logs"] = []
        s["storage_used_gb"] = max(0.0, s["storage_used_gb"] - freed)
        return f"🗑️  Deleted {count} log files, freed {freed:.1f}GB", 0.1

    if lid:
        log = next((l for l in logs if l["id"] == lid), None)
        if not log:
            return f"❌ Log '{lid}' not found.", -0.05
        s["storage_used_gb"] = max(0.0, s["storage_used_gb"] - log["size_gb"])
        logs.remove(log)
        return f"🗑️  Deleted '{log['name']}', freed {log['size_gb']:.1f}GB", 0.05

    return "⚠️  Provide log_id or delete_all=true.", -0.01


def _handle_send_reply(s: Dict, p: Dict) -> Tuple[str, float]:
    eid = p.get("email_id", "")
    msg = p.get("message", "").strip()
    if not msg:
        return "❌ 'message' is required.", -0.05
    email = next((e for e in s["emails"] if e["id"] == eid), None)
    if not email:
        return f"❌ Email '{eid}' not found.", -0.05
    email["replied"] = True
    email["reply_message"] = msg
    s["reward_breakdown"][f"reply_{eid}"] = 0.1
    return f"📤 Reply sent to {email['from']}: \"{msg[:100]}\"", 0.1


def _handle_update_crm(s: Dict, p: Dict) -> Tuple[str, float]:
    cid = p.get("client_id", "")
    updates = p.get("updates", {})
    if cid not in s["crm"]:
        return f"❌ Client '{cid}' not in CRM.", -0.05
    if not updates:
        return "❌ 'updates' dict is required.", -0.02
    s["crm"][cid].update(updates)
    s["reward_breakdown"][f"crm_{cid}"] = 0.2
    return f"✅ CRM updated for {cid}: {list(updates.keys())}", 0.2


def _handle_escalate(s: Dict, p: Dict) -> Tuple[str, float]:
    eid = p.get("email_id", "")
    reason = p.get("reason", "unspecified")
    email = next((e for e in s["emails"] if e["id"] == eid), None)
    if not email:
        return f"❌ Email '{eid}' not found.", -0.05

    sla = email.get("sla_minutes_remaining", 999)
    cid = email.get("client_id", "")
    tier = s["crm"].get(cid, {}).get("sla_tier", "standard")
    appropriate = sla <= 20 or tier in ("platinum", "premier") or email.get("correct_priority") == "critical"

    email["escalated"] = True
    if cid in s["crm"]:
        s["crm"][cid]["escalated"] = True

    reward = 0.2 if appropriate else -0.1
    tag = "✅ Correct escalation" if appropriate else "⚠️  Unnecessary escalation (reward penalty)"
    s["reward_breakdown"][f"escalate_{eid}"] = reward
    return f"🚨 {tag} | email={eid}, reason='{reason}'", reward


def _handle_mark_resolved(s: Dict, p: Dict) -> Tuple[str, float]:
    eid = p.get("email_id", "")
    email = next((e for e in s["emails"] if e["id"] == eid), None)
    if not email:
        return f"❌ Email '{eid}' not found.", -0.05
    if not (email.get("replied") or email.get("escalated") or email.get("triaged")):
        return f"⚠️  Handle email '{eid}' (reply/escalate/triage) before resolving.", -0.05
    email["resolved"] = True
    return f"✅ Email '{eid}' marked resolved.", 0.05


ACTION_HANDLERS = {
    "list_emails":   _handle_list_emails,
    "read_email":    _handle_read_email,
    "triage_email":  _handle_triage_email,
    "search_file":   _handle_search_file,
    "check_storage": _handle_check_storage,
    "render_video":  _handle_render_video,
    "delete_logs":   _handle_delete_logs,
    "send_reply":    _handle_send_reply,
    "update_crm":    _handle_update_crm,
    "escalate":      _handle_escalate,
    "mark_resolved": _handle_mark_resolved,
}


# ─── Graders (0.0 → 1.0) ─────────────────────────────────────────────────────

def _grade_task1(s: Dict) -> float:
    emails = s["emails"]
    if not emails:
        return 0.01
    correct = sum(
        1 for e in emails
        if e.get("triaged")
        and e.get("assigned_category") == e.get("correct_category")
        and e.get("assigned_route") == e.get("correct_route")
    )
    score = correct / len(emails) * 0.75
    if correct == len(emails) and s["step_count"] <= 15:
        score += max(0.0, (15 - s["step_count"]) / 15 * 0.25)
    return min(0.99, max(0.01, score))


def _grade_task2(s: Dict) -> float:
    score = 0.0
    email = next((e for e in s["emails"] if e["id"] == "e101"), None)
    if email and email.get("read"):
        score += 0.10
    if "search_success" in s["reward_breakdown"]:
        score += 0.15
    delivered = [f for f in s["files"].get("delivery", []) if f.get("client_id") == "CLI002"]
    if delivered:
        score += 0.35
    if s["crm"].get("CLI002", {}).get("delivery_status") == "delivered":
        score += 0.25
    if email and email.get("replied"):
        score += 0.15
    score -= min(0.10, s["error_count"] * 0.02)
    return min(0.99, max(0.01, score))


def _grade_task3(s: Dict) -> float:
    score = 0.0
    e301 = next((e for e in s["emails"] if e["id"] == "e301"), None)
    if e301 and e301.get("escalated"):
        score += 0.25
    delivered_v01 = [f for f in s["files"].get("delivery", []) if f.get("client_id") == "CLIV01"]
    if delivered_v01:
        score += 0.20
    e302 = next((e for e in s["emails"] if e["id"] == "e302"), None)
    if e302 and e302.get("assigned_category") == "billing":
        score += 0.10
    if e302 and e302.get("replied"):
        score += 0.05
    delivered_v03 = [f for f in s["files"].get("delivery", []) if f.get("client_id") == "CLIV03"]
    if delivered_v03:
        score += 0.15
    pct = (s["storage_used_gb"] / s["storage_limit_gb"]) * 100
    if pct < 70:
        score += 0.15
    elif pct < 80:
        score += 0.05
    score -= min(0.15, s["error_count"] * 0.03)
    return min(0.99, max(0.01, score))


TASK_GRADERS = {1: _grade_task1, 2: _grade_task2, 3: _grade_task3}


# ─── Environment Class ────────────────────────────────────────────────────────

class MediaOpsCRMEnvironment(Environment):
    """
    MediaOps-CRM-Env: A simulated media agency backend for RL training.

    Three tasks simulate real-world operations professionals face daily:
    email triage, video delivery pipelines, and multi-client SLA crises.
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        self._s: Dict = {}
        self._current_email: Optional[Dict] = None
        self._current_file: Optional[Dict] = None

    def reset(self, task_id: int = 1, **kwargs) -> "MediaOpsObservation":  # type: ignore[override]
        task_id = max(1, min(3, int(task_id)))
        self._s = STATE_FACTORIES[task_id]()
        self._s["episode_id"] = str(uuid.uuid4())
        self._s["step_count"] = 0
        self._current_email = None
        self._current_file = None
        cfg = TASK_CONFIGS[task_id]
        return self._build_obs(
            f"🚀 Task {task_id}: {cfg['display_name']}\n"
            f"   {cfg['description']}\n"
            f"   You have {cfg['max_steps']} steps. Start with list_emails.",
            0.0, done=False,
        )

    def step(self, action: "MediaOpsAction") -> "MediaOpsObservation":  # type: ignore[override]
        s = self._s
        if s.get("episode_done"):
            return self._build_obs("Episode already ended. Call reset().", 0.0, done=True)

        s["step_count"] = s.get("step_count", 0) + 1
        atype = action.action_type.lower().strip()
        params = action.params or {}

        if atype not in ACTION_HANDLERS:
            s["error_count"] = s.get("error_count", 0) + 1
            return self._build_obs(
                f"❌ Unknown action '{atype}'. Valid actions: {AVAILABLE_ACTIONS}",
                -0.05, done=False,
            )

        handler = ACTION_HANDLERS[atype]
        try:
            result = handler(s, params)
        except Exception as exc:  # pragma: no cover
            s["error_count"] = s.get("error_count", 0) + 1
            return self._build_obs(f"💥 Internal error: {exc}", -0.1, done=False)

        if len(result) == 3:
            message, reward, extra = result
            if atype == "read_email":
                self._current_email = extra
            elif atype == "search_file" and extra:
                self._current_file = extra
        else:
            message, reward = result

        # per-step cost on zero/negative actions
        net = reward - (0.03 if reward <= 0 else 0.0)
        net = max(-0.5, net)
        s["total_reward"] = min(1.0, max(0.0, s.get("total_reward", 0.0) + net))
        s.setdefault("completed_actions", []).append(atype)

        done = self._check_done(s)
        if done:
            final = TASK_GRADERS[s["task_id"]](s)
            s["total_reward"] = final
            s["episode_done"] = True
            message += f"\n\n🏁 Episode complete! Final score: {final:.3f}"
            net = final

        return self._build_obs(message, net, done=done)

    @property
    def state(self) -> State:
        return State(
            episode_id=self._s.get("episode_id", ""),
            step_count=self._s.get("step_count", 0),
        )

    # ── private helpers ──────────────────────────────────────────────────────

    def _check_done(self, s: Dict) -> bool:
        if s["step_count"] >= s["max_steps"]:
            return True
        if s.get("error_count", 0) >= 10:
            return True
        tid = s["task_id"]
        if tid == 1:
            return all(e["triaged"] for e in s["emails"])
        if tid == 2:
            delivered = any(f.get("client_id") == "CLI002" for f in s["files"].get("delivery", []))
            crm_ok = s["crm"].get("CLI002", {}).get("delivery_status") == "delivered"
            return delivered and crm_ok
        if tid == 3:
            return all(
                e.get("triaged") or e.get("escalated") or e.get("resolved") or e.get("replied")
                for e in s["emails"]
            )
        return False

    def _build_obs(self, message: str, reward: float, done: bool) -> "MediaOpsObservation":
        s = self._s
        pct = (s.get("storage_used_gb", 0) / s.get("storage_limit_gb", 10)) * 100
        if pct >= 75:
            message += f"  ⚠️  STORAGE {pct:.0f}% FULL!"

        inbox = [
            {k: v for k, v in e.items()
             if k in ("id", "from", "subject", "read", "triaged", "replied", "escalated", "resolved")}
            for e in s.get("emails", [])
        ]
        crm_snap = [
            {"client_id": cid, **{k: v for k, v in data.items()
                                  if k in ("name", "sla_tier", "payment_status", "delivery_status", "escalated")}}
            for cid, data in s.get("crm", {}).items()
        ]
        task_progress: Dict[str, Any] = {
            "task_id": s.get("task_id", 1),
            "step": s.get("step_count", 0),
            "max_steps": s.get("max_steps", 25),
            "steps_remaining": max(0, s.get("max_steps", 25) - s.get("step_count", 0)),
            "error_count": s.get("error_count", 0),
            "running_score": round(s.get("total_reward", 0.0), 3),
        }
        tid = s.get("task_id", 1)
        if tid == 1:
            task_progress["triaged"] = f"{sum(1 for e in s.get('emails', []) if e.get('triaged'))}/{len(s.get('emails', []))}"
        elif tid == 2:
            task_progress["delivery_status"] = s.get("crm", {}).get("CLI002", {}).get("delivery_status", "pending")
        elif tid == 3:
            handled = sum(1 for e in s.get("emails", [])
                         if e.get("triaged") or e.get("escalated") or e.get("resolved") or e.get("replied"))
            task_progress["clients_handled"] = f"{handled}/{len(s.get('emails', []))}"

        return MediaOpsObservation(
            done=done,
            reward=round(max(-1.0, min(1.0, reward)), 4),
            message=message,
            inbox=inbox,
            current_email=self._current_email,
            current_file=self._current_file,
            storage_used_gb=round(s.get("storage_used_gb", 0.0), 2),
            storage_limit_gb=s.get("storage_limit_gb", 10.0),
            crm_snapshot=crm_snap,
            available_actions=AVAILABLE_ACTIONS,
            task_progress=task_progress,
            reward_breakdown=dict(s.get("reward_breakdown", {})),
        )
