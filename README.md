---
title: MediaOps CRM Env
emoji: 🎬
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
tags:
  - openenv
  - reinforcement-learning
  - media-ops
  - crm
  - email-triage
---

# MediaOps-CRM-Env

> **Meta × PyTorch × Hugging Face OpenEnv Hackathon Submission**

A production-quality OpenEnv reinforcement learning environment that simulates a **media agency operations backend**. An AI agent must triage client emails, manage a mock file system, execute video delivery pipelines, and navigate multi-client SLA crises — all the operations a real media agency handles daily.

---

## 🎯 Environment Overview

| Property | Value |
|---|---|
| Domain | Media Operations + CRM |
| Tasks | 3 (easy → medium → hard) |
| Reward range | 0.0 → 1.0 |
| Max steps | 25 / 20 / 35 per task |
| Framework | OpenEnv + FastAPI |

---

## 📋 Tasks

### Task 1: Email Triage & Classification *(Easy)*
**Objective**: Classify and route 5 incoming client emails to the correct department.

**Agent must**: `list_emails → read_email → triage_email` for every email.

**Reward**: +0.06 correct category · +0.06 correct route · +0.03 correct priority · +0.25 speed bonus (all done in ≤15 steps)

**Score range**: 0.0 – 1.0 (0.75 from accuracy + 0.25 speed bonus)

---

### Task 2: Video Delivery Pipeline *(Medium)*
**Objective**: Process a premium client's video delivery request end-to-end.

**Agent must**: `read_email → search_file → check_storage → delete_logs (if needed) → render_video → send_reply → update_crm`

**Reward**: Partial credit per completed step. Storage management is required (starts at 72% full).

**Score range**: 0.0 – 1.0

---

### Task 3: Multi-Client SLA Crisis *(Hard)*
**Objective**: Handle 3 simultaneous client crises with overlapping SLA deadlines and 78% full storage.

- **Client 1 (CRITICAL)**: Broadcast in 15 minutes → must escalate immediately
- **Client 2 (HIGH)**: Invoice dispute → triage to billing queue + reply
- **Client 3 (HIGH)**: Render failing due to storage → delete logs + render

**Reward**: Weighted by urgency, escalation correctness, and storage management.

**Score range**: 0.0 – 1.0

---

## 🎮 Action Space

| action_type | params | Description |
|---|---|---|
| `list_emails` | — | Show inbox summary |
| `read_email` | `email_id` | Read full email content |
| `triage_email` | `email_id, category, route, priority` | Classify and route |
| `search_file` | `filename` or `client_id` | Find file across directories |
| `check_storage` | — | Report storage usage |
| `render_video` | `file_id` or `file_name` | Process video file |
| `delete_logs` | `log_id` or `delete_all=true` | Free storage |
| `send_reply` | `email_id, message` | Reply to client |
| `update_crm` | `client_id, updates={}` | Update CRM record |
| `escalate` | `email_id, reason` | Escalate to human manager |
| `mark_resolved` | `email_id` | Close email |

**Valid categories**: `billing`, `technical`, `general`  
**Valid routes**: `billing_queue`, `technical_queue`, `account_manager_queue`, `production_queue`  
**Valid priorities**: `low`, `medium`, `high`, `urgent`, `critical`

---

## 👁️ Observation Space

Each step returns a `MediaOpsObservation` containing:

| Field | Type | Description |
|---|---|---|
| `message` | str | Result of the last action |
| `inbox` | list | Email summaries (id, from, subject, status flags) |
| `current_email` | dict | Full email body (after `read_email`) |
| `current_file` | dict | File details (after `search_file`) |
| `storage_used_gb` | float | Current storage usage |
| `storage_limit_gb` | float | Storage cap (10.0 GB) |
| `crm_snapshot` | list | Client CRM overview |
| `available_actions` | list | All valid action types |
| `task_progress` | dict | Step count, errors, running score |
| `reward_breakdown` | dict | Per-component reward history |

---

## 🚀 Setup & Usage

### Local Development
```bash
# Install dependencies
uv sync

# Start server
uvicorn server.app:app --host 0.0.0.0 --port 8000 --reload

# Run inference against all 3 tasks
export API_BASE_URL="https://api.openai.com/v1"
export MODEL_NAME="gpt-4o-mini"
export OPENAI_API_KEY="sk-..."
export HF_SPACE_URL="http://localhost:8000"
python inference.py
```

### Docker
```bash
docker build -t mediaops-crm-env .
docker run -p 8000:8000 mediaops-crm-env

# Run inference vs Docker container
export IMAGE_NAME="mediaops-crm-env"
python inference.py
```

### Python Client
```python
from client import MediaOpsCRMEnv
from models import MediaOpsAction

with MediaOpsCRMEnv(base_url="http://localhost:8000") as env:
    result = env.reset(task_id=1)
    result = env.step(MediaOpsAction(action_type="list_emails", params={}))
    print(result.observation.message)
```

---

## 📊 Baseline Scores

| Task | Difficulty | Baseline (random) | Baseline (GPT-4o-mini) |
|---|---|---|---|
| 1: Email Triage | Easy | ~0.10 | ~0.65 |
| 2: Video Delivery | Medium | ~0.05 | ~0.55 |
| 3: SLA Crisis | Hard | ~0.02 | ~0.40 |
| **Average** | | **~0.06** | **~0.53** |

---

## 🏗️ Environment Design

### Multiple Trajectories
- ✅ **Happy path**: email → file found → render → CRM updated → CSAT bonus
- ⚠️ **Missing file**: search fails → must reply with BLOCKED status
- 💥 **Storage full**: delete logs → retry render → success
- 🚨 **SLA breach**: critical email → escalate immediately → partial credit
- 🔄 **Already processed**: penalty for redundant actions

### Reward Shaping
- Partial credit at every meaningful step (not just end-of-episode)
- Per-step cost on invalid/redundant actions (-0.03)
- Final episode score computed by deterministic grader
- Reward clamped to [0.0, 1.0]

---

## 📁 Project Structure
```
my_env_name/
├── models.py                    ← Pydantic Action + Observation types
├── client.py                    ← WebSocket client
├── inference.py                 ← Baseline inference script (required)
├── openenv.yaml                 ← OpenEnv manifest
├── pyproject.toml               ← Package metadata
├── Dockerfile                   ← Container definition
├── README.md
└── server/
    ├── app.py                   ← FastAPI app
    └── mediaops_environment.py  ← Core environment logic
```

---

## 📜 License
MIT License — open source and ready for the community.
