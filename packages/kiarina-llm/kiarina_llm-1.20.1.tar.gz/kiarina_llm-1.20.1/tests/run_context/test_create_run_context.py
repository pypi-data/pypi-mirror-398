from kiarina.llm.run_context import create_run_context, settings_manager


def test_create_run_context_with_settings():
    """Test that RunContext is created using configuration values"""
    context = create_run_context()
    settings = settings_manager.settings
    assert context.app_author == settings.app_author
    assert context.app_name == settings.app_name
    assert context.tenant_id == settings.tenant_id
    assert context.user_id == settings.user_id
    assert context.time_zone == settings.time_zone
    assert context.language == settings.language
    assert context.currency == settings.currency
    assert context.metadata == settings.metadata


def test_create_run_context_with_overrides():
    """Test that RunContext is created with argument overrides"""
    context = create_run_context(
        app_author="TestCompany",
        app_name="TestApp",
        tenant_id="tenant-123",
        user_id="user-456",
        agent_id="agent-789",
        runner_id="test-runner",
        time_zone="Asia/Tokyo",
        language="ja",
        currency="JPY",
        metadata={"version": "1.0.0"},
    )

    assert context.app_author == "TestCompany"
    assert context.app_name == "TestApp"
    assert context.tenant_id == "tenant-123"
    assert context.user_id == "user-456"
    assert context.agent_id == "agent-789"
    assert context.runner_id == "test-runner"
    assert context.time_zone == "Asia/Tokyo"
    assert context.language == "ja"
    assert context.currency == "JPY"
    assert context.metadata == {"version": "1.0.0"}
