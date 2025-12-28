import pytest

from kiarina.llm.run_context import settings_manager


@pytest.fixture(scope="session", autouse=True)
def setup_settings():
    settings_manager.user_config = {
        "tenant_id": "test-tenant",
        "user_id": "test-user",
        "agent_id": "test-agent",
    }
