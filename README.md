# To-Do Agent - LangGraph Tutorial

A complete, beginner-friendly tutorial on building a To-Do agent with LangGraph.

## 🎯 What You'll Learn

- The fundamental concepts of LangGraph (State, Nodes, Edges, Graph)
- How to build an agent that can use tools
- The ReAct pattern (Reasoning + Acting)
- How to create multi-step, intelligent agents
- Best practices for agent architecture

## 📁 Files in This Project

- **`todo_agent.py`** - The complete agent implementation with detailed comments
- **`TUTORIAL.md`** - Step-by-step guide explaining concepts and mindset
- **`ARCHITECTURE.md`** - Visual diagrams and architecture deep-dive
- **`test_agent.py`** - Test script to see the agent in action
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

**Interactive mode:**
```bash
python todo_agent.py
```

**Test mode:**
```bash
python test_agent.py
```

## 💬 Example Interactions

```
You: Add a task to buy milk
🤖 Agent: I've added "buy milk" to your tasks!

You: What are my current tasks?
🤖 Agent: Your tasks:
1. Buy groceries
2. Write LangGraph tutorial
3. Go to gym

You: Mark task 2 as done
🤖 Agent: Task #2 has been marked as done!
```

## 📚 Learning Path

**Start here:**
1. Read [TUTORIAL.md](TUTORIAL.md) - Understand the concepts
2. Read [todo_agent.py](todo_agent.py) - See the implementation
3. Run `python test_agent.py` - See it working
4. Read [ARCHITECTURE.md](ARCHITECTURE.md) - Deep dive into flow

**Then experiment:**
- Add a new tool (e.g., `edit_task`, `search_tasks`)
- Modify the state to track task completion
- Add persistent storage (SQLite)
- Implement memory across sessions

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

- `add_task(task: str)` - Add a new task
- `list_tasks()` - Show all tasks
- `mark_task_done(task_number: int)` - Mark a task complete
- `clear_all_tasks()` - Clear all tasks

**Note:** Currently using mock implementations. You can extend these to use a real database.

## 🚧 Extending the Agent

### Add Persistent Storage

Replace mock functions with database calls:

```python
import sqlite3

def add_task(task: str) -> str:
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (task, done) VALUES (?, ?)",
                   (task, False))
    conn.commit()
    conn.close()
    return f"✓ Added task: '{task}'"
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

### Add Conversation Memory

Use LangGraph's checkpointing:

```python
from langgraph.checkpoint.sqlite import SqliteSaver

memory = SqliteSaver.from_conn_string("checkpoints.db")
graph = workflow.compile(checkpointer=memory)

# Use thread_id to persist conversations
config = {"configurable": {"thread_id": "user_123"}}
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
