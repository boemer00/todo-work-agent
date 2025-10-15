"""
Example: How to evaluate your agent with LangSmith.

This demonstrates:
1. Creating a test dataset
2. Running evaluations
3. Measuring agent quality

Run this after you've used the agent a few times so LangSmith has traces.
"""

from langsmith import Client
from langsmith.evaluation import evaluate
from monitoring import (
    evaluate_tool_selection,
    evaluate_response_quality,
    evaluate_task_completion
)


def create_test_dataset():
    """
    Create a dataset with test cases for the Todo Agent.

    This dataset will be used to evaluate agent quality.
    """
    client = Client()

    # Create dataset (only once)
    try:
        dataset = client.create_dataset(
            dataset_name="todo_agent_test_suite",
            description="Test cases for Todo Agent evaluation"
        )
        print(f"✓ Created dataset: {dataset.name}")
    except Exception as e:
        print(f"Dataset might already exist: {e}")
        # Get existing dataset
        dataset = client.read_dataset(dataset_name="todo_agent_test_suite")
        print(f"✓ Using existing dataset: {dataset.name}")

    # Add test examples
    test_cases = [
        {
            "inputs": {
                "message": "add task: buy milk",
                "user_id": "test_user"
            },
            "outputs": {
                "expected_tool": "add_task",
                "expected_outcome": "task_added"
            },
            "metadata": {
                "test_type": "tool_selection",
                "description": "Should call add_task tool"
            }
        },
        {
            "inputs": {
                "message": "what are my tasks?",
                "user_id": "test_user"
            },
            "outputs": {
                "expected_tool": "list_tasks",
                "expected_outcome": "tasks_listed"
            },
            "metadata": {
                "test_type": "tool_selection",
                "description": "Should call list_tasks tool"
            }
        },
        {
            "inputs": {
                "message": "mark task 1 as done",
                "user_id": "test_user"
            },
            "outputs": {
                "expected_tool": "mark_task_done",
                "expected_outcome": "task_marked_done"
            },
            "metadata": {
                "test_type": "tool_selection",
                "description": "Should call mark_task_done tool"
            }
        },
        {
            "inputs": {
                "message": "clear all my tasks",
                "user_id": "test_user"
            },
            "outputs": {
                "expected_tool": "clear_all_tasks",
                "expected_outcome": "tasks_cleared"
            },
            "metadata": {
                "test_type": "tool_selection",
                "description": "Should call clear_all_tasks tool"
            }
        },
        {
            "inputs": {
                "message": "add buy groceries and walk the dog",
                "user_id": "test_user"
            },
            "outputs": {
                "expected_tool": "add_task",
                "expected_outcome": "task_added"
            },
            "metadata": {
                "test_type": "complex_request",
                "description": "Should handle multiple tasks in one request"
            }
        },
    ]

    # Add examples to dataset
    for test_case in test_cases:
        try:
            client.create_example(
                dataset_id=dataset.id,
                inputs=test_case["inputs"],
                outputs=test_case["outputs"],
                metadata=test_case["metadata"]
            )
            print(f"  + Added: {test_case['metadata']['description']}")
        except Exception as e:
            print(f"  - Example might already exist: {test_case['metadata']['description']}")

    print(f"\n✓ Dataset ready with {len(test_cases)} test cases")
    return dataset.name


def run_evaluation():
    """
    Run evaluation on the test dataset.

    This will:
    1. Run your agent on each test case
    2. Apply evaluators to measure quality
    3. Show results in LangSmith UI
    """
    from agent.graph import create_graph
    from langchain_core.messages import HumanMessage

    # Create agent
    graph = create_graph()

    # Define how to run agent on test inputs
    def run_agent_on_test(inputs: dict) -> dict:
        """Run agent and return outputs for evaluation."""
        state = {
            "messages": [HumanMessage(content=inputs["message"])],
            "user_id": inputs["user_id"]
        }

        config = {
            "configurable": {
                "thread_id": f"test_{inputs['user_id']}_eval"
            }
        }

        result = graph.invoke(state, config)
        return {"messages": result["messages"]}

    # Create evaluators
    def tool_selection_evaluator(run, example):
        expected_tool = example.outputs["expected_tool"]
        return evaluate_tool_selection(run.outputs, expected_tool)

    def response_quality_evaluator(run, example):
        return evaluate_response_quality(run.outputs, "helpful")

    def task_completion_evaluator(run, example):
        expected_outcome = example.outputs["expected_outcome"]
        return evaluate_task_completion(run.outputs, expected_outcome)

    # Run evaluation
    print("\n🔍 Running evaluation...")
    print("This will take a minute...\n")

    results = evaluate(
        run_agent_on_test,
        data="todo_agent_test_suite",
        evaluators=[
            tool_selection_evaluator,
            response_quality_evaluator,
            task_completion_evaluator
        ],
        experiment_prefix="todo_agent_eval"
    )

    print("\n✓ Evaluation complete!")
    print(f"View detailed results in LangSmith: {results.experiment_url}")

    # Print summary
    print("\n" + "="*60)
    print("📊 EVALUATION RESULTS")
    print("="*60)

    # Note: results object structure may vary
    # Access aggregated metrics if available
    try:
        print(f"Tool Selection Accuracy: {results['tool_selection_accuracy']:.1%}")
        print(f"Response Quality: {results['response_helpful']:.1%}")
        print(f"Task Completion: {results['task_completion']:.1%}")
    except:
        print("Check LangSmith UI for detailed results")

    print("="*60)

    return results


def main():
    """
    Main function to set up and run evaluation.

    Usage:
        python monitoring/example_evaluation.py
    """
    print("="*60)
    print("🧪 LangSmith Evaluation Example")
    print("="*60)

    # Step 1: Create test dataset
    print("\n[1/2] Creating test dataset...")
    dataset_name = create_test_dataset()

    # Step 2: Run evaluation
    print("\n[2/2] Running evaluation...")
    results = run_evaluation()

    print("\n✅ Done! Check LangSmith for full results.")
    print("   https://smith.langchain.com")


if __name__ == "__main__":
    main()
