# Monitoring & Observability

This directory provides **LangSmith observability** for the Todo Agent.

## 🎯 What We Track

### 1. **Automatic Tracing** (LangSmith built-in)
- **LLM calls**: Model, tokens, latency, cost
- **Tool executions**: Which tools, arguments, results, duration
- **Agent decisions**: What the agent decided to do at each step
- **Errors**: Stack traces, error messages, context

### 2. **Custom Metadata** (Our additions)
- User ID (who's using the agent)
- Thread ID (conversation tracking)
- Session type (interactive, API, test)
- Agent version

### 3. **Quality Metrics** (Evaluators)
- Tool selection accuracy (did agent pick right tool?)
- Response quality (helpful, concise, accurate?)
- Task completion (was the task actually done?)

### 4. **Performance Metrics** (Custom tracking)
- Tool usage patterns
- Response times (avg, min, max)
- Error rates and types
- Session counts

---

## 📁 File Structure

```
monitoring/
├── __init__.py           # Package exports
├── langsmith_config.py   # LangSmith setup & metadata
├── evaluators.py         # Quality evaluation functions
├── metrics.py            # Custom metrics tracking
└── README.md            # This file
```

---

## 🚀 Quick Start

### 1. Setup LangSmith

Ensure your `.env` has:
```bash
LANGSMITH_API_KEY="your_api_key_here"
LANGSMITH_PROJECT="my-todo-agent"
LANGSMITH_TRACING_V2=true
```

### 2. Initialize in Your App

```python
from monitoring import setup_langsmith, add_metadata

# Enable tracing
setup_langsmith()

# Add metadata to traces
metadata = add_metadata(
    user_id="alice",
    thread_id="alice_session_123",
    session_type="interactive"
)
```

### 3. Run Your Agent

Traces automatically appear in LangSmith! 🎉

View them at: https://smith.langchain.com

---

## 📊 What You'll See in LangSmith

### Trace View
```
Run: User adds a task
├─ Agent Node (LLM call)
│  ├─ Model: gpt-4o-mini
│  ├─ Tokens: 150 input, 50 output
│  ├─ Latency: 450ms
│  └─ Decision: Call add_task tool
├─ Tool: add_task
│  ├─ Input: {"task": "buy milk", "user_id": "alice"}
│  ├─ Duration: 15ms
│  └─ Output: "✓ Added task #1: 'buy milk'"
└─ Agent Node (LLM call)
   ├─ Model: gpt-4o-mini
   ├─ Tokens: 180 input, 40 output
   ├─ Latency: 420ms
   └─ Response: "I've added 'buy milk' to your tasks!"
```

### Metadata (Filterable)
- User: alice
- Thread: alice_session_123
- Session Type: interactive
- Agent: todo_assistant v1.0.0

---

## 🧪 Evaluation (Testing Agent Quality)

### Create Test Dataset

```python
from langsmith import Client

client = Client()

# Create dataset
dataset = client.create_dataset("todo_agent_tests")

# Add test cases
client.create_example(
    dataset_id=dataset.id,
    inputs={"message": "add task: buy milk"},
    outputs={"expected_tool": "add_task", "expected_outcome": "task_added"}
)

client.create_example(
    dataset_id=dataset.id,
    inputs={"message": "what are my tasks?"},
    outputs={"expected_tool": "list_tasks", "expected_outcome": "tasks_listed"}
)
```

### Run Evaluation

```python
from langsmith.evaluation import evaluate
from monitoring import (
    evaluate_tool_selection,
    evaluate_response_quality,
    evaluate_task_completion
)

results = evaluate(
    lambda inputs: run_agent(inputs["message"]),
    data="todo_agent_tests",  # Dataset name
    evaluators=[
        lambda run, example: evaluate_tool_selection(
            run.outputs, example.outputs["expected_tool"]
        ),
        lambda run, example: evaluate_response_quality(run.outputs, "helpful"),
        lambda run, example: evaluate_task_completion(
            run.outputs, example.outputs["expected_outcome"]
        )
    ]
)

# View results in LangSmith UI
print(f"Accuracy: {results['tool_selection_accuracy']}")
```

---

## 📈 Custom Metrics

Track additional metrics beyond LangSmith:

```python
from monitoring.metrics import get_metrics

metrics = get_metrics()

# Track tool usage
metrics.track_tool_call("add_task")

# Track errors
metrics.track_error("ValueError", "Invalid task number", {"user": "alice"})

# Track response time
metrics.track_response_time(450.5)  # milliseconds

# Print summary
metrics.print_summary()
```

Output:
```
============================================================
📊 AGENT METRICS SUMMARY
============================================================
Total Sessions: 5

Tool Usage:
  • add_task: 12 calls
  • list_tasks: 8 calls
  • mark_task_done: 5 calls

Performance:
  • Avg Response Time: 485.32ms
  • Min Response Time: 320.0ms
  • Max Response Time: 750.0ms

Errors: 2
============================================================
```

---

## 🎓 What This Teaches You

For AI engineering job interviews, you can discuss:

1. **Observability Strategy**
   - "I implemented comprehensive tracing with LangSmith"
   - "Every LLM call and tool execution is automatically traced"
   - "We can debug production issues by replaying exact traces"

2. **Evaluation Framework**
   - "I created custom evaluators to measure agent quality"
   - "We test tool selection accuracy, response quality, task completion"
   - "Automated evaluation runs on every deployment"

3. **Production Monitoring**
   - "I track performance metrics: latency, tool usage, error rates"
   - "Metadata tagging enables filtering by user, session, version"
   - "We can identify performance regressions quickly"

4. **Cost & Performance**
   - "Token usage tracking helps optimize costs"
   - "Latency monitoring ensures good user experience"
   - "Tool usage patterns inform optimization priorities"

---

## 🔍 Key Metrics to Monitor

| Metric | What It Tells You | Good Target |
|--------|-------------------|-------------|
| **Token Usage** | Cost per request | < 500 tokens/request |
| **Latency** | User experience | < 2s total |
| **Tool Calls** | Agent efficiency | 1-2 tools/request |
| **Error Rate** | Reliability | < 1% |
| **Tool Accuracy** | Agent intelligence | > 95% |
| **Response Quality** | User satisfaction | > 4/5 rating |

---

## 📚 Next Steps

1. **Enable tracing**: Update `app.py` to call `setup_langsmith()`
2. **Add metadata**: Include user/thread info in every run
3. **Create test dataset**: Build 10-20 test cases
4. **Run evaluation**: Measure baseline quality
5. **Monitor production**: Track metrics over time

---

## 🔗 Resources

- [LangSmith Documentation](https://docs.smith.langchain.com/)
- [LangSmith Evaluation Guide](https://docs.smith.langchain.com/evaluation)
- [LangSmith Tracing](https://docs.smith.langchain.com/tracing)

---

**Pro Tip**: In job interviews, pull up your LangSmith dashboard and show:
- Real traces from your agent
- Evaluation results with scores
- Performance metrics over time

This demonstrates you understand production AI systems! 🚀
