"""
Quick verification script to test LangSmith tracing.

This script:
1. Loads environment variables
2. Makes a simple LLM call
3. Verifies tracing is working

Run this to confirm LangSmith is properly configured:
    python monitoring/verify_tracing.py
"""

import os
import sys

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Check if LangSmith is configured
api_key = os.getenv("LANGSMITH_API_KEY")
if not api_key:
    print("❌ LANGSMITH_API_KEY not found in .env")
    print("   Please add it to your .env file")
    sys.exit(1)

# Set tracing environment variables
os.environ["LANGSMITH_TRACING_V2"] = "true"
if not os.getenv("LANGSMITH_PROJECT"):
    os.environ["LANGSMITH_PROJECT"] = "my-todo-agent"

project = os.getenv("LANGSMITH_PROJECT")
endpoint = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")

print("="*60)
print("🧪 LangSmith Tracing Verification")
print("="*60)
print(f"✓ LANGSMITH_API_KEY: {api_key[:20]}...")
print(f"✓ LANGSMITH_PROJECT: {project}")
print(f"✓ LANGSMITH_ENDPOINT: {endpoint}")
print(f"✓ LANGSMITH_TRACING_V2: {os.getenv('LANGSMITH_TRACING_V2')}")
print()

# Import LangChain components AFTER environment is configured
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

print("📡 Making test LLM call...")
print("   This should create a trace in LangSmith")
print()

try:
    # Create LLM and make a simple call
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    response = llm.invoke([
        HumanMessage(content="Say exactly: 'LangSmith tracing is working!'")
    ])

    print(f"✅ LLM Response: {response.content}")
    print()

    # Determine UI URL
    if "eu.api.smith.langchain.com" in endpoint:
        ui_url = "https://eu.smith.langchain.com"
    else:
        ui_url = "https://smith.langchain.com"

    print("="*60)
    print("🎉 SUCCESS! Tracing should be working.")
    print("="*60)
    print()
    print("Next steps:")
    print(f"1. Go to {ui_url}")
    print(f"2. Navigate to Projects → '{project}'")
    print("3. You should see a new trace from this test!")
    print("4. Look for a run with input: 'Say exactly: LangSmith...'")
    print()
    print("If you see the trace, LangSmith is working correctly! 🚀")
    print()

except Exception as e:
    print(f"❌ Error: {e}")
    print()
    print("Troubleshooting:")
    print("1. Check your LANGSMITH_API_KEY is valid")
    print("2. Verify you have network access to LangSmith")
    print("3. Make sure you have the langsmith package installed:")
    print("   pip install langsmith")
    sys.exit(1)
