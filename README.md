# 📅 To-Do Agent with Google Calendar Integration

An intelligent to-do list assistant powered by LangGraph and integrated with Google Calendar. This project demonstrates production-ready AI agent development, including natural language processing, external API integration, and conversational AI design.

##⭐ Key Features

- **Natural Language Understanding** - "Remind me to call Gabi tomorrow at 10am" → automatic parsing and scheduling
- **Google Calendar Integration** - Seamless OAuth 2.0 authentication and event synchronization
- **Smart Conversational Flow** - Agent asks about scheduling preferences and respects user choices
- **Multi-User Support** - Isolated task lists per user with persistent storage
- **Production Patterns** - LangGraph checkpointing, LangSmith observability, graceful error handling
- **Timezone Aware** - Proper handling of timezones for distributed users

## 🎯 Portfolio Highlights

This project showcases skills relevant to AI Engineering roles:

1. **LangGraph Mastery** - State management, conditional routing, tool calling
2. **External API Integration** - OAuth 2.0, Google Calendar API, token management
3. **Natural Language Processing** - Date parsing, intent recognition, conversation design
4. **Database Design** - Schema evolution, backwards-compatible migrations
5. **Testing & Quality** - 50 tests, 64% coverage, CI/CD with GitHub Actions
6. **Security Best Practices** - Credential management, gitignore, scope limitation
7. **Production Mindset** - Error handling, logging, observability, documentation

## 📁 Files in This Project

- **`app.py`** - CLI entry point with auto-detection and persistence
- **`agent/`** - Agent implementation (graph, nodes, state, tools)
- **`database/`** - Database utilities and task management
- **`TUTORIAL.md`** - Step-by-step guide explaining concepts and mindset
- **`ARCHITECTURE.md`** - Visual diagrams and architecture deep-dive
- **`requirements.txt`** - Python dependencies

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment

Create a `.env` file with your API keys:

```bash
OPENAI_API_KEY=your_openai_key_here
LANGSMITH_API_KEY=your_langsmith_key_here  # Optional, for observability
```

### 3. (Optional) Set Up Google Calendar

For calendar integration, follow the setup guide:

👉 **[Google Calendar Setup Guide](docs/GOOGLE_CALENDAR_SETUP.md)**

Quick summary:
1. Create Google Cloud project
2. Enable Google Calendar API
3. Download OAuth credentials as `credentials.json`
4. Place in project root

**Note**: The agent works perfectly fine without Google Calendar! It will just skip calendar integration and store tasks locally.

### 4. Run the Agent

**Default mode (auto-detects your username):**
```bash
python app.py
```

**Specify a custom user:**
```bash
python app.py --user alice
```

**View help:**
```bash
python app.py --help
```

## 💬 Example Interactions

### 📅 With Google Calendar Integration

```
============================================================
🤖 To-Do Agent with Google Calendar Integration
============================================================

You: remind me to call Gabi tomorrow at 10am

🤖 Agent: ✓ Reminder set: 'call Gabi' for Tuesday, October 28, 2025 at 10:00 AM
📅 Added to your Google Calendar!

You: add buy milk to my list

🤖 Agent: Would you like me to set a reminder for this? If so, when?

You: yes, tonight at 6pm

🤖 Agent: ✓ Reminder set: 'buy milk' for Monday, October 27, 2025 at 06:00 PM
📅 Added to your Google Calendar!

You: add finish report

🤖 Agent: Would you like me to set a reminder for this? If so, when?

You: no thanks

🤖 Agent: ✓ Added task #3: 'finish report'

You: show my tasks

🤖 Agent: Your tasks:
1. call Gabi (Due: 2025-10-28T10:00:00+00:00)
2. buy milk (Due: 2025-10-27T18:00:00+00:00)
3. finish report

You: mark task 1 as done

🤖 Agent: ✓ Marked task #1 as done: 'call Gabi'
📅 Removed from Google Calendar
```

### 📝 Without Google Calendar (still works!)

```
You: remind me to call dentist tomorrow at 2pm

🤖 Agent: ✓ Task 'call dentist' added locally.
⚠️ Google Calendar not configured. See docs/GOOGLE_CALENDAR_SETUP.md
```

## 🧪 Testing

This project includes a comprehensive test suite to ensure reliability and demonstrate production-ready code.

### Run Tests

**Basic test run:**
```bash
pytest
```

**With coverage report:**
```bash
pytest --cov
```

**Run specific test categories:**
```bash
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
```

### Test Structure

```
tests/
├── conftest.py           # Shared fixtures and test configuration
├── test_database.py      # Database/Repository tests (14 tests)
├── test_date_parser.py   # Date parsing utility tests (13 tests)
├── test_tools.py         # Tool function tests (15 tests)
└── test_agent_flows.py   # Integration tests for agent (8 tests)
```

### Test Coverage

- **50 tests** covering core functionality
- **64% code coverage** on agent, database, tools, and utils modules
- **Mocked external APIs** (Google Calendar, OpenAI) for fast, reliable tests
- **Isolated test databases** using in-memory SQLite
- **Fast test suite** - all tests run in under 3 seconds

### Continuous Integration

Tests run automatically on every push via GitHub Actions:
- Tests on Python 3.9, 3.10, and 3.11
- Coverage reporting
- Automatic test results in pull requests

### Key Testing Patterns

**Fixtures for Test Isolation:**
```python
@pytest.fixture
def task_repo(test_db_path):
    """Provide isolated test database."""
    return TaskRepository(db_path=test_db_path)
```

**Mocking External APIs:**
```python
@pytest.fixture
def mock_google_calendar(mocker):
    """Mock Google Calendar to avoid external calls."""
    mock = mocker.patch('tools.google_calendar.create_calendar_event')
    mock.return_value = "mock_event_id"
    return mock
```

**Time-Based Testing:**
```python
@freeze_time("2025-01-15 10:00:00")
def test_parse_tomorrow():
    """Test with frozen time for predictable results."""
    result = parse_natural_language_date("tomorrow at 10am")
    assert result.day == 16
```

## 📚 Learning Path

**Start here:**
1. Read [TUTORIAL.md](TUTORIAL.md) - Understand the concepts
2. Read [app.py](app.py) and explore `agent/` directory - See the implementation
3. Run `python app.py` - Try it yourself
4. Read [ARCHITECTURE.md](ARCHITECTURE.md) - Deep dive into flow

**Then experiment:**
- Add a new tool (e.g., `edit_task`, `search_tasks`)
- Modify the state to track additional task metadata
- Extend the database schema (SQLite already included!)
- Implement session resumption using thread_id

## 🧠 Core Concepts

### State
The "memory" that flows through your graph. Contains the conversation history and any data that needs to persist.

### Nodes
Functions that process the state. In our agent:
- **Agent Node**: LLM decides what to do
- **Tools Node**: Executes the tools

### Edges
Connections between nodes. Can be:
- **Direct**: Always go to the next node
- **Conditional**: Router decides based on state

### Graph
The compiled workflow that orchestrates everything.

## 🎨 The Agent Pattern

```
START → agent → [decide] → tools → agent → [decide] → END
                   ↓                ↑
                  END ←─────────────┘
```

This is called the **ReAct pattern** (Reasoning + Acting).

## 🔧 Tools Included

- **`create_reminder(task, when, user_id, timezone)`** - Create a scheduled reminder with Google Calendar integration
- **`add_task(task, user_id)`** - Add a simple task without scheduling
- **`list_tasks(user_id)`** - Show all tasks (with due dates if scheduled)
- **`mark_task_done(task_number, user_id)`** - Mark task complete & remove from calendar
- **`clear_all_tasks(user_id)`** - Clear all tasks

**Features:**
- 📅 **Google Calendar Integration** - OAuth 2.0 authentication, automatic event sync
- 🕐 **Natural Language Dates** - Parse "tomorrow at 10am", "next Friday 2pm", "in 3 hours"
- 💾 **SQLite Database** - Persistent task storage with temporal schema
- 👥 **Multi-User Support** - Isolated tasks per user
- 🔄 **LangGraph Checkpointing** - Conversation memory and state persistence
- 📊 **LangSmith Observability** - Real-time tracing and monitoring
- 🌍 **Timezone Aware** - Proper handling of user timezones

## 🚧 Extending the Agent

### Add More Task Metadata

The database schema is in `database/tasks.py`. Extend it:

```python
def create_tasks_table():
    """Create the tasks table with additional fields."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            task TEXT NOT NULL,
            done BOOLEAN DEFAULT 0,
            priority TEXT DEFAULT 'medium',
            due_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
```

### Add More Tools

```python
def edit_task(task_number: int, new_description: str) -> str:
    """Edit an existing task's description."""
    # Implementation here
    return f"✓ Updated task #{task_number}"

# Don't forget to add to tools list!
tools = [add_task, list_tasks, mark_task_done, clear_all_tasks, edit_task]
```

### Resume Previous Conversations

The agent already has checkpointing! To resume a session:

```python
# In app.py, instead of generating a new thread_id:
# thread_id = f"{user_id}_session_{int(time.time())}"

# Use a saved thread_id to resume:
thread_id = "alice_session_1760452854"  # From previous run
config = {"configurable": {"thread_id": thread_id}}
result = graph.invoke(state, config)
```

## 🐛 Troubleshooting

### Agent not calling tools?
- Check that tools are bound to LLM: `llm.bind_tools(tools)`
- Verify tool docstrings are clear
- Try more explicit requests

### ImportError?
- Run `pip install -r requirements.txt`
- Check Python version (3.9+ recommended)

### API errors?
- Verify `.env` file has `OPENAI_API_KEY`
- Check your OpenAI account has credits

## 📖 Additional Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangChain Academy](https://github.com/langchain-ai/langchain-academy)
- Your course modules (`../module-1` through `../module-5`)

## 🎓 Next Steps

After mastering this agent:

1. **Build a different agent** - Try a calculator agent, weather agent, or email agent
2. **Study the course modules** - More advanced patterns in your repo
3. **Add complexity** - Multi-agent systems, long-term memory, human-in-the-loop
4. **Build a real project** - Customer service bot, research assistant, coding helper

## 💡 Key Takeaways

- LangGraph is about **state management** and **flow control**
- Agents are just **graphs** with **LLM-powered routing**
- The **ReAct pattern** (agent ↔ tools loop) is powerful and flexible
- **Start simple**, then add complexity incrementally
- **External integrations** require careful error handling and security practices

## 🎤 Interview Preparation

When discussing this project in interviews, highlight these technical decisions:

### Architecture & Design
- **"Why LangGraph over pure LLM calls?"** - State persistence, checkpointing, complex multi-step flows, built-in tool calling
- **"How does the agent decide which tool to use?"** - LLM tool calling with clear docstrings and examples in system prompt
- **"Explain the ReAct pattern"** - Reasoning (LLM thinks) → Acting (execute tools) → Observation (tool results) → repeat until done

### Database & Schema
- **"How did you handle schema migration?"** - Backwards-compatible ALTER TABLE with NULL defaults, PRAGMA table_info checks
- **"Why store calendar_event_id?"** - Enables bidirectional sync, prevents duplicate events, allows calendar cleanup when tasks complete
- **"Why single table vs normalized schema?"** - YAGNI principle, simpler queries, easier to reason about, can normalize later if needed

### Natural Language Processing
- **"Why dateparser vs asking LLM to parse dates?"** - Deterministic, no hallucinations, < 1ms vs 200ms+, cheaper (no API call)
- **"What edge cases did you handle?"** - Past dates, ambiguous expressions, timezone issues, invalid input, missing date components
- **"How do you handle timezone-aware scheduling?"** - Timezone stored per task, dateparser settings, Python datetime with tzinfo

### Google Calendar Integration
- **"Explain OAuth 2.0 flow"** - Authorization code flow for desktop apps, browser-based consent, token exchange, refresh tokens
- **"How do you secure credentials?"** - .gitignore, environment variables, token.json with pickle, never commit to git
- **"What if Calendar API is down?"** - Graceful degradation, task still created locally, clear error message, try-except blocks
- **"How would you handle rate limiting?"** - Exponential backoff, retry logic, circuit breaker pattern, quota monitoring

### Conversational AI Design
- **"How do you prevent pushy UX?"** - Ask once, respect "no", don't over-prompt, clear opt-out language
- **"How did you design the system prompt?"** - Clear guidelines, examples, decision boundaries, tool usage patterns
- **"What's your testing strategy for LLMs?"** - Unit tests for tools, integration tests for flows, LangSmith evals, human feedback

### Production Considerations
- **"How would you deploy this?"** - Docker container, cloud functions (AWS Lambda, Google Cloud Run), managed services
- **"What about scaling?"** - Stateless tools (horizontal scaling), database pooling, calendar API quotas, LLM rate limits
- **"How do you monitor AI systems?"** - LangSmith tracing, error logging, success rate metrics, latency monitoring
- **"Security best practices?"** - Credential management, scope limitation, input validation, SQL injection prevention, HTTPS

## 🚀 Next Steps for Portfolio

To make this even more impressive:

1. **Add Tests** - pytest for tools, integration tests for agent flows
2. **Web UI** - FastAPI backend + React frontend
3. **Voice Input** - Whisper API for voice-to-text commands
4. **Bidirectional Sync** - Pull events from Calendar into tasks
5. **Recurring Reminders** - Support "every Monday at 9am"
6. **Multi-Calendar** - Support work vs personal calendars
7. **Team Features** - Shared tasks, permissions, collaboration
8. **Mobile App** - React Native or Flutter
9. **Deployment** - Deploy to cloud with CI/CD
10. **Blog Post** - Write about architecture decisions and learnings

---

**Happy building! 🚀**

Built as a portfolio project by [Renato Boemer](https://github.com/boemer00) to demonstrate AI engineering skills.

Questions? Check out the course materials or [LangGraph docs](https://langchain-ai.github.io/langgraph/).
