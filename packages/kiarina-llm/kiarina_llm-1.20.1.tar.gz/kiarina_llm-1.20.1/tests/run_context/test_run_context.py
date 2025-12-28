import pytest

from kiarina.llm.run_context import RunContext


def test_valid():
    data = {
        "app_author": "TestCompany",
        "app_name": "TestApp",
        "tenant_id": "tenant-123",
        "user_id": "user-456",
        "agent_id": "agent-789",
        "runner_id": "runner-001",
        "time_zone": "UTC",
        "language": "en",
        "currency": "USD",
        "metadata": {"key": "value"},
    }

    run_context = RunContext.model_validate(data)
    assert run_context.model_dump() == data


def test_invalid():
    with pytest.raises(Exception):
        RunContext.model_validate(
            {
                "app_author": "Invalid/Name",  # Invalid character
                "app_name": "TestApp",
                "tenant_id": "tenant-123",
                "user_id": "user-456",
                "agent_id": "agent-789",
                "runner_id": "runner-001",
                "time_zone": "UTC",
                "language": "en",
                "currency": "USD",
            }
        )
