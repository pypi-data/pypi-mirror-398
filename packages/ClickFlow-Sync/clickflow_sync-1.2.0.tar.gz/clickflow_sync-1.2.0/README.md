# ClickFlow-Sync 🚀

ClickFlow-Sync is a professional, idempotent Python engine designed to bridge external
data sources (Vulnerability Scanners, Monitoring Tools, or CI/CD pipelines) with ClickUp.
Unlike a simple API wrapper, ClickFlow-Sync manages state. It ensures that if a scanner
finds the same issue multiple times, it updates the existing ClickUp task instead of creating
annoying duplicates.

## 📦 Installation

#### 1. Clone the repository:

```
git clone https://github.com/jenilmistryhq/ClickFlow-Sync.git
cd ClickFlow-Sync
```
#### 2. Install Dependencies:

```
pip install -r requirements.txt
```
## ⚙ Configuration (.env)

Create a `.env` file in your project root to manage credentials securely:
```
# ClickUp Configuration
CLICKUP_API_KEY=pk_your_api_key_here
CLICKUP_LIST_ID=123456789012
CLICKUP_DEFAULT_ASSIGNEE=1234567,8901234
# Slack Configuration (Optional)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T000/B000/XXXX
```

## 🛠 Usage Patterns

ClickFlow-Sync is designed to be a "plug-and-play" package. You do not need to modify the
core `src/` files.

**1. Smart Integration (With Slack & Member Mapping)**

This is the recommended way to use the package. It allows you to map IDs to real names
and departments.


```
from src.engine import ClickFlowEngine
from src.models import ClickUpTask
from src.slack_plugin import SlackPlugin

# 1. Map ClickUp IDs to Human Names and Departments
MEMBER_DATA = {
    1234567: {"name": "Jack", "dept": "Security Engineering"},
    8901234: {"name": "Alice", "dept": "DevOps"}
}

# 2. Setup Tools
engine = ClickFlowEngine()
slack = SlackPlugin(member_info=MEMBER_DATA)

# 3. Define the Task
task = ClickUpTask(
    internal_id="SCAN-2025-001", 
    title="[CRITICAL] SQL Injection Detected",
    description="Found on /api/login endpoint.",
    priority=1,
    category="security",
    tags=["automated-scan"]
)

# 4. Sync & Notify
# This will update ClickUp AND send a rich notification
engine.upsert_task(task, callback=slack.send_notification)
```
## 🎨 Customization

* **Clean Output Logic:**
The engine uses "Smart Filtering." If a field like `tags`, `priority`, or `description` is empty, it is

* **Automatically hidden:** from both the local terminal preview and the Slack message to keep
notifications clean.

* **Local Testing (No Slack Required):**
If you haven't added a `SLACK_WEBHOOK_URL` yet, the engine will still work! It will print a
beautiful, human-readable Local Notification Preview to your terminal so you can verify the
data before going live.

* **Custom Message Formatting:**
You can bypass the default Slack look by passing your own formatter function:
def my_mini_style(task, clickup_id, action):


```
def my_mini_style(task, clickup_id, action):
    return {"text": f"🚀 {action}: {task.title} (ID: {clickup_id})"}

engine.upsert_task(task, callback=lambda t, cid, act: 
    slack.send_notification(t, cid, act, custom_formatter=my_mini_style)
)
```
## 🏗 Architecture & State

ClickFlow-Sync creates a `sync_state.json` file to track tasks.

● **Creation:** If an `internal_id` is new, a task is created.

● **Update:** If the `internal_id` exists, it performs a PUT request to update the task.

● **Auto-Recovery:** If a task is manually deleted in ClickUp, the engine detects the
error, clears the local state, and automatically re-creates the task on the next run.

## 📝 Data Model (ClickUpTask)

```
| Field           | Type | Default    | Description                                                     |
|-----------------|------|------------|-----------------------------------------------------------------|
| internal_id     | str  | Required   | Unique ID from your source (e.g., CVE ID).                      |
| title           | str  | Required   | The ClickUp task name.                                          |
| description     | str  | ""         | The task body / content.                                       |
| category        | str  | "general"  | Matches keys in your Team Map for auto-assignment.              |
| priority        | int  | None       | 1 (Urgent), 2 (High), 3 (Normal), 4 (Low).                      |
| tags            | list | []         | List of strings for ClickUp tags.                               |
| target_list_id  | str  | None       | Override the default list for specific tasks.                   |

```

## 🤝 Contributing

Contributions are welcome! Please open an issue or submit a pull request.