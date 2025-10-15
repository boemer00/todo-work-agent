"""
Evaluation functions for measuring agent quality.

These evaluators help you:
1. Test if the agent makes correct decisions
2. Measure response quality
3. Track task completion accuracy

Use with LangSmith to automatically evaluate your agent on test datasets.
"""

from typing import Dict, Any


def evaluate_tool_selection(run_output: Dict[str, Any], expected_tool: str) -> Dict[str, Any]:
    """
    Evaluate if the agent selected the correct tool.

    Use this to test if the agent understands when to use each tool.

    Args:
        run_output: The agent's output from LangSmith
        expected_tool: The tool that should have been called

    Returns:
        Evaluation result with score and reasoning

    Example:
        Input: "add task: buy milk"
        Expected: agent should call add_task tool
    """
    # Extract tool calls from the agent's output
    messages = run_output.get("messages", [])

    # Find if any message has tool_calls
    tool_called = None
    for msg in messages:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            tool_called = msg.tool_calls[0]["name"]
            break

    # Evaluate
    correct = tool_called == expected_tool
    score = 1.0 if correct else 0.0

    return {
        "key": "tool_selection_accuracy",
        "score": score,
        "reasoning": f"Expected '{expected_tool}', got '{tool_called}'",
    }


def evaluate_response_quality(run_output: Dict[str, Any], criteria: str = "helpful") -> Dict[str, Any]:
    """
    Evaluate the quality of the agent's response.

    Criteria can be:
    - "helpful": Was the response helpful to the user?
    - "concise": Was the response concise and clear?
    - "accurate": Did the agent accurately report the action taken?

    Args:
        run_output: The agent's output from LangSmith
        criteria: What aspect to evaluate

    Returns:
        Evaluation result with score and reasoning

    Note:
        In production, you'd use an LLM-as-judge here.
        For simplicity, we'll do basic checks.
    """
    messages = run_output.get("messages", [])

    if not messages:
        return {
            "key": f"response_{criteria}",
            "score": 0.0,
            "reasoning": "No response found"
        }

    last_message = messages[-1]
    content = last_message.content if hasattr(last_message, "content") else ""

    # Simple heuristics (in production, use LLM-as-judge)
    score = 0.5  # Default neutral score
    reasoning = f"Response: {content[:100]}..."

    if criteria == "helpful":
        # Check if response contains success indicators
        if any(indicator in content.lower() for indicator in ["✓", "added", "marked", "cleared"]):
            score = 1.0
            reasoning = "Response indicates successful action"

    elif criteria == "concise":
        # Check if response is not too long (< 200 chars)
        if len(content) < 200:
            score = 1.0
            reasoning = f"Response is concise ({len(content)} chars)"
        else:
            score = 0.5
            reasoning = f"Response is verbose ({len(content)} chars)"

    return {
        "key": f"response_{criteria}",
        "score": score,
        "reasoning": reasoning
    }


def evaluate_task_completion(
    run_output: Dict[str, Any],
    expected_outcome: str
) -> Dict[str, Any]:
    """
    Evaluate if the agent completed the task correctly.

    Use this for end-to-end testing of agent behavior.

    Args:
        run_output: The agent's output from LangSmith
        expected_outcome: What should have happened (e.g., "task_added")

    Returns:
        Evaluation result with score and reasoning

    Example:
        User: "add buy milk"
        Expected outcome: "task_added"
        Check: Did the database show a new task?
    """
    # This is a placeholder - in reality, you'd check the database
    # or verify the actual state change

    messages = run_output.get("messages", [])

    # Simple check: look for success indicators in tool messages
    task_completed = False
    for msg in messages:
        if hasattr(msg, "content"):
            content = str(msg.content).lower()
            if expected_outcome == "task_added" and "added task" in content:
                task_completed = True
            elif expected_outcome == "task_marked_done" and "marked task" in content:
                task_completed = True
            elif expected_outcome == "tasks_listed" and "your tasks" in content:
                task_completed = True

    score = 1.0 if task_completed else 0.0

    return {
        "key": "task_completion",
        "score": score,
        "reasoning": f"Expected '{expected_outcome}', task_completed={task_completed}"
    }


# Example: How to use these evaluators with LangSmith
"""
from langsmith import Client

client = Client()

# Create a dataset
dataset = client.create_dataset("todo_agent_tests")

# Add examples
client.create_example(
    dataset_id=dataset.id,
    inputs={"messages": [{"role": "user", "content": "add task: buy milk"}]},
    outputs={"expected_tool": "add_task", "expected_outcome": "task_added"}
)

# Run evaluation
from langsmith.evaluation import evaluate

results = evaluate(
    lambda inputs: run_agent(inputs),  # Your agent function
    data=dataset,
    evaluators=[
        lambda run, example: evaluate_tool_selection(run.outputs, example.outputs["expected_tool"]),
        lambda run, example: evaluate_response_quality(run.outputs, "helpful"),
        lambda run, example: evaluate_task_completion(run.outputs, example.outputs["expected_outcome"])
    ]
)
"""
