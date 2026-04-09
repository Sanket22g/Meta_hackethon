# MediaOps-CRM-Env

## A Meta PyTorch Hackathon OpenEnv Submission

**MediaOps-CRM-Env** is an advanced, real-world OpenEnv simulation that trains agentic AI systems to operate the backend of a highly-pressured digital media agency. 

Instead of playing a toy game, the agent is dropped into the role of a Digital Media Operations Manager where it must navigate partial observability, execute long-horizon multi-step pipelines, and juggle simultaneous VIP crises—all within strict storage limits and SLA deadlines.

---

## 🚀 The Three Agentic Tasks

The environment evaluates agents across three progressively difficult tasks, testing their ability to plan, prioritize, and recover from failures.

### Task 1: Email Triage & Classification (Easy)
* **Objective:** Read 5 incoming client emails and properly triage them.
* **Agentic Challenge:** The agent must invoke `list_emails`, sequentially `read_email` for each unread item, classify the intent (billing, technical, general), determine the correct queue (production, account manager, etc.), and accurately assign a priority format.
* **Max Steps:** 25

### Task 2: Video Delivery Pipeline (Medium)
* **Objective:** Execute an end-to-end media delivery pipeline.
* **Agentic Challenge:** The agent receives an email request for a final video delivery. It must search the file system (`search_file`) for the correct `.mp4`, evaluate the server's storage limits (`check_storage`), optionally free up space by deleting old renderer logs (`delete_logs`), officially render/process the file (`render_video`), send a confirmation reply to the client (`send_reply`), and officially update the client's database status (`update_crm`).
* **Max Steps:** 20

### Task 3: Multi-Client SLA Crisis (Hard)
* **Objective:** Manage three overlapping crises under extreme storage pressure.
* **Agentic Challenge:** Absolute chaos. A Platinum VIP client demands a video for a live TV broadcast in 15 minutes. Another Premier client has their account frozen due to a $12,000 billing dispute. The server storage is 78% full. The agent must realize it must immediately drop everything to free up log storage, render the VIP video, properly escalate the 15-minute deadline to human intervention, and accurately route the billing dispute—all while being penalized for every wasted API action.
* **Max Steps:** 35

---

## 📊 Deterministic Grading & Scoring (0.0 to 1.0)

Grades are deterministic and reflect partial progress toward task completion. The final score is constrained between `0.0` and `1.0`.

* **Task 1 Grader:** 75% of the score is based on accurately assigning the exact `correct_category` and `correct_route` to all 5 emails. The remaining 25% is an efficiency bonus awarded only if the agent perfectly triages all emails in 15 steps or fewer.
* **Task 2 Grader:** Rewards partial progress across the pipeline. +10% for reading the email, +15% for successfully searching and finding the file, +35% if the file successfully renders to the `/delivery/` directory, +25% for successfully updating the CRM record to `"delivered"`, and +15% for sending the email reply. Penalty (-2%) is applied for every unrecognized command or error generated.
* **Task 3 Grader:** Heavily weighted on crisis prioritization. +25% for correctly escalating the 15-minute VIP email immediately. +20% for rendering the exact VIP file requested. +10% for correctly routing the billing dispute and +5% for replying to it. +15% for completing the other standard render. Furthermore, +15% is awarded at the end of the episode if overall storage is brought under 70%.

---

## 🛠️ Action & Observation Space

### The Action Space
The environment expects the LLM to output a valid JSON object requesting one of the following explicit tools, accompanied by parameters:

* `list_emails`
* `read_email` (params: `email_id`)
* `triage_email` (params: `email_id`, `category`, `route`, `priority`)
* `search_file` (params: `filename` or `client_id`)
* `check_storage` 
* `render_video` (params: `file_name` or `file_id`)
* `delete_logs` (params: `log_id` or `delete_all`)
* `send_reply` (params: `email_id`, `message`)
* `update_crm` (params: `client_id`, `updates`)
* `escalate` (params: `email_id`, `reason`)
* `mark_resolved` (params: `email_id`)

### The Observation Space
After every step, the agent receives a highly structured observation payload containing:
* A human-readable `message` showing the direct output of their last tool action.
* An `inbox` summary of unread/read/resolved emails.
* `storage_used_gb` and `storage_limit_gb`.
* `crm_snapshot` showing a snapshot of current client database tiers and statuses.
* The immediate `reward` granted for that step.

---

## ⚙️ How to Test and Run

The environment does not require an active Docker container for baseline testing. The `inference.py` script runs the environment entirely in-process before grading the model.

1. Install dependencies:
   ```bash
   uv sync
   # or
   pip install openenv-core openai pydantic fastapi uvicorn
   ```
2. Run the baseline evaluation script:
   ```bash
   export MODEL_NAME="gpt-4o-mini"
   export API_BASE_URL="https://api.openai.com/v1"
   export HF_TOKEN="your-api-key"
   
   python inference.py
   ```

The inference script perfectly outputs the required `[START]`, `[STEP]`, and `[END]` stdout format necessary for automated qualification logging.

---

## 🏆 Hackathon Qualification Alignment Structure

1. **Real-world Utility**: Models a highly realistic Digital Media workflow, testing practical API usage, state-tracking, and priority routing.
2. **OpenEnv Spec Compliance**: Built strictly using `openenv-core` providing the Playground GUI out of the box, `openenv.yaml`, and strict Pydantic typed models.
3. **Deploys to HF Spaces**: Port 7860 mapped correctly via Dockerfile, ensuring automated ping access to `POST /reset`.
4. **Baseline Included**: Clean `inference.py` script that hits ~0.65 - 0.70 score averages using deterministic grading.
