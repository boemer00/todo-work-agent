# AI Task Agent - Production Deployment on Google Cloud Run

![Tests](https://img.shields.io/badge/tests-50%20passing-success)
![Coverage](https://img.shields.io/badge/coverage-77%25-yellow)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Deployed](https://img.shields.io/badge/deployed-Google%20Cloud%20Run-blue)

An intelligent task management agent deployed on **Google Cloud Run** with **WhatsApp interface**, powered by **LangGraph** and **GPT-4o-mini**. Features natural language date parsing, multi-user support, and Google Calendar integration. Built to demonstrate production-ready AI engineering skills.

**Live Service**: https://ai-task-agent-kbimuakj2a-uc.a.run.app

---

## 🌐 Live Demo

**Try the WhatsApp bot now!**

1. Text: **+1 (415) 523-8886**
2. Send: `join [your-sandbox-code]` (get code from Twilio console)
3. Try: `remind me to buy milk tomorrow at 2pm`

**Service Status**: ✅ Live on Google Cloud Run (us-central1)

---

## ⚡ Key Features

- **🚀 Production Deployment** - Fully deployed on Google Cloud Run with HTTPS endpoints
- **💬 WhatsApp Interface** - Natural conversational UI via Twilio WhatsApp API
- **🧠 LangGraph Agent** - ReAct pattern with state management and checkpointing
- **🗄️ Cloud-Native Storage** - SQLite databases synced to Cloud Storage
- **🌍 Multi-User Support** - Isolated task lists per user with phone number hashing
- **⏰ Smart Date Parsing** - "tomorrow at 2pm", "next Friday", "in 3 hours"
- **🔒 Production Security** - Webhook signature verification, rate limiting (10 msg/min)
- **📊 Observability** - LangSmith tracing for debugging and monitoring

---

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────────────┐      ┌──────────────────┐
│  WhatsApp   │─────▶│    Cloud Run         │─────▶│ Cloud Storage    │
│  (Twilio)   │◀─────│  FastAPI + LangGraph │      │ (SQLite DBs)     │
└─────────────┘      └──────────────────────┘      └──────────────────┘
                              │
                              ▼
                       ┌──────────────┐
                       │  GPT-4o-mini │
                       │   + Tools    │
                       └──────────────┘
                              │
                     ┌────────┴────────┐
                     ▼                 ▼
              ┌───────────┐     ┌──────────┐
              │   Redis   │     │  Google  │
              │ (Limits)  │     │ Calendar │
              └───────────┘     └──────────┘
```

**Data Flow**:
1. User sends WhatsApp message → Twilio webhook
2. Cloud Run receives POST → verifies signature → sends ACK
3. LangGraph agent processes message → calls tools
4. Tools interact with database/calendar
5. Response sent back via Twilio Messages API
6. Databases synced to Cloud Storage on shutdown

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Agent Framework** | LangGraph | State management, tool orchestration, checkpointing |
| **LLM** | GPT-4o-mini | Natural language understanding, tool selection |
| **Backend** | FastAPI | Async webhook endpoints, background processing |
| **Database** | SQLite + Cloud Storage | Task persistence, conversation memory |
| **Messaging** | Twilio WhatsApp API | User interface, webhook integration |
| **Deployment** | Google Cloud Run | Serverless container hosting, auto-scaling |
| **Rate Limiting** | Redis Cloud | 10 messages/min per user |
| **Observability** | LangSmith | Agent tracing, debugging, performance monitoring |
| **CI/CD** | GitHub Actions | Automated testing (planned) |

---

## 🚀 Quick Start (Local Development)

### 1. Clone and Install

```bash
git clone https://github.com/boemer00/my-agent.git
cd my-agent
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create `.env` file:

```bash
# Required
OPENAI_API_KEY=your_openai_key_here

# Optional - Observability
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key_here
LANGCHAIN_PROJECT=my-todo-agent

# Optional - WhatsApp (for local webhook testing)
TWILIO_ACCOUNT_SID=ACxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

### 3. Run Locally

**CLI mode** (terminal interface):
```bash
python app.py
```

**API mode** (WhatsApp webhook):
```bash
uvicorn api.main:app --reload --port 8080
```

**Expose local webhook** (for Twilio testing):
```bash
ngrok http 8080
# Update Twilio webhook to: https://your-ngrok-url.ngrok.io/whatsapp/webhook
```

---

## 💬 Example Interaction

```
User: Hi!
Agent: 👋 Hi! I'm your task assistant...

User: remind me to buy kombucha tomorrow at 2pm
Agent: Working on it.
Agent: ✓ Reminder set: 'buy kombucha' for Thursday, October 31, 2025 at 02:00 PM

User: show my tasks
Agent: Your tasks:
       1. buy kombucha (Due: tomorrow at 2pm)

User: mark 1 as done
Agent: ✓ Marked task #1 as done: 'buy kombucha'
```

---

## 🧪 Testing

**Test Coverage**: 50 tests | 64% coverage | <3s runtime

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov

# Specific categories
pytest tests/test_agent_flows.py    # Integration tests
pytest tests/test_tools.py          # Tool unit tests
pytest tests/test_database.py       # Repository tests
pytest tests/test_date_parser.py    # Date parsing tests
```

### Test Structure

```
tests/
├── conftest.py           # Shared fixtures, test configuration
├── test_agent_flows.py   # End-to-end agent tests (8 tests)
├── test_database.py      # Database/Repository tests (14 tests)
├── test_date_parser.py   # Date utility tests (13 tests)
└── test_tools.py         # Tool function tests (15 tests)
```

**Key Testing Patterns**:
- ✅ Mocked external APIs (Google Calendar, OpenAI) for fast tests
- ✅ Isolated test databases (in-memory SQLite)
- ✅ Time-freezing for predictable date parsing tests
- ✅ Pytest fixtures for setup/teardown

---

## 🗺️ Roadmap: Phase 2 - Per-User OAuth

**Current State**: Google Calendar sync works locally with single account
**Goal**: Each WhatsApp user syncs with their own Google Calendar

### Why This Matters

Right now, all users would share one Google Calendar (privacy issue). Production needs per-user OAuth where each person authorizes their own calendar.

### Implementation Plan

**1. OAuth Flow Integration** (~2 hours)
- Add `/auth/google` endpoint to initiate user authorization
- Generate unique authorization URLs per user
- Handle OAuth callback and token exchange
- Send authorization link via WhatsApp on first reminder

**2. Token Storage** (~1 hour)
- Store user tokens in Cloud Storage: `gs://bucket/user_tokens/{user_id}_token.json`
- Implement token refresh logic with expiry handling
- Graceful degradation if user hasn't authorized

**3. Secret Management** (~1 hour)
- Move `credentials.json` to Google Secret Manager
- Configure Cloud Run to access secrets
- Remove credentials from container image

**4. Calendar Service Updates** (~2 hours)
- Modify `get_calendar_service(user_id)` to load user-specific tokens
- Update all calendar functions to accept `user_id`
- Add error handling for missing/expired tokens

**5. UX Flow** (~1 hour)
```
User: "remind me to call mom tomorrow"
Agent: "To sync with your Google Calendar, please authorize:
       https://ai-task-agent-xxx.run.app/auth/google?user_id=abc123"
[User clicks, authorizes]
Agent: "✅ Calendar connected! Creating reminder..."
```

**Timeline**: 6-8 hours of focused development
**Benefits**: True multi-tenant support, production-ready OAuth, showcase architectural evolution

---

## 📁 Project Structure

```
my-agent/
├── agent/
│   ├── graph.py              # LangGraph workflow definition
│   ├── nodes.py              # Agent & tools nodes
│   ├── state.py              # State schema (messages, user_id)
│   └── prompts.py            # System prompts
├── api/
│   ├── main.py               # FastAPI app entry point
│   ├── routes/
│   │   ├── whatsapp.py       # Webhook endpoints
│   │   └── health.py         # Health check
│   ├── services/
│   │   └── message_handler.py # Async message processing
│   └── schemas/
│       └── whatsapp.py       # Pydantic models
├── database/
│   ├── models.py             # SQLite schema
│   ├── repository.py         # Data access layer
│   └── cloud_storage.py      # GCS sync utilities
├── tools/
│   ├── tasks.py              # Task CRUD tools
│   ├── google_calendar.py    # Calendar integration
│   └── __init__.py
├── utils/
│   └── date_parser.py        # Natural language date parsing
├── config/
│   └── settings.py           # Environment config
├── tests/                    # 50 tests, 64% coverage
├── docs/                     # Setup guides
├── app.py                    # CLI entry point
├── deploy.sh                 # Cloud Run deployment script
├── Dockerfile                # Multi-stage build
└── requirements.txt          # Dependencies
```

---

## 🎤 Interview Talking Points

**Architecture & Design**
- **"Why LangGraph over pure LLM calls?"** → State persistence, checkpointing for conversation memory, built-in tool calling, conditional routing
- **"Explain the ReAct pattern"** → Reasoning (LLM thinks) → Acting (execute tools) → Observation (tool results) → repeat until done
- **"How does Cloud Run handle statelessness?"** → Databases synced to Cloud Storage on startup/shutdown, ephemeral containers

**Production Considerations**
- **"How do you handle Cloud Run cold starts?"** → First message gets "Working on it" acknowledgment within 100ms, then full response after agent processing
- **"What's your security model?"** → Webhook signature verification (HMAC-SHA1), rate limiting (10/min), API key in env vars, phone number hashing
- **"How would you scale this?"** → Horizontal scaling (Cloud Run auto-scales), database connection pooling, async processing, queue for high load

**OAuth & Calendar Integration**
- **"Why not implement per-user OAuth yet?"** → MVP prioritization - focused on core agent + deployment first. Calendar works locally for demos. Phase 2 adds multi-tenant OAuth.
- **"Explain OAuth 2.0 flow"** → Authorization code flow: redirect to Google → user consents → callback with code → exchange for tokens → store refresh token
- **"How do you handle token expiry?"** → Refresh tokens automatically refresh access tokens when expired, graceful degradation if refresh fails

**Technical Decisions**
- **"Why SQLite instead of PostgreSQL?"** → Simple MVP, <10K users, Cloud Storage sync works well, easy migration path to Cloud SQL later
- **"Why Twilio sandbox vs WhatsApp Business API?"** → Faster iteration (5 min setup vs 2 week approval), free for demo, production would use Business API
- **"How do you test agent behavior?"** → Mock LLM responses for deterministic tests, integration tests with real LangGraph, LangSmith for production tracing

---

## 📖 Additional Documentation

- **[Google Calendar Setup](docs/GOOGLE_CALENDAR_SETUP.md)** - OAuth 2.0 configuration guide
- **[Deployment Guide](docs/GCP_DEPLOYMENT.md)** - Step-by-step Cloud Run deployment (if exists)
- **[Monitoring Guide](docs/MONITORING_GUIDE.md)** - LangSmith setup and best practices

---

## 🙏 Credits

Built by **Renato Boemer** as a portfolio project to demonstrate AI engineering skills.

- **GitHub**: [@boemer00](https://github.com/boemer00)
- **LinkedIn**: [Renato Boemer](https://linkedin.com/in/renatoboemer)

**Technologies**: LangGraph, LangChain, FastAPI, Google Cloud Run, Twilio, OpenAI

---

**Questions?** Check the [LangGraph docs](https://langchain-ai.github.io/langgraph/) or open an issue!
