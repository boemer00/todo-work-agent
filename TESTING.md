# Testing Guide

## Overview

This project includes a comprehensive test suite with **50+ tests** covering database operations, tools, date parsing, and agent flows.

## Quick Start

### Install Test Dependencies

```bash
pip install -r requirements-dev.txt
```

### Run All Tests

```bash
pytest
```

### Run Tests with Coverage

```bash
pytest --cov
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Specific test file
pytest tests/test_database.py

# Specific test function
pytest tests/test_database.py::TestTaskRepository::test_create_task_basic
```

### Generate HTML Coverage Report

```bash
pytest --cov --cov-report=html
open htmlcov/index.html
```

## Test Structure

```
tests/
├── __init__.py              # Package initialization
├── conftest.py              # Shared fixtures and configuration
├── test_database.py         # Database/Repository tests (14 tests)
├── test_date_parser.py      # Date parsing utility tests (13 tests)
├── test_tools.py            # Tool function tests (15 tests)
└── test_agent_flows.py      # Integration tests for agent (8 tests)
```

## Test Coverage

### Current Coverage

- **agent/**: ~80% coverage
- **database/**: ~90% coverage
- **tools/**: ~85% coverage
- **utils/**: ~75% coverage
- **Overall**: ~75% coverage

### What's Tested

**Database Operations:**
- ✅ Task creation (with and without due dates)
- ✅ Task retrieval (filtering, user isolation)
- ✅ Task updates (marking done, calendar sync)
- ✅ Multi-user isolation
- ✅ Schema migration compatibility

**Tool Functions:**
- ✅ add_task - creating tasks
- ✅ list_tasks - retrieving tasks
- ✅ mark_task_done - completing tasks
- ✅ clear_all_tasks - bulk operations
- ✅ create_reminder - scheduling with calendar integration

**Date Parsing:**
- ✅ Natural language parsing ("tomorrow at 10am")
- ✅ Timezone handling
- ✅ Date extraction from text
- ✅ ISO formatting
- ✅ Past date detection

**Agent Flows:**
- ✅ Tool routing decisions
- ✅ Multi-turn conversations
- ✅ State preservation
- ✅ LLM integration (mocked)

## Key Testing Patterns

### 1. Test Isolation with Fixtures

Each test gets a fresh database to avoid interference:

```python
@pytest.fixture
def task_repo(test_db_path):
    """Provide isolated test database."""
    return TaskRepository(db_path=test_db_path)
```

### 2. Mocking External APIs

Avoid real API calls for fast, reliable tests:

```python
@pytest.fixture
def mock_google_calendar(mocker):
    """Mock Google Calendar API."""
    mock = mocker.patch('tools.google_calendar.create_calendar_event')
    mock.return_value = "mock_event_id"
    return mock
```

### 3. Time-Based Testing

Use `freezegun` for predictable date/time testing:

```python
@freeze_time("2025-01-15 10:00:00")
def test_parse_tomorrow():
    result = parse_natural_language_date("tomorrow at 10am")
    assert result.day == 16  # Always predictable
```

### 4. Parametrized Tests

Test multiple scenarios efficiently:

```python
@pytest.mark.parametrize("date_string,expected_day", [
    ("tomorrow at 10am", 16),
    ("in 2 days", 17),
    ("next Monday", None),  # Depends on current day
])
def test_various_dates(date_string, expected_day):
    result = parse_natural_language_date(date_string)
    if expected_day:
        assert result.day == expected_day
```

## Continuous Integration

Tests run automatically on every push via GitHub Actions:

- **Python Versions**: 3.9, 3.10, 3.11
- **Coverage Reporting**: Automatic coverage uploads
- **Test Results**: Visible in pull requests

See `.github/workflows/tests.yml` for CI configuration.

## Writing New Tests

### Test File Naming

- Name test files `test_*.py`
- Place in `tests/` directory
- Group related tests in classes

### Test Function Naming

- Name test functions `test_*`
- Use descriptive names: `test_create_task_with_due_date`
- One assertion per test (ideally)

### Example Test

```python
import pytest

@pytest.mark.unit
class TestNewFeature:
    """Tests for new feature."""

    def test_feature_happy_path(self, task_repo, test_user_id):
        """Test the main success scenario."""
        result = some_function(test_user_id)

        assert result is not None
        assert result.status == "success"

    def test_feature_edge_case(self, task_repo, test_user_id):
        """Test edge case handling."""
        result = some_function(test_user_id, invalid_input=True)

        assert "error" in result.lower()
```

## Debugging Tests

### Run Single Test with Output

```bash
pytest tests/test_database.py::test_create_task_basic -v -s
```

### Drop into Debugger on Failure

```bash
pytest --pdb
```

### Show Local Variables on Failure

```bash
pytest -l
```

## Best Practices

1. **Keep tests fast** - Use mocks for external APIs
2. **Test behavior, not implementation** - Focus on what, not how
3. **One assertion per test** - Makes failures easy to diagnose
4. **Use descriptive names** - Test name should explain what it tests
5. **Arrange-Act-Assert** - Structure tests clearly
6. **Clean up resources** - Use fixtures for setup/teardown

## Common Issues

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'agent'`

**Solution:** Run pytest from project root, or install package in editable mode:
```bash
pip install -e .
```

### Database Lock Errors

**Problem:** `database is locked`

**Solution:** Each test gets isolated database via fixtures. If you see this, check that you're using the `task_repo` fixture.

### Mock Not Working

**Problem:** Mocked function still makes real API call

**Solution:** Ensure you're patching the right location:
```python
# Patch where it's used, not where it's defined
mocker.patch('tools.tasks.create_calendar_event')  # ✓ Correct
mocker.patch('tools.google_calendar.create_calendar_event')  # ✗ Wrong
```

## Interview Talking Points

When discussing testing in interviews:

1. **Test Coverage**: "I have 50+ tests covering ~75% of core business logic"

2. **Test Strategy**: "I use pytest with fixtures for isolation, mocks for external APIs, and freezegun for time-based testing"

3. **CI/CD**: "Tests run automatically on every push with GitHub Actions across multiple Python versions"

4. **Best Practices**: "I follow AAA pattern (Arrange-Act-Assert) and focus on testing behavior, not implementation"

5. **Mocking**: "I mock external APIs like Google Calendar and OpenAI to keep tests fast and avoid API costs"

6. **Isolation**: "Each test gets a fresh in-memory database to ensure tests don't affect each other"

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-Mock](https://pytest-mock.readthedocs.io/)
- [Freezegun](https://github.com/spulec/freezegun)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
