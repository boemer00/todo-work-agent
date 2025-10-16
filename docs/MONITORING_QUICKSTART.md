# LangSmith Monitoring - Quick Start Guide

## ⚡ TL;DR

```bash
# 1. Verify tracing works
python monitoring/verify_tracing.py

# 2. Run your agent
python app.py

# 3. Check traces at
https://eu.smith.langchain.com
```

---

## 🎯 What Is This?

Your Todo Agent now has **automatic tracing** with LangSmith. Every LLM call and tool execution is logged for:
- Debugging
- Performance monitoring
- Quality measurement
- Cost tracking

## ✅ Is Tracing Working?

Run the verification script:

```bash
python monitoring/verify_tracing.py
```

You should see:
```
✅ LLM Response: LangSmith tracing is working!

🎉 SUCCESS! Tracing should be working.
```

Then:
1. Go to https://eu.smith.langchain.com
2. Click on Projects → "my-todo-agent"
3. You should see a NEW trace!

---

## 🔍 How It Works

### The Magic: Environment Variables

LangSmith tracing is **automatic** when these env vars are set:

```bash
# Your .env file
LANGSMITH_API_KEY="lsv2_pt_..."
LANGSMITH_TRACING=true
LANGSMITH_PROJECT="my-todo-agent"
LANGSMITH_ENDPOINT="https://eu.api.smith.langchain.com"
```

### The Critical Detail: Import Order

**This code loads env vars BEFORE any LangChain imports:**

```python
# app.py (lines 18-37)
from dotenv import load_dotenv
load_dotenv()  # ← FIRST!

from monitoring import setup_langsmith
setup_langsmith()  # ← SECOND!

from langchain_core.messages import HumanMessage  # ← THIRD!
from agent.graph import create_graph  # ← FOURTH!
```

If you import LangChain components BEFORE loading `.env`, tracing won't work!

---

## 🚀 Using Tracing

### 1. Run Your Agent

```bash
python app.py
```

You'll see:
```
✓ LangSmith tracing enabled
  Project: my-todo-agent
  API Endpoint: https://eu.api.smith.langchain.com
  View traces: https://eu.smith.langchain.com

  💡 After running the agent, check for traces at:
     https://eu.smith.langchain.com → Projects → 'my-todo-agent'
```

### 2. Interact with the Agent

```
You: add task: buy milk
🤖 Agent: ✓ Added task #1: 'buy milk'

You: what are my tasks?
🤖 Agent: Your tasks:
1. buy milk
```

### 3. View Traces in LangSmith

Go to https://eu.smith.langchain.com and you'll see:

**Trace Example:**
```
Run: RunnableSequence (2.5s)
├─ ChatOpenAI (1.2s)
│  ├─ Input: [HumanMessage(content="add task: buy milk")]
│  ├─ Output: AIMessage(tool_calls=[...])
│  ├─ Tokens: 150 input, 30 output
│  └─ Cost: $0.0015
├─ ToolCall: add_task (0.05s)
│  ├─ Input: {"task": "buy milk", "user_id": "renatoboemer"}
│  └─ Output: "✓ Added task #1: 'buy milk'"
└─ ChatOpenAI (1.1s)
   ├─ Input: [..., ToolMessage(content="✓ Added task #1...")]
   └─ Output: AIMessage(content="I've added 'buy milk'...")
```

---

## 📊 What You Can See

### For Each Trace:
- **LLM Calls**: Model, tokens, latency, cost
- **Tool Executions**: Which tool, arguments, results, duration
- **Agent Flow**: Complete decision tree
- **Errors**: Full stack traces with context
- **Metadata**: User ID, session ID, agent version

### Filtering:
- By user: `metadata.user_id = "alice"`
- By session: `metadata.thread_id = "alice_session_123"`
- By date range
- By error status

---

## 🐛 Troubleshooting

### "I don't see any traces!"

**Check 1: Environment variables loaded?**
```bash
python monitoring/verify_tracing.py
```

**Check 2: Correct LangSmith region?**
Your `.env` has:
```
LANGSMITH_ENDPOINT="https://eu.api.smith.langchain.com"
```

So view traces at: **https://eu.smith.langchain.com** (not .com)

**Check 3: API key valid?**
```bash
# Should see your key (first 20 chars)
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('LANGSMITH_API_KEY')[:20])"
```

**Check 4: Import order correct?**
Ensure `app.py` loads `.env` at the very top (before any LangChain imports)

### "Traces appear but no metadata!"

Metadata is added in `app.py` via the `config` dict:
```python
config["metadata"] = add_metadata(user_id, thread_id, "interactive")
```

Check that this runs before `graph.invoke(state, config)`

### "Can I disable tracing?"

Yes! Just set in `.env`:
```bash
LANGSMITH_TRACING=false
```

---

## 💡 Pro Tips

### Tip 1: Use Meaningful Thread IDs
```python
# Good: Resumable sessions
thread_id = "alice_session_20250115"

# Bad: Always unique (can't resume)
thread_id = f"session_{random.randint(0, 1000000)}"
```

### Tip 2: Add Custom Metadata
```python
metadata = add_metadata(
    user_id=user_id,
    thread_id=thread_id,
    session_type="interactive",
    additional_metadata={
        "deployment": "staging",
        "feature_flag": "new_ui"
    }
)
```

### Tip 3: Monitor Costs
In LangSmith, filter by date range and check:
- Total tokens used
- Cost per request
- Most expensive operations

### Tip 4: Create Datasets from Traces
Find good/bad examples → Save to dataset → Use for evaluation

---

## 🎓 Next Steps

1. **Run the agent and generate traces**
   ```bash
   python app.py
   ```

2. **Explore traces in LangSmith**
   - Click on individual traces
   - View timing breakdown
   - Check token usage

3. **Create an evaluation dataset**
   ```bash
   python monitoring/example_evaluation.py
   ```

4. **Set up alerts** (future)
   - Alert on high error rates
   - Alert on high latency
   - Alert on high costs

---

## 📚 Resources

- **LangSmith Docs**: https://docs.smith.langchain.com
- **Tracing Guide**: https://docs.smith.langchain.com/tracing
- **EU Instance**: https://eu.smith.langchain.com

---

## ✨ Summary

You now have:
- ✅ Automatic tracing of ALL LLM/tool calls
- ✅ EU-region LangSmith instance configured
- ✅ Verification script to test tracing
- ✅ Metadata for filtering traces
- ✅ Cost and performance visibility

**The key insight**: LangSmith tracing is automatic via environment variables, but they must be loaded BEFORE importing LangChain components!

Happy tracing! 🚀
