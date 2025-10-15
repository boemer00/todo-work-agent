# To-Do Agent - LangGraph Tutorial

A complete, beginner-friendly tutorial on building a To-Do agent with LangGraph.

## 🎯 What You'll Learn

- The fundamental concepts of LangGraph (State, Nodes, Edges, Graph)
- How to build an agent that can use tools
- The ReAct pattern (Reasoning + Acting)
- How to create multi-step, intelligent agents
- Best practices for agent architecture

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

Make sure your `.env` file has your OpenAI API key:

```bash
OPENAI_API_KEY=your_key_here
```

### 3. Run the Agent

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

```
============================================================
🤖 To-Do Agent with Persistence
============================================================

✓ User: renatoboemer
✓ Session ID: renatoboemer_session_1760452854

Commands:
  - Type your message to interact with the agent
  - Type 'quit', 'exit', or 'q' to exit
============================================================

You: add gym to my list

🤖 Agent: I've added "gym" to your task list!

You: what are my tasks?

🤖 Agent: Here are your tasks:
1. Buy groceries
2. Write LangGraph tutorial
3. gym

You: mark task 3 as done

🤖 Agent: Task #3 "gym" has been marked as complete!
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

- `add_task(task: str, user_id: str)` - Add a new task
- `list_tasks(user_id: str)` - Show all tasks for the user
- `mark_task_done(task_number: int, user_id: str)` - Mark a task complete
- `clear_all_tasks(user_id: str)` - Clear all tasks

**Features:**
- SQLite database for persistent task storage
- Multi-user support (tasks are isolated per user)
- LangGraph checkpointing for conversation memory

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
- **Draw your graph first**, then code it

---

**Happy building! 🚀**

Questions? Check out the course materials or LangGraph docs.
