# AgentTrace - Time-Travel Debugging for AI Agents 🚀

**The Industry's First Time-Travel Debugger for LLM Agents + AutoFix Engine**

AgentTrace enables you to record, replay, and debug AI agent executions with full determinism. Jump to any point in time, edit the past, and see what would have happened. Our **AutoFix Engine (AFE)** automatically detects failures, classifies root causes, generates fixes, validates them in sandboxes, and can even auto-apply solutions.

## 🚀 Quick Start

```bash
# Install
pip install agenttrace

# Record a trace
agenttrace record my_agent.py

# List traces
agenttrace list

# Replay a trace
agenttrace replay <trace-id>

# Jump to specific step
agenttrace replay <trace-id> --step 42
```

## ✨ Features

### ⏱️ Time-Travel Debugging
- **Record** agent executions with full state capture
- **Replay** deterministically (same random numbers, same API responses)
- **Jump** to any step using keyframe snapshots
- **Resume** execution from any saved step (state hydration + runtime restore)
- **Edit** the past (fork a branch, tweak payloads, continue execution)

### � AutoFix Engine (AFE)
- **Automatic Failure Detection** - Detects errors in traces automatically
- **Root Cause Analysis** - Classifies failures (rate limits, API errors, missing context, etc.)
- **Multi-Strategy Fix Generation** - Code patches, config changes, prompt improvements, retry policies
- **Sandbox Validation** - Tests fixes in isolated environments before applying
- **Policy-Based Ranking** - Prioritizes fixes by confidence, risk, and success rate
- **Auto-Apply** - High-confidence fixes can be applied automatically
- **LLM-Powered** - Uses Groq for intelligent code generation and analysis

### �🛡️ Safety Sandbox
- **Virtual File System** - File writes are isolated during replay
- **VCR Pattern** - API calls are cached (no costs during debugging)
- **Deterministic Replay** - Random numbers, time, and API calls are frozen

### ☁️ Full SaaS Platform
- **Multi-User Auth** - Email magic link login with organization isolation
- **Cloud Storage** - Traces stored in Supabase Storage with CDN delivery
- **Worker Fleet** - Python workers for distributed trace processing
- **Real-Time Dashboard** - AFE monitoring, trace timeline, multiverse branching
- **Email Notifications** - Brevo integration for failure alerts and fix notifications

### 🤖 Framework Support
- OpenAI API
- Groq API
- LangChain (coming soon)
- AutoGen (coming soon)

## 📖 Usage

### Basic Recording

```python
# my_agent.py
from groq import Groq

client = Groq()
response = client.chat.completions.create(
    model="llama3-8b-8192",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

```bash
agenttrace record my_agent.py
# Output: ✅ Trace recorded: abc123-def456-...
```

### Replay Mode

```bash
export AGENTTRACE_MODE=REPLAY
export AGENTTRACE_ID=abc123-def456-...
python my_agent.py
# Runs with cached API responses (free!)
```

### Resuming from a Saved Step

```bash
# Jump directly to step 25 and resume from there
agenttrace replay abc123-def456-... --step 25
python my_agent.py  # execution restarts with the recorded locals/globals
```

### Branching & Editing History

```bash
# Create a branch at a specific step (requires a snapshot/keyframe there)
agenttrace branch create abc123-def456-... --step 42 --name patch-output

# Override a recorded event payload (e.g., change an LLM response)
agenttrace branch edit abc123-def456-...__patch-output --event 42 --payload '{"content":"Rewritten response"}'

# Replay from that branch and continue deterministically
agenttrace replay abc123-def456-... --branch abc123-def456-...__patch-output
python my_agent.py  # starts from the forked state with your edits applied
```

### AI-Powered Auto-Fix

```bash
# Auto-fix errors using Groq AI
agenttrace fix <trace-id>

# Fix a specific step
agenttrace fix <trace-id> --step 42

# Use your own API key
agenttrace fix <trace-id> --api-key your_groq_key

# Override Groq model (or set GROQ_MODEL env var)
agenttrace fix <trace-id> --model llama-3.1-8b-instant

# Use heuristic suggestions instead of AI
agenttrace fix <trace-id> --no-ai
```

**Setup:**
1. Copy `.env.example` to `.env`
2. Add your Groq API key: `GROQ_API_KEY=your_key_here`
3. (Optional) Set `GROQ_MODEL=llama-3.1-8b-instant` (see https://console.groq.com/docs/models for options)
4. Get your key from: https://console.groq.com/

The AI fixer analyzes error traces, extracts code context, and generates actual code patches with explanations.

### Automatic State Capture

AgentTrace automatically captures:
- Local variables at keyframe intervals
- Global state
- Function call stack
- API request/response pairs
- Random number sequences
- Time/DateTime values

## 🚀 Production Deployment

### 1️⃣ Supabase Setup

```bash
# Run all migrations
cd supabase
supabase db push

# Or manually run SQL files:
# - supabase_fix_afe_constraint.sql (AFE type constraint)
# - supabase_fix_afe_status_constraint.sql (AFE status constraint)
# - supabase_add_notifications.sql (Brevo integration)
```

### 2️⃣ Environment Configuration

Copy `frontend/.env.local.example` to `frontend/.env.local` and configure:

```bash
# Supabase
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Groq (for AFE)
GROQ_API_KEY=your_groq_api_key

# Brevo (for notifications)
BREVO_API_KEY=your_brevo_api_key
BREVO_SENDER_EMAIL=your_email@domain.com
BREVO_SENDER_NAME="AgentTrace"
```

### 3️⃣ Frontend Deployment

```bash
cd frontend
npm install
npm run build
npm start
```

Or deploy to Vercel:

```bash
vercel --prod
```

### 4️⃣ Worker Deployment

```bash
cd worker
pip install -r requirements.txt
python main.py
```

For production, use process managers:

```bash
# Using PM2
pm2 start main.py --name agenttrace-worker --interpreter python

# Using systemd (create /etc/systemd/system/agenttrace-worker.service)
# Or containerize with Docker
```

### 5️⃣ Brevo IP Whitelisting

Add your worker's IP address to Brevo's authorized IPs:
1. Go to https://app.brevo.com/security/authorised_ips
2. Add your server IP
3. Restart worker

### Architecture Overview

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Next.js    │────▶│  Supabase    │◀────│   Python    │
│  Frontend   │     │  (Auth/DB/   │     │   Workers   │
│             │     │   Storage)   │     │             │
└─────────────┘     └──────────────┘     └─────────────┘
      │                    │                     │
      │                    ├─────────────────────┤
      │                    │   Polling Jobs      │
      │                    │   Processing Traces │
      │                    │   Running AFE       │
      └────────────────────┴─────────────────────┘
```

## 🧪 Tests

### Pytest (Tracer + CLI)
```bash
pytest tests/e2e
```

### Next.js API Routes
```bash
cd frontend
npm install   # first run
npm run test:api
```

### UI Automation
```bash
cd frontend
npx playwright test   # Run UI branch flow tests
```

## 🏗️ Architecture

AgentTrace uses a **Hybrid Keyframe Architecture**:
- **Delta Log**: Lightweight event log (API calls, random numbers)
- **Keyframes**: Full memory snapshots every N steps (default: 10)
- **Fast Seek**: Load nearest keyframe + replay deltas = instant jump to any step

## 🔒 Security

- **PII Scrubbing**: Automatic detection and redaction (coming soon)
- **Secrets Detection**: API keys are automatically masked
- **Sandbox Isolation**: Replay can't affect production systems

## ☁️ Supabase Backend (Optional)

AgentTrace now supports a hosted Supabase backend for team collaboration:

- **Multi-user auth** — Email magic link login with org isolation
- **Cloud storage** — Traces and snapshots stored in Supabase Storage
- **Job queue** — Replay jobs queued in Postgres for worker processing
- **Row-level security** — All data scoped by organization

**Setup:** See `supabase/README.md` for instructions. You can connect to a real Supabase project directly — no Docker required!

## 📊 Recent Improvements

### ✅ December 2024 - Stability & Production Readiness

**Bug Fixes:**
- Fixed AFE database constraints to support all candidate types
- Fixed script upload for Fork, Simulate, and Replay operations
- Fixed worker organization selection for multi-tenant support
- Fixed Supabase import issues in AFE stats API
- Fixed GitHub secret detection by excluding API keys from commits

**Features:**
- Added AutoFix Engine link to sidebar navigation
- Created comprehensive stress testing suite (5 concurrent jobs)
- Added utility scripts for debugging and verification
- Implemented reset_traces.py for clean database resets
- Added migration verification scripts

**Infrastructure:**
- Configured Brevo email notifications for failures and fixes
- Set up proper .gitignore for security (excludes .env files and local traces)
- Established GitHub repository with clean commit history
- Created deployment documentation and setup guides

## 📊 Roadmap

- [x] Core time-travel engine
- [x] VCR pattern for LLM APIs
- [x] Virtual File System
- [x] Automatic state capture
- [x] CLI tool
- [x] Web UI (Timeline visualizer)
- [x] AutoFix Engine (RCA + multi-strategy fixes)
- [x] Cloud storage & sharing (Supabase backend)
- [x] Python worker for remote replay
- [x] Email notifications (Brevo)
- [x] Stress testing & production stability
- [ ] LangChain integration
- [ ] CLI login & token auth
- [ ] Auto-apply policies with approval workflows

## 🤝 Contributing

This is a rapidly evolving project. Contributions welcome!

## 📄 License

MIT License

## 🙏 Acknowledgments

Built on research from:
- Temporal (Durable Execution)
- CRIU (Checkpoint/Restore)
- cloudpickle (State Serialization)
- pyfakefs (Virtual File System)

---

**Made with ❤️ for the AI Agent community**

